#!/bin/bash

# Re-Defined Blog Automation - Complete Startup Script
# This script starts everything you need: database, website, and dashboard

clear
echo "🚀 Re-Defined Blog Automation - Complete Setup"
echo "=============================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_error "Virtual environment not found!"
    echo "Please run: python -m venv venv"
    exit 1
fi

# Activate virtual environment
print_info "Activating virtual environment..."
source venv/bin/activate
print_status "Virtual environment activated"

# Check if requirements are installed
print_info "Checking dependencies..."
if ! python -c "import fastapi, streamlit, sqlalchemy" 2>/dev/null; then
    print_warning "Installing missing dependencies..."
    pip install -r requirements.txt
    print_status "Dependencies installed"
else
    print_status "All dependencies are installed"
fi

# Initialize database if it doesn't exist
if [ ! -f "re_defined_blogs.db" ]; then
    print_info "Initializing database..."
    python src/database/init_db.py
    print_status "Database initialized"
else
    print_status "Database already exists"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    print_warning "Creating .env file from template..."
    cp env.example .env
    print_warning "Please edit .env file and add your OpenAI API key!"
    echo ""
    echo "To edit: nano .env"
    echo "Add your OpenAI API key to OPENAI_API_KEY="
    echo ""
fi

# Create logs directory if it doesn't exist
mkdir -p logs

print_status "Setup complete! Starting services..."
echo ""

# Function to kill background processes on exit
cleanup() {
    print_info "Stopping all services..."
    jobs -p | xargs -r kill
    print_status "All services stopped"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM EXIT

# Start the beautiful website
print_info "Starting beautiful blog website..."
echo "🌐 Website will be available at: http://localhost:8080"
python web_app.py &
WEBSITE_PID=$!

# Wait a moment for the website to start
sleep 3

# Start the Streamlit dashboard
print_info "Starting Streamlit dashboard..."
echo "🎛️  Dashboard will be available at: http://localhost:8501"
streamlit run dashboard.py --server.port 8501 --server.headless true &
DASHBOARD_PID=$!

# Wait for services to start
sleep 5

# Check if services are running
if kill -0 $WEBSITE_PID 2>/dev/null; then
    print_status "Website is running on http://localhost:8080"
else
    print_error "Website failed to start"
fi

if kill -0 $DASHBOARD_PID 2>/dev/null; then
    print_status "Dashboard is running on http://localhost:8501"
else
    print_error "Dashboard failed to start"
fi

echo ""
echo "🎉 Re-Defined Blog Automation is now running!"
echo "=============================================="
echo ""
echo "📱 Services Available:"
echo "   🌐 Beautiful Website:  http://localhost:8080"
echo "   🎛️  Admin Dashboard:   http://localhost:8501"
echo "   📊 Health Check:      http://localhost:8080/api/health"
echo "   📈 Statistics:        http://localhost:8080/api/stats"
echo ""
echo "🎯 Quick Start:"
echo "   1. Visit http://localhost:8501 to create blog posts"
echo "   2. View them on http://localhost:8080"
echo "   3. Generate AI content using the dashboard"
echo ""
echo "💡 Tips:"
echo "   - Add your OpenAI API key to .env file for content generation"
echo "   - Check logs/ directory for any errors"
echo "   - Press Ctrl+C to stop all services"
echo ""

# Keep script running and wait for user to stop
print_info "Services are running... Press Ctrl+C to stop all services"
wait 