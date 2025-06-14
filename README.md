# Re-Defined Newsletter Automation System

An AI-powered blog automation system that generates, schedules, and publishes educational content for international students and young professionals.

## 🚀 Features

- **AI-Powered Content Generation**: Creates engaging blog posts using GPT-4
- **Automated Research**: Scrapes trending topics from LinkedIn, Forbes, and educational sources
- **Thumbnail Generation**: Automatically creates eye-catching images for each post
- **SEO Optimization**: Built-in meta descriptions and keyword optimization
- **Citation Management**: Tracks and cites all sources used in content
- **Scheduling System**: Publishes blogs bi-weekly automatically
- **Customizable Voice**: Maintains Re-Defined's community-first tone
- **Web Dashboard**: Easy-to-use interface for monitoring and customization

## 📋 Requirements

- Python 3.9+
- OpenAI API Key
- Database (PostgreSQL or SQLite)
- Image generation API access (DALL-E or Stable Diffusion)
- Web hosting for dashboard

## 🛠️ Installation

1. Clone the repository:

```bash
git clone https://github.com/re-defined/blog-automation.git
cd blog-automation
```

2. Create virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Set up environment variables:

```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

5. Initialize database:

```bash
python src/database/init_db.py
```

6. Run the application:

```bash
python app.py
```

## 🏗️ Project Structure

```
re-defined-blog-automation/
├── src/
│   ├── content_generator/      # AI content generation
│   ├── scraper/               # Web scraping for trends
│   ├── image_generator/       # Thumbnail creation
│   ├── seo_optimizer/         # SEO tools
│   ├── publisher/             # Publishing automation
│   ├── scheduler/             # Scheduling system
│   └── database/              # Database models
├── web/                       # Web dashboard
├── tests/                     # Test suite
├── config/                    # Configuration files
└── logs/                      # Application logs
```

## 📝 Usage

### Generate a Blog Post

```python
from src.content_generator import BlogGenerator

generator = BlogGenerator()
blog = generator.create_blog(
    topic="Tips for International Students",
    word_count=500
)
```

### Schedule Publication

```python
from src.scheduler import BlogScheduler

scheduler = BlogScheduler()
scheduler.schedule_blog(blog, publish_date="2024-06-26")
```

## 🎯 Content Guidelines

- **Length**: 300-600 words
- **Tone**: Friendly, supportive, community-focused
- **Topics**: Education, career development, job market insights
- **Audience**: International students and young professionals

## 📊 Success Metrics

- ✅ 2 blogs auto-published during testing
- ✅ Custom thumbnails generated
- ✅ SEO meta descriptions included
- ✅ Sources properly cited
- ✅ Bi-weekly automation ready

## 🤝 Support

For questions or issues, please contact the development team.
