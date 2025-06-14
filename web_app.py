"""
Re-Defined Blog Website - Beautiful Local Website with Tailwind CSS
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, desc
from typing import Optional
import uvicorn
from loguru import logger

from config.settings import settings
from src.database.models import BlogPost, Source, GenerationData, TrendingTopic
from src.database.init_db import get_session

# Initialize FastAPI app
app = FastAPI(
    title="Re-Defined Blog Website",
    description="Beautiful blog website showcasing AI-generated content",
    version="1.0.0"
)

# Setup templates and static files
templates = Jinja2Templates(directory="web/templates")
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Database setup
engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_blog_stats():
    """Get blog statistics for the homepage"""
    try:
        session = get_session()
        total_blogs = session.query(BlogPost).count()
        published_blogs = session.query(BlogPost).filter_by(status='published').count()
        trending_topics = session.query(TrendingTopic).count()
        
        return {
            'total_blogs': total_blogs,
            'published_blogs': published_blogs,
            'trending_topics': trending_topics
        }
    except Exception as e:
        logger.error(f"Error getting blog stats: {e}")
        return {
            'total_blogs': 0,
            'published_blogs': 0,
            'trending_topics': 0
        }

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Homepage with beautiful landing page"""
    try:
        # Get statistics
        stats = get_blog_stats()
        
        # Get latest blogs
        session = get_session()
        latest_blogs = session.query(BlogPost)\
            .order_by(desc(BlogPost.created_at))\
            .limit(6)\
            .all()
        
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": stats,
            "latest_blogs": latest_blogs
        })
    except Exception as e:
        logger.error(f"Error in home route: {e}")
        return templates.TemplateResponse("index.html", {
            "request": request,
            "stats": {'total_blogs': 0, 'published_blogs': 0, 'trending_topics': 0},
            "latest_blogs": []
        })

@app.get("/blogs", response_class=HTMLResponse)
async def blog_list(
    request: Request, 
    status: Optional[str] = Query(None, description="Filter by blog status")
):
    """Blog listing page"""
    try:
        session = get_session()
        
        # Build query
        query = session.query(BlogPost)
        if status:
            query = query.filter_by(status=status)
        
        # Get blogs
        blogs = query.order_by(desc(BlogPost.created_at)).all()
        total_blogs = session.query(BlogPost).count()
        
        return templates.TemplateResponse("blogs.html", {
            "request": request,
            "blogs": blogs,
            "total_blogs": total_blogs,
            "status": status
        })
    except Exception as e:
        logger.error(f"Error in blog_list route: {e}")
        return templates.TemplateResponse("blogs.html", {
            "request": request,
            "blogs": [],
            "total_blogs": 0,
            "status": status
        })

@app.get("/blog/{slug}", response_class=HTMLResponse)
async def blog_detail(request: Request, slug: str):
    """Individual blog post page"""
    try:
        session = get_session()
        
        # Get blog post
        blog = session.query(BlogPost).filter_by(slug=slug).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog post not found")
        
        # Get sources for this blog
        sources = session.query(Source)\
            .filter_by(blog_post_id=blog.id)\
            .all()
        
        # Get generation data
        generation_data = session.query(GenerationData)\
            .filter_by(blog_post_id=blog.id)\
            .first()
        
        return templates.TemplateResponse("blog_post.html", {
            "request": request,
            "blog": blog,
            "sources": sources,
            "generation_data": generation_data
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in blog_detail route: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        session = get_session()
        blog_count = session.query(BlogPost).count()
        
        return {
            "status": "healthy",
            "database": "connected",
            "blog_count": blog_count,
            "message": "Blog website is running successfully"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/api/stats")
async def get_stats():
    """Get blog statistics API"""
    try:
        stats = get_blog_stats()
        
        # Add more detailed stats
        session = get_session()
        drafts = session.query(BlogPost).filter_by(status='draft').count()
        scheduled = session.query(BlogPost).filter_by(status='scheduled').count()
        
        stats.update({
            'drafts': drafts,
            'scheduled': scheduled
        })
        
        return stats
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return {"error": str(e)}

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Custom 404 page"""
    return templates.TemplateResponse("404.html", {
        "request": request
    }, status_code=404)

@app.exception_handler(500)
async def server_error_handler(request: Request, exc: HTTPException):
    """Custom 500 page"""
    return templates.TemplateResponse("500.html", {
        "request": request
    }, status_code=500)

if __name__ == "__main__":
    # Configure logging
    logger.add(
        settings.logs_path / "web_app.log",
        rotation="500 MB",
        retention="10 days",
        level=settings.log_level
    )
    
    logger.info("Starting Re-Defined Blog Website...")
    
    # Run the web application
    uvicorn.run(
        "web_app:app",
        host=settings.app_host,
        port=8080,  # Different port from the API
        reload=True,
        log_level=settings.log_level.lower()
    ) 