#!/bin/bash

# Notion Task Sync Launcher

echo "🚀 Starting Notion Task Sync..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "Please copy env.example to .env and configure your tokens:"
    echo "  cp env.example .env"
    echo "  # Then edit .env with your Notion credentials"
    exit 1
fi

# Check if dependencies are installed
if ! python -c "import notion_client, plyer" 2>/dev/null; then
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Test connection first
echo "🧪 Testing Notion connection..."
python test_connection.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Connection test passed! Starting notification system..."
    echo "Press Ctrl+C to stop"
    echo ""
    python notion_sync.py
else
    echo ""
    echo "❌ Connection test failed. Please fix the issues above before running."
    exit 1
fi 