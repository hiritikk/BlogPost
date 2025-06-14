#!/bin/bash

# Re-Defined Blog Automation - Website Startup Script

echo "🚀 Starting Re-Defined Blog Automation System"
echo "============================================="

# Activate virtual environment
source venv/bin/activate

echo "✅ Virtual environment activated"

# Check if database exists
if [ ! -f "re_defined_blogs.db" ]; then
    echo "📅 Initializing database..."
    python src/database/init_db.py
    echo "✅ Database initialized"
fi

# Start the beautiful website
echo "🌐 Starting beautiful blog website on http://localhost:8080"
echo "🎨 Features: Tailwind CSS, responsive design, beautiful UI"

# Run the web application
python web_app.py

echo "�� Website stopped" 