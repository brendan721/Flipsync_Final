#!/bin/bash

# Exit any virtual environment
if [[ -n "$VIRTUAL_ENV" ]]; then
    echo "Exiting virtual environment: $VIRTUAL_ENV"
    deactivate 2>/dev/null || true
fi

# Ensure we're in the mobile directory
cd /home/brend/Flipsync_Final/mobile

echo "Current directory: $(pwd)"
echo "Virtual environment check: $VIRTUAL_ENV"

# Set Chrome executable for web development
export CHROME_EXECUTABLE="/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"

echo "=== Flutter Environment Setup ==="

# Clean previous builds
echo "1. Cleaning Flutter project..."
flutter clean

# Get dependencies
echo "2. Getting Flutter dependencies..."
flutter pub get

# Repair build runner
echo "3. Repairing build runner..."
dart run build_runner repair

# Run build runner clean
echo "4. Cleaning build runner cache..."
dart run build_runner clean

# Check Flutter doctor
echo "5. Checking Flutter doctor..."
flutter doctor

echo "=== Flutter Environment Setup Complete ==="
