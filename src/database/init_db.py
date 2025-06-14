"""
Database initialization script
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Base
from config.settings import settings
from loguru import logger

def init_database():
    """Initialize the database and create all tables"""
    try:
        # Create engine
        engine = create_engine(settings.database_url, echo=True)
        
        # Create all tables
        Base.metadata.create_all(engine)
        
        logger.info(f"Database initialized successfully at {settings.database_url}")
        return engine
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

def get_session():
    """Get a database session"""
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    return Session()

if __name__ == "__main__":
    init_database() 