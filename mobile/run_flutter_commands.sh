#!/bin/bash

# Force exit any virtual environment
unset VIRTUAL_ENV
unset PYTHONPATH

# Change to mobile directory
cd /home/brend/Flipsync_Final/mobile

# Set environment variables
export CHROME_EXECUTABLE="/mnt/c/Program Files/Google/Chrome/Application/chrome.exe"
export ANDROID_HOME="/home/brend/development/android-sdk"

echo "=== Flutter Environment Setup - Complete Solution ==="
echo "Current directory: $(pwd)"
echo "Virtual environment: ${VIRTUAL_ENV:-'None'}"
echo "Flutter path: $(which flutter)"
echo "Chrome executable: $CHROME_EXECUTABLE"
echo "Android SDK: $ANDROID_HOME"

# Clean and get dependencies
echo ""
echo "1. Cleaning Flutter project..."
flutter clean

echo ""
echo "2. Getting Flutter dependencies..."
flutter pub get

echo ""
echo "3. Running build runner repair..."
dart run build_runner repair

echo ""
echo "4. Cleaning build runner cache..."
dart run build_runner clean

echo ""
echo "5. Checking Flutter doctor..."
flutter doctor

echo ""
echo "6. Testing Flutter web build..."
flutter build web

echo ""
echo "7. Starting Flutter web server on port 3000..."
echo "   Access your app at: http://localhost:3000"
echo "   Press Ctrl+C to stop the server"
flutter run -d web-server --web-port 3000

echo ""
echo "=== Flutter Environment Setup Complete ==="
