"""
AI-powered blog content generator for Re-Defined
"""
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
from loguru import logger
import tiktoken
from src.database.models import BlogPost, Source, GenerationData
from src.database.init_db import get_session
from config.settings import settings
from src.utils.text_utils import generate_slug, count_words, estimate_reading_time

class BlogGenerator:
    """Generates blog content using OpenAI GPT models"""
    
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.encoder = tiktoken.encoding_for_model(self.model)
        
    def create_blog(
        self,
        topic: str,
        trending_data: Optional[Dict] = None,
        sources: Optional[List[Dict]] = None,
        custom_instructions: Optional[str] = None
    ) -> BlogPost:
        """
        Generate a complete blog post
        
        Args:
            topic: Main topic for the blog
            trending_data: Data from trending topics research
            sources: List of sources to cite
            custom_instructions: Additional instructions for content generation
            
        Returns:
            BlogPost object ready for publishing
        """
        start_time = time.time()
        
        # Generate blog content
        content_data = self._generate_content(topic, trending_data, sources, custom_instructions)
        
        # Create blog post object
        blog_post = BlogPost(
            title=content_data['title'],
            slug=generate_slug(content_data['title']),
            content=content_data['content'],
            summary=content_data['summary'],
            meta_description=content_data['meta_description'],
            keywords=content_data['keywords'],
            word_count=count_words(content_data['content']),
            reading_time=estimate_reading_time(content_data['content']),
            tone_analysis=self._analyze_tone(content_data['content']),
            status="draft"
        )
        
        # Save to database
        session = get_session()
        session.add(blog_post)
        
        # Add sources if provided
        if sources:
            for source_data in sources:
                source = Source(
                    blog_post_id=blog_post.id,
                    source_type=source_data.get('type', 'article'),
                    title=source_data.get('title'),
                    author=source_data.get('author'),
                    url=source_data.get('url'),
                    publication_date=source_data.get('publication_date'),
                    citation_text=source_data.get('citation_text'),
                    credibility_score=source_data.get('credibility_score', 8),
                    relevance_score=source_data.get('relevance_score', 8)
                )
                session.add(source)
        
        # Add generation metadata
        generation_data = GenerationData(
            blog_post_id=blog_post.id,
            model_used=self.model,
            prompt_template=self._get_prompt_template(),
            temperature=0.8,
            generation_time=int(time.time() - start_time),
            tokens_used=self._count_tokens(content_data['content']),
            search_queries=trending_data.get('search_queries', []) if trending_data else [],
            scraped_urls=trending_data.get('scraped_urls', []) if trending_data else [],
            trending_topics=trending_data.get('topics', []) if trending_data else []
        )
        session.add(generation_data)
        
        session.commit()
        logger.info(f"Blog post created: {blog_post.title} (ID: {blog_post.id})")
        
        return blog_post
    
    def _generate_content(
        self,
        topic: str,
        trending_data: Optional[Dict] = None,
        sources: Optional[List[Dict]] = None,
        custom_instructions: Optional[str] = None
    ) -> Dict[str, any]:
        """Generate the actual blog content using OpenAI"""
        
        # Build the prompt
        prompt = self._build_prompt(topic, trending_data, sources, custom_instructions)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=1500
            )
            
            # Parse the response
            content = response.choices[0].message.content
            return self._parse_blog_response(content)
            
        except Exception as e:
            logger.error(f"Failed to generate content: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for blog generation"""
        tone_description = ", ".join(settings.blog_tone)
        return f"""You are a professional content writer for Re-Defined, a platform supporting international students and young professionals.

Your writing style is {tone_description}. You write engaging, informative blog posts that provide real value to readers.

Guidelines:
1. Write in a conversational yet professional tone
2. Include actionable advice and practical tips
3. Use statistics and facts when available (cite sources)
4. Keep content between {settings.min_word_count}-{settings.max_word_count} words
5. Structure content with clear headings and sections
6. End with a compelling call-to-action
7. Focus on the experiences and challenges of international students and newcomers

Format your response as a JSON object with the following structure:
{{
    "title": "Compelling blog title",
    "content": "Full blog content with markdown formatting",
    "summary": "2-3 sentence summary",
    "meta_description": "SEO meta description (max 160 chars)",
    "keywords": ["keyword1", "keyword2", "keyword3"]
}}"""
    
    def _build_prompt(
        self,
        topic: str,
        trending_data: Optional[Dict] = None,
        sources: Optional[List[Dict]] = None,
        custom_instructions: Optional[str] = None
    ) -> str:
        """Build the content generation prompt"""
        prompt_parts = [f"Write a blog post about: {topic}"]
        
        if trending_data and trending_data.get('topics'):
            prompt_parts.append(f"\nIncorporate these trending topics where relevant:")
            for trend in trending_data['topics'][:3]:
                prompt_parts.append(f"- {trend}")
        
        if sources:
            prompt_parts.append(f"\nUse these sources for facts and statistics:")
            for source in sources[:5]:
                prompt_parts.append(f"- {source.get('title', 'Unknown')} ({source.get('url', '')})")
        
        if custom_instructions:
            prompt_parts.append(f"\nAdditional instructions: {custom_instructions}")
        
        prompt_parts.append(f"\nRemember to maintain Re-Defined's voice and focus on value for international students.")
        
        return "\n".join(prompt_parts)
    
    def _parse_blog_response(self, response: str) -> Dict[str, any]:
        """Parse the AI response into structured data"""
        try:
            # Try to parse as JSON
            data = json.loads(response)
            
            # Validate required fields
            required_fields = ['title', 'content', 'summary', 'meta_description', 'keywords']
            for field in required_fields:
                if field not in data:
                    raise ValueError(f"Missing required field: {field}")
            
            return data
            
        except json.JSONDecodeError:
            # If not valid JSON, try to extract content manually
            logger.warning("Response is not valid JSON, attempting manual parsing")
            return self._manual_parse_response(response)
    
    def _manual_parse_response(self, response: str) -> Dict[str, any]:
        """Manually parse response if JSON parsing fails"""
        # This is a fallback method
        lines = response.strip().split('\n')
        
        return {
            'title': lines[0] if lines else "Untitled Blog Post",
            'content': '\n'.join(lines[1:]) if len(lines) > 1 else response,
            'summary': f"A blog post about {lines[0][:100]}..." if lines else "Blog summary",
            'meta_description': lines[0][:160] if lines else "Blog post from Re-Defined",
            'keywords': ["international students", "career", "education"]
        }
    
    def _analyze_tone(self, content: str) -> Dict[str, float]:
        """Analyze the tone of the generated content"""
        # Simple tone analysis - could be enhanced with sentiment analysis
        tone_keywords = {
            'friendly': ['welcome', 'help', 'support', 'together', 'community'],
            'supportive': ['guide', 'assist', 'encourage', 'believe', 'achieve'],
            'informative': ['learn', 'discover', 'understand', 'explain', 'insight'],
            'professional': ['career', 'opportunity', 'develop', 'growth', 'success']
        }
        
        content_lower = content.lower()
        tone_scores = {}
        
        for tone, keywords in tone_keywords.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            tone_scores[tone] = min(score / len(keywords), 1.0)
        
        return tone_scores
    
    def _count_tokens(self, text: str) -> int:
        """Count the number of tokens in the text"""
        return len(self.encoder.encode(text))
    
    def _get_prompt_template(self) -> str:
        """Get the prompt template for reference"""
        return self._get_system_prompt()
    
    def regenerate_section(self, blog_post_id: str, section: str, instructions: str) -> str:
        """Regenerate a specific section of a blog post"""
        session = get_session()
        blog_post = session.query(BlogPost).filter_by(id=blog_post_id).first()
        
        if not blog_post:
            raise ValueError(f"Blog post not found: {blog_post_id}")
        
        prompt = f"""Given this blog post titled "{blog_post.title}", regenerate the {section} section.

Current content:
{blog_post.content}

Instructions for the new {section} section: {instructions}

Provide only the new section content, maintaining the same tone and style."""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.8,
                max_tokens=500
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Failed to regenerate section: {e}")
            raise 