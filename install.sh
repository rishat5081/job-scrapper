#!/bin/bash
# One-command installation script for Job Tracker

echo "🎯 Job Tracker Installation"
echo "======================================"
echo ""

cd "$(dirname "$0")"

# Step 1: Create virtual environment
echo "📦 Step 1/4: Creating virtual environment..."
if [ -d "venv" ]; then
    echo "   ✅ Virtual environment already exists"
else
    python3 -m venv venv
    if [ $? -eq 0 ]; then
        echo "   ✅ Virtual environment created"
    else
        echo "   ❌ Failed to create virtual environment"
        exit 1
    fi
fi

# Step 2: Install dependencies
echo ""
echo "📚 Step 2/4: Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

if [ $? -eq 0 ]; then
    echo "   ✅ Dependencies installed"
else
    echo "   ❌ Failed to install dependencies"
    exit 1
fi

# Step 3: Run initial scrape
echo ""
echo "🔍 Step 3/4: Scraping initial jobs..."
python job_scraper.py scrape

# Step 4: Create desktop shortcut (optional)
echo ""
echo "🔗 Step 4/4: Creating start script..."
chmod +x start_server.sh auto_scraper.sh setup_auto_scraper.sh

echo ""
echo "======================================"
echo "✅ Installation Complete!"
echo "======================================"
echo ""
echo "📊 To start the dashboard:"
echo "   ./start_server.sh"
echo ""
echo "   Then open: http://localhost:5000"
echo ""
echo "🔄 To setup automated scraping (optional):"
echo "   ./setup_auto_scraper.sh"
echo ""
echo "📖 Read README_SCRAPER.md for full documentation"
echo ""
