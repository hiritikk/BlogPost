"""
Database models for Re-Defined Blog Automation System
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid

Base = declarative_base()

class BlogPost(Base):
    """Model for blog posts"""
    __tablename__ = "blog_posts"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False)
    slug = Column(String(250), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text)
    meta_description = Column(String(160))
    keywords = Column(JSON)  # List of keywords
    
    # Thumbnail and images
    thumbnail_url = Column(String)
    banner_image_url = Column(String)
    
    # Content metadata
    word_count = Column(Integer)
    reading_time = Column(Integer)  # in minutes
    tone_analysis = Column(JSON)  # Analysis of tone/style
    
    # Publishing info
    status = Column(String(50), default="draft")  # draft, scheduled, published, failed
    scheduled_date = Column(DateTime)
    published_date = Column(DateTime)
    website_post_id = Column(String)  # ID from the website after publishing
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sources = relationship("Source", back_populates="blog_post", cascade="all, delete-orphan")
    generation_data = relationship("GenerationData", back_populates="blog_post", uselist=False)

class Source(Base):
    """Model for content sources and citations"""
    __tablename__ = "sources"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    blog_post_id = Column(String, ForeignKey("blog_posts.id"))
    
    source_type = Column(String(50))  # article, website, social_media, research
    title = Column(String(300))
    author = Column(String(200))
    url = Column(String)
    publication_date = Column(DateTime)
    
    # Citation info
    citation_text = Column(Text)  # The actual text cited
    citation_location = Column(Integer)  # Position in the blog content
    
    # Metadata
    credibility_score = Column(Integer)  # 1-10 score
    relevance_score = Column(Integer)  # 1-10 score
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    blog_post = relationship("BlogPost", back_populates="sources")

class GenerationData(Base):
    """Model for storing AI generation metadata"""
    __tablename__ = "generation_data"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    blog_post_id = Column(String, ForeignKey("blog_posts.id"), unique=True)
    
    # Generation parameters
    model_used = Column(String(100))
    prompt_template = Column(Text)
    temperature = Column(Integer)
    
    # Research data
    search_queries = Column(JSON)  # List of queries used
    scraped_urls = Column(JSON)  # List of URLs scraped
    trending_topics = Column(JSON)  # Topics identified as trending
    
    # Performance metrics
    generation_time = Column(Integer)  # in seconds
    tokens_used = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    blog_post = relationship("BlogPost", back_populates="generation_data")

class ScheduledTask(Base):
    """Model for scheduling blog generation and publishing"""
    __tablename__ = "scheduled_tasks"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_type = Column(String(50))  # generate, publish, scrape
    status = Column(String(50), default="pending")  # pending, running, completed, failed
    
    scheduled_for = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Task data
    parameters = Column(JSON)
    result = Column(JSON)
    error_message = Column(Text)
    retry_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class TrendingTopic(Base):
    """Model for storing trending topics from various sources"""
    __tablename__ = "trending_topics"
    
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    source = Column(String(100))  # linkedin, forbes, news, etc.
    topic = Column(String(300))
    description = Column(Text)
    relevance_score = Column(Integer)  # 1-10
    
    # Metadata
    source_url = Column(String)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    used_in_post = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow) 