"""
Application Settings Configuration
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Settings:
    """Application settings"""
    
    # Database
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./re_defined_blogs.db")
    
    # OpenAI
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # Web Application
    app_host: str = os.getenv("APP_HOST", "127.0.0.1")
    app_port: int = int(os.getenv("APP_PORT", "8000"))
    secret_key: str = os.getenv("SECRET_KEY", "local-dev-secret-key")
    
    # Static files and templates
    static_path: Path = Path("web/static")
    templates_path: Path = Path("web/templates")
    
    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    logs_path: Path = Path("logs")
    
    # Content Settings
    min_word_count: int = int(os.getenv("MIN_WORD_COUNT", "300"))
    max_word_count: int = int(os.getenv("MAX_WORD_COUNT", "600"))
    
    # Blog tone as list (split comma-separated string)
    @property
    def blog_tone(self):
        tone_str = os.getenv("BLOG_TONE", "friendly,supportive,informative,community-focused")
        return [tone.strip() for tone in tone_str.split(",")]
    
    # SEO
    default_meta_description_length: int = int(os.getenv("DEFAULT_META_DESCRIPTION_LENGTH", "160"))
    
    # Target keywords as list (split comma-separated string)
    @property
    def target_keywords(self):
        keywords_str = os.getenv("TARGET_KEYWORDS", "international students,career development,job search,networking")
        return [keyword.strip() for keyword in keywords_str.split(",")]
    
    # Publishing
    publish_interval_days: int = int(os.getenv("PUBLISH_INTERVAL_DAYS", "14"))
    website_api_endpoint: str = os.getenv("WEBSITE_API_ENDPOINT", "")
    website_api_key: str = os.getenv("WEBSITE_API_KEY", "")
    
    # Image Generation
    stability_api_key: str = os.getenv("STABILITY_API_KEY", "")
    dalle_api_key: str = os.getenv("DALLE_API_KEY", "")
    
    # Scraping Settings
    linkedin_search_terms: str = os.getenv("LINKEDIN_SEARCH_TERMS", "international students,career tips")
    forbes_categories: str = os.getenv("FORBES_CATEGORIES", "education,careers,leadership")
    news_api_key: str = os.getenv("NEWS_API_KEY", "")
    
    # Email Settings (Optional)
    smtp_host: str = os.getenv("SMTP_HOST", "smtp.gmail.com")
    smtp_port: int = int(os.getenv("SMTP_PORT", "587"))
    smtp_user: str = os.getenv("SMTP_USER", "")
    smtp_password: str = os.getenv("SMTP_PASSWORD", "")
    notification_email: str = os.getenv("NOTIFICATION_EMAIL", "")
    
    # Monitoring
    sentry_dsn: str = os.getenv("SENTRY_DSN", "")
    
    # Redis/Scheduling (fallback for compatibility)
    redis_url: str = os.getenv("REDIS_URL", "sqlite:///./scheduler.db")

# Create settings instance
settings = Settings() 