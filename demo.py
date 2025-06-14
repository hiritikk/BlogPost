"""
Demo script for Re-Defined Blog Automation System
Shows how to use the system to generate, optimize, and publish blogs
"""
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.database.init_db import init_database
from src.content_generator.generator import BlogGenerator
from src.scraper.trend_scraper import TrendScraper
from src.image_generator.generator import ImageGenerator
from src.seo_optimizer.optimizer import SEOOptimizer
from src.publisher.publisher import BlogPublisher
from src.scheduler.scheduler import BlogScheduler
from loguru import logger

def demo_blog_generation():
    """Demonstrate blog generation workflow"""
    
    print("🚀 Re-Defined Blog Automation System Demo")
    print("=" * 50)
    
    # Step 1: Initialize database
    print("\n1️⃣ Initializing database...")
    init_database()
    print("✅ Database initialized")
    
    # Step 2: Scrape trending topics
    print("\n2️⃣ Scraping trending topics...")
    scraper = TrendScraper()
    trends = scraper.scrape_all_sources()
    
    trend_count = sum(len(t) for t in trends.values())
    print(f"✅ Found {trend_count} trending topics from {len(trends)} sources")
    
    # Display some trends
    for source, source_trends in trends.items():
        if source_trends:
            print(f"\n  From {source}:")
            for trend in source_trends[:2]:
                print(f"  - {trend['topic']}")
    
    # Step 3: Generate a blog post
    print("\n3️⃣ Generating blog post...")
    generator = BlogGenerator()
    
    # Example topic
    topic = "5 Essential Tips for International Students Starting Their Career Journey in 2024"
    
    # Get some sources
    sources = scraper.search_sources_for_topic(topic)
    
    # Prepare trending data
    top_trends = scraper.get_top_trends(3)
    trending_data = {
        'topics': [t.topic for t in top_trends],
        'search_queries': [topic],
        'scraped_urls': [t.source_url for t in top_trends]
    }
    
    # Generate the blog
    blog_post = generator.create_blog(
        topic=topic,
        trending_data=trending_data,
        sources=sources[:3],
        custom_instructions="Focus on practical, actionable advice. Include statistics where relevant."
    )
    
    print(f"✅ Blog generated: {blog_post.title}")
    print(f"   - Word count: {blog_post.word_count}")
    print(f"   - Reading time: {blog_post.reading_time} minutes")
    print(f"   - Keywords: {', '.join(blog_post.keywords[:5])}")
    
    # Step 4: Generate images
    print("\n4️⃣ Generating images...")
    image_gen = ImageGenerator()
    
    thumbnail_path = image_gen.generate_thumbnail(
        blog_post.title,
        subtitle="Re-Defined Career Resources"
    )
    banner_path = image_gen.generate_banner(
        blog_post.title,
        category="Career Development"
    )
    
    print(f"✅ Thumbnail generated: {thumbnail_path}")
    print(f"✅ Banner generated: {banner_path}")
    
    # Update blog with images
    from src.database.init_db import get_session
    session = get_session()
    blog_post.thumbnail_url = thumbnail_path
    blog_post.banner_image_url = banner_path
    session.commit()
    
    # Step 5: SEO optimization
    print("\n5️⃣ Optimizing for SEO...")
    seo = SEOOptimizer()
    
    blog_data = {
        'title': blog_post.title,
        'content': blog_post.content,
        'meta_description': blog_post.meta_description,
        'keywords': blog_post.keywords,
        'slug': blog_post.slug
    }
    
    optimizations = seo.optimize_blog_post(blog_data)
    seo_score = optimizations['seo_score']
    
    print(f"✅ SEO Score: {seo_score['score']:.1f}/100")
    if seo_score['recommendations']:
        print("   Recommendations:")
        for rec in seo_score['recommendations'][:3]:
            print(f"   - {rec}")
    
    # Update blog with SEO optimizations
    blog_post.meta_description = optimizations['meta_description']
    blog_post.keywords = optimizations['keywords']
    session.commit()
    
    # Step 6: Preview content
    print("\n6️⃣ Blog Preview:")
    print("=" * 50)
    print(f"Title: {blog_post.title}")
    print(f"Meta: {blog_post.meta_description}")
    print(f"\nContent preview (first 200 chars):")
    print(blog_post.content[:200] + "...")
    print("=" * 50)
    
    # Step 7: Publishing (simulation)
    print("\n7️⃣ Publishing blog...")
    publisher = BlogPublisher()
    
    # Note: This will simulate publishing since no real API is configured
    result = publisher.publish_blog(blog_post.id)
    
    if result['success']:
        print(f"✅ Blog published successfully!")
        print(f"   URL: {result.get('url')}")
    else:
        print(f"❌ Publishing failed: {result.get('message')}")
    
    return blog_post

def demo_scheduling():
    """Demonstrate scheduling features"""
    
    print("\n\n🗓️ Scheduling Demo")
    print("=" * 50)
    
    scheduler = BlogScheduler()
    
    # Schedule a custom blog for next week
    next_week = datetime.now() + timedelta(days=7)
    
    print(f"\n📅 Scheduling custom blog for {next_week.strftime('%Y-%m-%d')}")
    
    task_id = scheduler.schedule_custom_blog(
        topic="How to Network Effectively as an International Student",
        scheduled_date=next_week,
        custom_instructions="Include virtual networking tips and LinkedIn strategies"
    )
    
    print(f"✅ Blog scheduled with task ID: {task_id}")
    
    # Show scheduled tasks
    print("\n📋 Current scheduled tasks:")
    tasks = scheduler.get_scheduled_tasks()
    
    for task in tasks[:5]:
        print(f"  - {task.task_type}: {task.scheduled_for.strftime('%Y-%m-%d %H:%M')} ({task.status})")

def demo_analytics():
    """Show analytics capabilities"""
    
    print("\n\n📊 Analytics Demo")
    print("=" * 50)
    
    from src.database.init_db import get_session
    from src.database.models import BlogPost
    
    session = get_session()
    
    # Get blog statistics
    total_blogs = session.query(BlogPost).count()
    published_blogs = session.query(BlogPost).filter_by(status="published").count()
    draft_blogs = session.query(BlogPost).filter_by(status="draft").count()
    
    print(f"\n📈 Blog Statistics:")
    print(f"  - Total blogs: {total_blogs}")
    print(f"  - Published: {published_blogs}")
    print(f"  - Drafts: {draft_blogs}")
    
    # Recent blogs
    recent_blogs = session.query(BlogPost).order_by(BlogPost.created_at.desc()).limit(3).all()
    
    if recent_blogs:
        print(f"\n📝 Recent Blogs:")
        for blog in recent_blogs:
            print(f"  - {blog.title[:50]}... ({blog.status})")

if __name__ == "__main__":
    try:
        # Run the main demo
        blog_post = demo_blog_generation()
        
        # Run scheduling demo
        demo_scheduling()
        
        # Run analytics demo
        demo_analytics()
        
        print("\n\n✅ Demo completed successfully!")
        print("\n💡 Next steps:")
        print("1. Run the web app: python app.py")
        print("2. Run the dashboard: streamlit run dashboard.py")
        print("3. Configure your API keys in .env file")
        print("4. Start automating your blog content!")
        
    except Exception as e:
        logger.error(f"Demo failed: {e}")
        print(f"\n❌ Demo failed: {e}")
        print("\n💡 Make sure you have:")
        print("1. Created a .env file with required API keys")
        print("2. Installed all dependencies: pip install -r requirements.txt")
        print("3. Set up your OpenAI API key") 