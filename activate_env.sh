#!/bin/bash
# FlipSync Environment Activation Script
# Ensures proper Python environment setup for development and testing

set -e

echo "🔧 FlipSync Environment Activation"
echo "=================================="

# Check if we're in the correct directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: Not in FlipSync project directory"
    echo "   Please run this script from /root/projects/flipsync/fs_clean"
    exit 1
fi

# Activate virtual environment
if [ -d "venv" ]; then
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
    echo "   Python: $(which python)"
    echo "   Version: $(python --version)"
else
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    echo "✅ Virtual environment created and activated"
fi

# Set environment variables
export PYTHONPATH="/root/projects/flipsync/fs_clean:$PYTHONPATH"
export FLIPSYNC_ENV="development"
export FLIPSYNC_DEBUG="true"

echo ""
echo "🌍 Environment variables set:"
echo "   PYTHONPATH: $PYTHONPATH"
echo "   FLIPSYNC_ENV: $FLIPSYNC_ENV"
echo "   FLIPSYNC_DEBUG: $FLIPSYNC_DEBUG"

echo ""
echo "✅ Environment ready for FlipSync development!"
echo "   Run tests with: python -m pytest"
echo "   Start app with: python -m uvicorn fs_agt_clean.app.main:app --reload"
