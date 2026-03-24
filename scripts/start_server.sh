#!/bin/bash
# Start the JobIntel dashboard server

cd "$(dirname "$0")/.."

echo "🚀 Starting JobIntel dashboard..."
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "⚠️  Virtual environment not found. Creating it..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Check if Flask is installed
if ! python -c "import flask" 2>/dev/null; then
    echo "⚠️  Installing dependencies..."
    pip install -r requirements.txt
fi

echo "📊 Dashboard will be available at: http://localhost:8080"
echo "Press Ctrl+C to stop the server"
echo ""

# Start the Flask server
PYTHONPATH=src FLASK_DEBUG=1 FLASK_HOST=0.0.0.0 python -m jobintel.api_server
