#!/bin/bash

echo "🌐 Starting FlipSync Web Testing Environment"
echo "============================================"

# Navigate to mobile project
cd /home/brend/Flipsync_Final/mobile

# Check Flutter web support
echo "📋 Checking Flutter web support..."
flutter config --enable-web
echo ""

# Check available devices
echo "📱 Available devices:"
flutter devices
echo ""

# Clean and get dependencies
echo "📦 Preparing dependencies..."
flutter clean
flutter pub get
echo ""

# Check if we can build for web
echo "🏗️ Testing web build capability..."
flutter build web --debug > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Web build successful"
else
    echo "❌ Web build failed - checking issues..."
    flutter build web --debug
    exit 1
fi
echo ""

# Start web server
echo "🚀 Starting Flutter web server..."
echo "📍 Access URL: http://localhost:3000"
echo "🔄 Hot reload enabled for development"
echo "⏹️  Press Ctrl+C to stop server"
echo ""
echo "🤖 AI can now access and test the application at:"
echo "   http://localhost:3000"
echo ""

# Start with hot reload for development
flutter run -d web-server --web-port 3000 --web-hostname 0.0.0.0 --hot
