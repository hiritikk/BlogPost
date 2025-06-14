"""
Web scraper for gathering trending topics and content ideas
"""
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional
from loguru import logger
import time
from src.database.models import TrendingTopic
from src.database.init_db import get_session
from config.settings import settings

class TrendScraper:
    """Scrapes trending topics from various sources"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def scrape_all_sources(self) -> Dict[str, List[Dict]]:
        """
        Scrape trending topics from all configured sources
        
        Returns:
            Dictionary of source names to lists of trending topics
        """
        all_trends = {}
        
        # Scrape each source
        sources = [
            ('linkedin', self._scrape_linkedin_trends),
            ('forbes', self._scrape_forbes_education),
            ('news', self._scrape_news_api),
            ('reddit', self._scrape_reddit_education)
        ]
        
        for source_name, scraper_func in sources:
            try:
                logger.info(f"Scraping {source_name}...")
                trends = scraper_func()
                all_trends[source_name] = trends
                logger.info(f"Found {len(trends)} trends from {source_name}")
                
                # Save to database
                self._save_trends_to_db(trends, source_name)
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Failed to scrape {source_name}: {e}")
                all_trends[source_name] = []
        
        return all_trends
    
    def _scrape_linkedin_trends(self) -> List[Dict]:
        """Scrape trending topics from LinkedIn (simplified version)"""
        trends = []
        
        # Note: Full LinkedIn scraping requires authentication
        # This is a simplified example using public data
        
        search_terms = settings.linkedin_search_terms
        
        for term in search_terms:
            # Simulate gathering trends for each search term
            trend = {
                'topic': f"Latest insights on {term}",
                'description': f"Trending discussions about {term} in the professional community",
                'relevance_score': 8,
                'source_url': f"https://www.linkedin.com/search/results/content/?keywords={term.replace(' ', '%20')}"
            }
            trends.append(trend)
        
        return trends
    
    def _scrape_forbes_education(self) -> List[Dict]:
        """Scrape education and career articles from Forbes"""
        trends = []
        
        categories = settings.forbes_categories
        base_url = "https://www.forbes.com"
        
        for category in categories:
            try:
                url = f"{base_url}/{category}/"
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find article headlines (simplified selector)
                    articles = soup.find_all('h4', class_='stream-item__title', limit=5)
                    
                    for article in articles:
                        title = article.get_text(strip=True)
                        link = article.find('a')
                        
                        if title and link:
                            trend = {
                                'topic': title,
                                'description': f"Forbes article on {category}",
                                'relevance_score': 9,
                                'source_url': base_url + link.get('href', '')
                            }
                            trends.append(trend)
                
            except Exception as e:
                logger.error(f"Error scraping Forbes {category}: {e}")
        
        return trends
    
    def _scrape_news_api(self) -> List[Dict]:
        """Get trending news using News API"""
        trends = []
        
        if not settings.news_api_key:
            logger.warning("News API key not configured")
            return trends
        
        try:
            # Query for education and career news
            url = "https://newsapi.org/v2/everything"
            params = {
                'q': 'international students OR career development OR job market',
                'sortBy': 'popularity',
                'language': 'en',
                'apiKey': settings.news_api_key,
                'pageSize': 10
            }
            
            response = self.session.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                for article in data.get('articles', [])[:10]:
                    trend = {
                        'topic': article.get('title', ''),
                        'description': article.get('description', ''),
                        'relevance_score': 7,
                        'source_url': article.get('url', '')
                    }
                    trends.append(trend)
            
        except Exception as e:
            logger.error(f"Error using News API: {e}")
        
        return trends
    
    def _scrape_reddit_education(self) -> List[Dict]:
        """Scrape trending topics from education-related subreddits"""
        trends = []
        
        subreddits = [
            'InternationalStudents',
            'careerguidance',
            'cscareerquestions',
            'gradadmissions'
        ]
        
        for subreddit in subreddits:
            try:
                url = f"https://www.reddit.com/r/{subreddit}/hot.json"
                response = self.session.get(url, headers={'User-Agent': 'BlogAutomation/1.0'}, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    posts = data.get('data', {}).get('children', [])[:3]
                    
                    for post in posts:
                        post_data = post.get('data', {})
                        
                        # Filter for high-quality posts
                        if post_data.get('score', 0) > 50:
                            trend = {
                                'topic': post_data.get('title', ''),
                                'description': f"Popular discussion in r/{subreddit}",
                                'relevance_score': min(10, post_data.get('score', 0) // 100),
                                'source_url': f"https://reddit.com{post_data.get('permalink', '')}"
                            }
                            trends.append(trend)
                
                time.sleep(1)  # Rate limiting for Reddit
                
            except Exception as e:
                logger.error(f"Error scraping Reddit r/{subreddit}: {e}")
        
        return trends
    
    def _save_trends_to_db(self, trends: List[Dict], source: str):
        """Save trending topics to database"""
        session = get_session()
        
        for trend_data in trends:
            # Check if already exists
            existing = session.query(TrendingTopic).filter_by(
                topic=trend_data['topic'],
                source=source
            ).first()
            
            if not existing:
                trend = TrendingTopic(
                    source=source,
                    topic=trend_data['topic'],
                    description=trend_data.get('description', ''),
                    relevance_score=trend_data.get('relevance_score', 5),
                    source_url=trend_data.get('source_url', '')
                )
                session.add(trend)
        
        session.commit()
    
    def get_top_trends(self, limit: int = 10) -> List[TrendingTopic]:
        """
        Get top trending topics from database
        
        Args:
            limit: Maximum number of trends to return
            
        Returns:
            List of TrendingTopic objects
        """
        session = get_session()
        
        # Get unused trends sorted by relevance and recency
        trends = session.query(TrendingTopic).filter_by(
            used_in_post=False
        ).order_by(
            TrendingTopic.relevance_score.desc(),
            TrendingTopic.discovered_at.desc()
        ).limit(limit).all()
        
        return trends
    
    def mark_trends_used(self, trend_ids: List[str]):
        """Mark trends as used in a blog post"""
        session = get_session()
        
        session.query(TrendingTopic).filter(
            TrendingTopic.id.in_(trend_ids)
        ).update({'used_in_post': True}, synchronize_session=False)
        
        session.commit()
    
    def search_sources_for_topic(self, topic: str) -> List[Dict]:
        """
        Search for credible sources on a specific topic
        
        Args:
            topic: The topic to search for
            
        Returns:
            List of source dictionaries
        """
        sources = []
        
        # Search using various methods
        # This is a simplified version - in production, you'd use more sophisticated search
        
        # Academic sources (simplified)
        sources.extend(self._search_academic_sources(topic))
        
        # News sources
        sources.extend(self._search_news_sources(topic))
        
        # Filter and rank by credibility
        sources = sorted(sources, key=lambda x: x.get('credibility_score', 0), reverse=True)
        
        return sources[:10]  # Return top 10 sources
    
    def _search_academic_sources(self, topic: str) -> List[Dict]:
        """Search for academic sources (simplified)"""
        # In production, you'd use APIs like Google Scholar, PubMed, etc.
        return [
            {
                'type': 'research',
                'title': f"Research insights on {topic}",
                'author': "Academic Researchers",
                'url': f"https://scholar.google.com/scholar?q={topic.replace(' ', '+')}",
                'credibility_score': 9,
                'relevance_score': 8
            }
        ]
    
    def _search_news_sources(self, topic: str) -> List[Dict]:
        """Search for news sources on the topic"""
        sources = []
        
        if settings.news_api_key:
            try:
                url = "https://newsapi.org/v2/everything"
                params = {
                    'q': topic,
                    'sortBy': 'relevancy',
                    'language': 'en',
                    'apiKey': settings.news_api_key,
                    'pageSize': 5
                }
                
                response = self.session.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for article in data.get('articles', []):
                        source = {
                            'type': 'article',
                            'title': article.get('title', ''),
                            'author': article.get('author', 'Unknown'),
                            'url': article.get('url', ''),
                            'publication_date': article.get('publishedAt', ''),
                            'credibility_score': 7,
                            'relevance_score': 8
                        }
                        sources.append(source)
                
            except Exception as e:
                logger.error(f"Error searching news sources: {e}")
        
        return sources 