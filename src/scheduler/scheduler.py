"""
Scheduler for automated blog generation and publishing
"""
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from loguru import logger
from src.database.models import ScheduledTask, BlogPost
from src.database.init_db import get_session
from src.content_generator.generator import BlogGenerator
from src.scraper.trend_scraper import TrendScraper
from src.image_generator.generator import ImageGenerator
from src.seo_optimizer.optimizer import SEOOptimizer
from src.publisher.publisher import BlogPublisher
from config.settings import settings

class BlogScheduler:
    """Manages automated blog generation and publishing"""
    
    def __init__(self):
        # Configure job store
        jobstores = {
            'default': SQLAlchemyJobStore(url=settings.database_url)
        }
        
        # Create scheduler
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            timezone='UTC'
        )
        
        # Initialize components
        self.generator = BlogGenerator()
        self.scraper = TrendScraper()
        self.image_generator = ImageGenerator()
        self.seo_optimizer = SEOOptimizer()
        self.publisher = BlogPublisher()
        
    def start(self):
        """Start the scheduler"""
        self.scheduler.start()
        
        # Schedule regular blog generation
        self._schedule_regular_tasks()
        
        logger.info("Blog scheduler started")
    
    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        logger.info("Blog scheduler stopped")
    
    def _schedule_regular_tasks(self):
        """Schedule regular automated tasks"""
        
        # Schedule trend scraping (daily)
        self.scheduler.add_job(
            func=self.scrape_trends_task,
            trigger="cron",
            hour=9,  # 9 AM UTC
            id="daily_trend_scraping",
            replace_existing=True
        )
        
        # Schedule blog generation (every 14 days)
        self.scheduler.add_job(
            func=self.generate_and_publish_blog_task,
            trigger="interval",
            days=settings.publish_interval_days,
            id="biweekly_blog_generation",
            replace_existing=True
        )
        
        logger.info("Regular tasks scheduled")
    
    def scrape_trends_task(self) -> Dict:
        """Task to scrape trending topics"""
        
        task = self._create_task("scrape", {
            'description': 'Daily trend scraping'
        })
        
        try:
            # Scrape trends
            trends = self.scraper.scrape_all_sources()
            
            # Update task status
            self._complete_task(task, {
                'trends_found': sum(len(t) for t in trends.values()),
                'sources': list(trends.keys())
            })
            
            logger.info(f"Trend scraping completed: {sum(len(t) for t in trends.values())} trends found")
            
            return {'success': True, 'trends': trends}
            
        except Exception as e:
            logger.error(f"Trend scraping failed: {e}")
            self._fail_task(task, str(e))
            return {'success': False, 'error': str(e)}
    
    def generate_and_publish_blog_task(self) -> Dict:
        """Task to generate and publish a blog post"""
        
        task = self._create_task("generate_and_publish", {
            'description': 'Automated blog generation and publishing'
        })
        
        try:
            # Get trending topics
            top_trends = self.scraper.get_top_trends(5)
            
            if not top_trends:
                logger.warning("No trending topics available")
                # Generate without trends
                topic = "Tips for International Students: Navigating Your Career Journey"
            else:
                # Select best topic
                topic = self._select_best_topic(top_trends)
                
                # Mark trends as used
                trend_ids = [t.id for t in top_trends[:3]]
                self.scraper.mark_trends_used(trend_ids)
            
            # Search for sources
            sources = self.scraper.search_sources_for_topic(topic)
            
            # Prepare trending data
            trending_data = {
                'topics': [t.topic for t in top_trends] if top_trends else [],
                'search_queries': [topic],
                'scraped_urls': [t.source_url for t in top_trends] if top_trends else []
            }
            
            # Generate blog
            logger.info(f"Generating blog on topic: {topic}")
            blog_post = self.generator.create_blog(
                topic=topic,
                trending_data=trending_data,
                sources=sources
            )
            
            # Apply SEO optimizations
            seo_optimizations = self.seo_optimizer.optimize_blog_post({
                'title': blog_post.title,
                'content': blog_post.content,
                'meta_description': blog_post.meta_description,
                'keywords': blog_post.keywords,
                'slug': blog_post.slug
            })
            
            # Update blog with SEO optimizations
            session = get_session()
            blog_post.meta_description = seo_optimizations['meta_description']
            blog_post.keywords = seo_optimizations['keywords']
            session.commit()
            
            # Generate images
            thumbnail_path = self.image_generator.generate_thumbnail(
                blog_post.title,
                subtitle="Re-Defined Resources"
            )
            banner_path = self.image_generator.generate_banner(
                blog_post.title,
                category="Career Development"
            )
            
            # Update blog with images
            blog_post.thumbnail_url = thumbnail_path
            blog_post.banner_image_url = banner_path
            session.commit()
            
            # Publish blog
            publish_result = self.publisher.publish_blog(blog_post.id)
            
            if publish_result['success']:
                self._complete_task(task, {
                    'blog_id': blog_post.id,
                    'blog_title': blog_post.title,
                    'published_url': publish_result.get('url'),
                    'seo_score': seo_optimizations['seo_score']['score']
                })
                
                logger.info(f"Blog published successfully: {blog_post.title}")
                return {
                    'success': True,
                    'blog_id': blog_post.id,
                    'url': publish_result.get('url')
                }
            else:
                raise Exception(f"Publishing failed: {publish_result.get('message')}")
                
        except Exception as e:
            logger.error(f"Blog generation/publishing failed: {e}")
            self._fail_task(task, str(e))
            return {'success': False, 'error': str(e)}
    
    def schedule_custom_blog(
        self,
        topic: str,
        scheduled_date: datetime,
        custom_instructions: Optional[str] = None
    ) -> str:
        """
        Schedule a custom blog post
        
        Args:
            topic: Blog topic
            scheduled_date: When to generate and publish
            custom_instructions: Additional instructions
            
        Returns:
            Task ID
        """
        task_id = f"custom_blog_{datetime.now().timestamp()}"
        
        self.scheduler.add_job(
            func=self.generate_custom_blog_task,
            trigger="date",
            run_date=scheduled_date,
            args=[topic, custom_instructions],
            id=task_id
        )
        
        # Create task record
        task = self._create_task("custom_blog", {
            'topic': topic,
            'custom_instructions': custom_instructions,
            'scheduled_for': scheduled_date.isoformat()
        })
        
        logger.info(f"Custom blog scheduled for {scheduled_date}: {topic}")
        
        return task.id
    
    def generate_custom_blog_task(self, topic: str, custom_instructions: Optional[str] = None):
        """Generate a custom blog post"""
        
        task = self._create_task("generate_custom", {
            'topic': topic,
            'custom_instructions': custom_instructions
        })
        
        try:
            # Search for sources
            sources = self.scraper.search_sources_for_topic(topic)
            
            # Generate blog
            blog_post = self.generator.create_blog(
                topic=topic,
                sources=sources,
                custom_instructions=custom_instructions
            )
            
            # Generate images
            thumbnail_path = self.image_generator.generate_thumbnail(blog_post.title)
            banner_path = self.image_generator.generate_banner(blog_post.title)
            
            # Update blog
            session = get_session()
            blog_post.thumbnail_url = thumbnail_path
            blog_post.banner_image_url = banner_path
            session.commit()
            
            # Schedule for review (don't auto-publish custom blogs)
            blog_post.status = "scheduled"
            blog_post.scheduled_date = datetime.utcnow() + timedelta(hours=24)
            session.commit()
            
            self._complete_task(task, {
                'blog_id': blog_post.id,
                'blog_title': blog_post.title,
                'status': 'scheduled_for_review'
            })
            
            logger.info(f"Custom blog generated and scheduled for review: {blog_post.title}")
            
        except Exception as e:
            logger.error(f"Custom blog generation failed: {e}")
            self._fail_task(task, str(e))
    
    def _select_best_topic(self, trends: List) -> str:
        """Select the best topic from trending topics"""
        
        # Sort by relevance score
        sorted_trends = sorted(trends, key=lambda x: x.relevance_score, reverse=True)
        
        # Get the most relevant trend
        best_trend = sorted_trends[0]
        
        # Convert to a blog topic
        if "?" in best_trend.topic:
            # It's already a question
            return best_trend.topic
        else:
            # Convert to a topic
            return f"Understanding {best_trend.topic}: A Guide for International Students"
    
    def _create_task(self, task_type: str, parameters: Dict) -> ScheduledTask:
        """Create a scheduled task record"""
        
        session = get_session()
        
        task = ScheduledTask(
            task_type=task_type,
            status="running",
            scheduled_for=datetime.utcnow(),
            started_at=datetime.utcnow(),
            parameters=parameters
        )
        
        session.add(task)
        session.commit()
        
        return task
    
    def _complete_task(self, task: ScheduledTask, result: Dict):
        """Mark task as completed"""
        
        session = get_session()
        task.status = "completed"
        task.completed_at = datetime.utcnow()
        task.result = result
        session.commit()
    
    def _fail_task(self, task: ScheduledTask, error_message: str):
        """Mark task as failed"""
        
        session = get_session()
        task.status = "failed"
        task.completed_at = datetime.utcnow()
        task.error_message = error_message
        task.retry_count += 1
        session.commit()
    
    def get_scheduled_tasks(self, status: Optional[str] = None) -> List[ScheduledTask]:
        """Get scheduled tasks"""
        
        session = get_session()
        query = session.query(ScheduledTask)
        
        if status:
            query = query.filter_by(status=status)
        
        return query.order_by(ScheduledTask.scheduled_for.desc()).all()
    
    def retry_failed_task(self, task_id: str) -> bool:
        """Retry a failed task"""
        
        session = get_session()
        task = session.query(ScheduledTask).filter_by(id=task_id).first()
        
        if not task or task.status != "failed":
            return False
        
        if task.retry_count >= 3:
            logger.warning(f"Task {task_id} has exceeded retry limit")
            return False
        
        # Reset task status
        task.status = "pending"
        task.error_message = None
        session.commit()
        
        # Reschedule based on task type
        if task.task_type == "generate_and_publish":
            self.scheduler.add_job(
                func=self.generate_and_publish_blog_task,
                trigger="date",
                run_date=datetime.utcnow() + timedelta(minutes=5),
                id=f"retry_{task_id}"
            )
        
        logger.info(f"Task {task_id} scheduled for retry")
        return True 