"""
Re-Defined Blog Automation System - Main Application
"""
import os
import sys
from pathlib import Path
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from loguru import logger

# Add project root to path
sys.path.append(str(Path(__file__).parent))

from src.database.init_db import init_database
from src.scheduler.scheduler import BlogScheduler
from src.content_generator.generator import BlogGenerator
from src.database.models import BlogPost
from src.database.init_db import get_session
from config.settings import settings

# Initialize FastAPI app
app = FastAPI(
    title="Re-Defined Blog Automation",
    description="AI-powered blog automation system for Re-Defined",
    version="1.0.0"
)

# Static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Initialize scheduler
scheduler = BlogScheduler()

# Request/Response models
class BlogGenerationRequest(BaseModel):
    topic: str
    custom_instructions: Optional[str] = None
    schedule_date: Optional[datetime] = None

class BlogResponse(BaseModel):
    id: str
    title: str
    slug: str
    status: str
    created_at: datetime
    published_date: Optional[datetime] = None
    url: Optional[str] = None

class TaskResponse(BaseModel):
    id: str
    task_type: str
    status: str
    scheduled_for: datetime
    result: Optional[dict] = None
    error_message: Optional[str] = None

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup"""
    logger.info("Starting Re-Defined Blog Automation System...")
    
    # Initialize database
    init_database()
    
    # Start scheduler
    scheduler.start()
    
    logger.info("Application started successfully!")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down application...")
    scheduler.stop()

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Re-Defined Blog Automation System",
        "status": "running",
        "version": "1.0.0"
    }

@app.post("/generate", response_model=BlogResponse)
async def generate_blog(request: BlogGenerationRequest, background_tasks: BackgroundTasks):
    """Generate a new blog post"""
    try:
        if request.schedule_date and request.schedule_date > datetime.utcnow():
            # Schedule for later
            task_id = scheduler.schedule_custom_blog(
                topic=request.topic,
                scheduled_date=request.schedule_date,
                custom_instructions=request.custom_instructions
            )
            
            return BlogResponse(
                id=task_id,
                title=f"Scheduled: {request.topic}",
                slug="pending",
                status="scheduled",
                created_at=datetime.utcnow(),
                published_date=request.schedule_date
            )
        else:
            # Generate immediately
            generator = BlogGenerator()
            blog_post = generator.create_blog(
                topic=request.topic,
                custom_instructions=request.custom_instructions
            )
            
            return BlogResponse(
                id=blog_post.id,
                title=blog_post.title,
                slug=blog_post.slug,
                status=blog_post.status,
                created_at=blog_post.created_at,
                published_date=blog_post.published_date,
                url=f"https://re-defined.ca/blog/{blog_post.slug}" if blog_post.status == "published" else None
            )
            
    except Exception as e:
        logger.error(f"Blog generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/blogs", response_model=List[BlogResponse])
async def list_blogs(status: Optional[str] = None, limit: int = 20):
    """List blog posts"""
    session = get_session()
    query = session.query(BlogPost)
    
    if status:
        query = query.filter_by(status=status)
    
    blogs = query.order_by(BlogPost.created_at.desc()).limit(limit).all()
    
    return [
        BlogResponse(
            id=blog.id,
            title=blog.title,
            slug=blog.slug,
            status=blog.status,
            created_at=blog.created_at,
            published_date=blog.published_date,
            url=f"https://re-defined.ca/blog/{blog.slug}" if blog.status == "published" else None
        )
        for blog in blogs
    ]

@app.get("/blogs/{blog_id}", response_model=BlogResponse)
async def get_blog(blog_id: str):
    """Get a specific blog post"""
    session = get_session()
    blog = session.query(BlogPost).filter_by(id=blog_id).first()
    
    if not blog:
        raise HTTPException(status_code=404, detail="Blog post not found")
    
    return BlogResponse(
        id=blog.id,
        title=blog.title,
        slug=blog.slug,
        status=blog.status,
        created_at=blog.created_at,
        published_date=blog.published_date,
        url=f"https://re-defined.ca/blog/{blog.slug}" if blog.status == "published" else None
    )

@app.post("/blogs/{blog_id}/publish")
async def publish_blog(blog_id: str):
    """Publish a blog post"""
    try:
        from src.publisher.publisher import BlogPublisher
        publisher = BlogPublisher()
        result = publisher.publish_blog(blog_id)
        
        if result['success']:
            return {"message": "Blog published successfully", "url": result.get('url')}
        else:
            raise HTTPException(status_code=400, detail=result.get('message'))
            
    except Exception as e:
        logger.error(f"Publishing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scrape-trends")
async def scrape_trends(background_tasks: BackgroundTasks):
    """Trigger trend scraping"""
    background_tasks.add_task(scheduler.scrape_trends_task)
    return {"message": "Trend scraping started"}

@app.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(status: Optional[str] = None):
    """List scheduled tasks"""
    tasks = scheduler.get_scheduled_tasks(status)
    
    return [
        TaskResponse(
            id=task.id,
            task_type=task.task_type,
            status=task.status,
            scheduled_for=task.scheduled_for,
            result=task.result,
            error_message=task.error_message
        )
        for task in tasks
    ]

@app.post("/tasks/{task_id}/retry")
async def retry_task(task_id: str):
    """Retry a failed task"""
    success = scheduler.retry_failed_task(task_id)
    
    if success:
        return {"message": "Task scheduled for retry"}
    else:
        raise HTTPException(status_code=400, detail="Cannot retry this task")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected",
        "scheduler": "running" if scheduler.scheduler.running else "stopped"
    }

if __name__ == "__main__":
    import uvicorn
    
    # Configure logging
    logger.add(
        settings.logs_path / "app.log",
        rotation="500 MB",
        retention="10 days",
        level=settings.log_level
    )
    
    # Run the application
    uvicorn.run(
        "app:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=True,
        log_level=settings.log_level.lower()
    ) 