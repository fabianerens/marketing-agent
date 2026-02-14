#!/bin/bash
# Quick start script for YouTube Marketing Agent

set -e

echo "🎬 YouTube Marketing Agent"
echo "=========================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found!"
    echo "Creating from .env.example..."
    cp .env.example .env
    echo ""
    echo "✓ Created .env file"
    echo ""
    echo "📝 NEXT STEPS:"
    echo "1. Edit .env and add your API keys:"
    echo "   - YOUTUBE_API_KEY"
    echo "   - GOOGLE_API_KEY"
    echo "2. Run this script again"
    echo ""
    exit 1
fi

# Check if dependencies are installed
if [ ! -d ".venv" ] && ! command -v uv &> /dev/null; then
    echo "⚠️  No virtual environment found and uv not installed"
    echo ""
    echo "Installing dependencies..."
    if command -v uv &> /dev/null; then
        uv sync
    else
        python -m venv .venv
        source .venv/bin/activate
        pip install -e .
    fi
fi

# Create data directory
mkdir -p data

echo "🚀 Starting application..."
echo ""

# Run app
if command -v uv &> /dev/null; then
    uv run python -m app.gradio_app
else
    source .venv/bin/activate
    python -m app.gradio_app
fi
