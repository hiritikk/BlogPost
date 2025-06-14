#!/bin/bash

# Re-Defined Blog Automation System Setup Script

echo "🚀 Re-Defined Blog Automation System Setup"
echo "=========================================="

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if [[ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]]; then
    echo "❌ Error: Python 3.9+ is required. You have Python $python_version"
    exit 1
fi
echo "✅ Python $python_version detected"

# Create virtual environment
echo -e "\n📦 Creating virtual environment..."
python3 -m venv venv
echo "✅ Virtual environment created"

# Activate virtual environment
echo -e "\n🔄 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo -e "\n📦 Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo -e "\n📦 Installing dependencies..."
pip install -r requirements.txt
echo "✅ Dependencies installed"

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo -e "\n📝 Creating .env file..."
    cp env.example .env
    echo "✅ .env file created from env.example"
    echo "⚠️  Please edit .env and add your API keys!"
else
    echo -e "\n✅ .env file already exists"
fi

# Create necessary directories
echo -e "\n📁 Creating directories..."
mkdir -p logs
mkdir -p published_blogs
mkdir -p web/static
echo "✅ Directories created"

# Initialize database
echo -e "\n🗄️ Initializing database..."
python src/database/init_db.py
echo "✅ Database initialized"

# Create a simple run script
echo -e "\n📝 Creating run scripts..."

# Create run_app.sh
cat > run_app.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python app.py
EOF
chmod +x run_app.sh

# Create run_dashboard.sh
cat > run_dashboard.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
streamlit run dashboard.py
EOF
chmod +x run_dashboard.sh

echo "✅ Run scripts created"

# Display next steps
echo -e "\n✨ Setup complete!"
echo -e "\n📋 Next steps:"
echo "1. Edit .env file and add your API keys:"
echo "   - OPENAI_API_KEY (required)"
echo "   - Other API keys as needed"
echo ""
echo "2. Run the demo to test the system:"
echo "   python demo.py"
echo ""
echo "3. Start the web application:"
echo "   ./run_app.sh"
echo ""
echo "4. Start the dashboard (in a new terminal):"
echo "   ./run_dashboard.sh"
echo ""
echo "5. Access the services:"
echo "   - API: http://localhost:8000"
echo "   - Dashboard: http://localhost:8501"
echo ""
echo "Happy blogging! 📝✨" 