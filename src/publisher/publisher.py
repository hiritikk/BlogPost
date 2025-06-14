"""
Publisher module for posting blogs to Re-Defined website
"""
import requests
import json
from datetime import datetime
from typing import Dict, Optional
from loguru import logger
from src.database.models import BlogPost
from src.database.init_db import get_session
from config.settings import settings

class BlogPublisher:
    """Handles publishing blogs to the Re-Defined website"""
    
    def __init__(self):
        self.api_endpoint = settings.website_api_endpoint
        self.api_key = settings.website_api_key
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def publish_blog(self, blog_post_id: str) -> Dict:
        """
        Publish a blog post to the website
        
        Args:
            blog_post_id: ID of the blog post to publish
            
        Returns:
            Dictionary with publish status and details
        """
        session = get_session()
        blog_post = session.query(BlogPost).filter_by(id=blog_post_id).first()
        
        if not blog_post:
            raise ValueError(f"Blog post not found: {blog_post_id}")
        
        if blog_post.status == "published":
            logger.warning(f"Blog post already published: {blog_post.title}")
            return {
                'success': False,
                'message': 'Blog post already published',
                'post_id': blog_post.website_post_id
            }
        
        try:
            # Prepare blog data for API
            blog_data = self._prepare_blog_data(blog_post)
            
            # Send to website API
            if self.api_endpoint:
                response = self._send_to_api(blog_data)
            else:
                # Simulate publishing for testing
                response = self._simulate_publish(blog_data)
            
            # Update blog post status
            if response['success']:
                blog_post.status = "published"
                blog_post.published_date = datetime.utcnow()
                blog_post.website_post_id = response.get('post_id')
                session.commit()
                
                logger.info(f"Successfully published: {blog_post.title}")
            else:
                blog_post.status = "failed"
                session.commit()
                logger.error(f"Failed to publish: {response.get('message')}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error publishing blog post: {e}")
            blog_post.status = "failed"
            session.commit()
            
            return {
                'success': False,
                'message': str(e)
            }
    
    def _prepare_blog_data(self, blog_post: BlogPost) -> Dict:
        """Prepare blog data for the website API"""
        
        # Load related data
        session = get_session()
        sources = [
            {
                'title': source.title,
                'url': source.url,
                'citation': source.citation_text
            }
            for source in blog_post.sources
        ]
        
        # Format the blog content with citations
        content_with_citations = self._add_citations_to_content(
            blog_post.content,
            sources
        )
        
        # Prepare the data structure expected by the website
        blog_data = {
            'title': blog_post.title,
            'slug': blog_post.slug,
            'content': content_with_citations,
            'excerpt': blog_post.summary,
            'meta': {
                'description': blog_post.meta_description,
                'keywords': blog_post.keywords,
                'reading_time': blog_post.reading_time,
                'word_count': blog_post.word_count
            },
            'media': {
                'thumbnail': blog_post.thumbnail_url,
                'banner': blog_post.banner_image_url
            },
            'category': 'Resources & Blog',
            'tags': self._extract_tags(blog_post.keywords),
            'author': 'Re-Defined Team',
            'status': 'publish',
            'created_at': blog_post.created_at.isoformat() if blog_post.created_at else None
        }
        
        return blog_data
    
    def _send_to_api(self, blog_data: Dict) -> Dict:
        """Send blog data to the website API"""
        
        try:
            response = requests.post(
                self.api_endpoint,
                json=blog_data,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 201:
                data = response.json()
                return {
                    'success': True,
                    'post_id': data.get('id'),
                    'url': data.get('url'),
                    'message': 'Blog published successfully'
                }
            else:
                return {
                    'success': False,
                    'message': f'API error: {response.status_code} - {response.text}'
                }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {
                'success': False,
                'message': f'API request failed: {str(e)}'
            }
    
    def _simulate_publish(self, blog_data: Dict) -> Dict:
        """Simulate publishing for testing when API is not configured"""
        
        logger.info("Simulating blog publish (no API endpoint configured)")
        logger.info(f"Blog title: {blog_data['title']}")
        logger.info(f"Blog slug: {blog_data['slug']}")
        
        # Save to local file for testing
        from pathlib import Path
        output_dir = Path("published_blogs")
        output_dir.mkdir(exist_ok=True)
        
        filename = f"{blog_data['slug']}.json"
        filepath = output_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(blog_data, f, indent=2)
        
        # Generate a mock post ID
        import uuid
        mock_post_id = str(uuid.uuid4())[:8]
        
        return {
            'success': True,
            'post_id': mock_post_id,
            'url': f"https://re-defined.ca/blog/{blog_data['slug']}",
            'message': f'Blog published (simulated) to {filepath}'
        }
    
    def _add_citations_to_content(self, content: str, sources: list) -> str:
        """Add citations to the blog content"""
        
        if not sources:
            return content
        
        # Add citations section at the end
        citations_section = "\n\n## Sources\n\n"
        
        for i, source in enumerate(sources, 1):
            citation = f"{i}. [{source['title']}]({source['url']})"
            if source.get('citation'):
                citation += f" - \"{source['citation']}\""
            citations_section += citation + "\n"
        
        return content + citations_section
    
    def _extract_tags(self, keywords: list) -> list:
        """Extract tags from keywords"""
        
        # Convert keywords to tags
        tags = []
        
        for keyword in keywords:
            # Clean up keyword for tag
            tag = keyword.lower().strip()
            # Replace spaces with hyphens
            tag = tag.replace(' ', '-')
            # Remove special characters
            tag = ''.join(c for c in tag if c.isalnum() or c == '-')
            
            if tag and len(tag) > 2:
                tags.append(tag)
        
        return tags[:10]  # Limit to 10 tags
    
    def unpublish_blog(self, blog_post_id: str) -> Dict:
        """Unpublish a blog post from the website"""
        
        session = get_session()
        blog_post = session.query(BlogPost).filter_by(id=blog_post_id).first()
        
        if not blog_post:
            raise ValueError(f"Blog post not found: {blog_post_id}")
        
        if blog_post.status != "published":
            return {
                'success': False,
                'message': 'Blog post is not published'
            }
        
        try:
            if self.api_endpoint and blog_post.website_post_id:
                # Send delete request to API
                response = requests.delete(
                    f"{self.api_endpoint}/{blog_post.website_post_id}",
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code in [200, 204]:
                    blog_post.status = "draft"
                    blog_post.website_post_id = None
                    session.commit()
                    
                    return {
                        'success': True,
                        'message': 'Blog unpublished successfully'
                    }
                else:
                    return {
                        'success': False,
                        'message': f'API error: {response.status_code}'
                    }
            else:
                # Simulate unpublishing
                blog_post.status = "draft"
                blog_post.website_post_id = None
                session.commit()
                
                return {
                    'success': True,
                    'message': 'Blog unpublished (simulated)'
                }
                
        except Exception as e:
            logger.error(f"Error unpublishing blog post: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def update_published_blog(self, blog_post_id: str) -> Dict:
        """Update an already published blog post"""
        
        session = get_session()
        blog_post = session.query(BlogPost).filter_by(id=blog_post_id).first()
        
        if not blog_post or not blog_post.website_post_id:
            return {
                'success': False,
                'message': 'Blog post not found or not published'
            }
        
        try:
            # Prepare updated data
            blog_data = self._prepare_blog_data(blog_post)
            
            if self.api_endpoint:
                # Send update request to API
                response = requests.put(
                    f"{self.api_endpoint}/{blog_post.website_post_id}",
                    json=blog_data,
                    headers=self.headers,
                    timeout=30
                )
                
                if response.status_code == 200:
                    blog_post.updated_at = datetime.utcnow()
                    session.commit()
                    
                    return {
                        'success': True,
                        'message': 'Blog updated successfully'
                    }
                else:
                    return {
                        'success': False,
                        'message': f'API error: {response.status_code}'
                    }
            else:
                # Simulate update
                blog_post.updated_at = datetime.utcnow()
                session.commit()
                
                return {
                    'success': True,
                    'message': 'Blog updated (simulated)'
                }
                
        except Exception as e:
            logger.error(f"Error updating blog post: {e}")
            return {
                'success': False,
                'message': str(e)
            } 