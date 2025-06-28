#!/bin/bash
# Chrome Development Launch Script for FlipSync Mobile Testing

echo "🌐 Launching Chrome for FlipSync Mobile Development"
echo "This will open Chrome with CORS disabled for local development"
echo ""

# Create temporary user data directory
TEMP_DIR="/tmp/chrome_flipsync_dev"
mkdir -p "$TEMP_DIR"

# Chrome executable paths for different systems
if command -v google-chrome &> /dev/null; then
    CHROME_CMD="google-chrome"
elif command -v chromium-browser &> /dev/null; then
    CHROME_CMD="chromium-browser"  
elif command -v chrome &> /dev/null; then
    CHROME_CMD="chrome"
else
    echo "❌ Chrome not found. Please install Google Chrome or Chromium."
    exit 1
fi

echo "✅ Found Chrome: $CHROME_CMD"
echo "🚀 Launching with development settings..."

# Launch Chrome with development settings
$CHROME_CMD \
    --disable-web-security \
    --user-data-dir="$TEMP_DIR" \
    --allow-running-insecure-content \
    --disable-features=VizDisplayCompositor \
    --ignore-certificate-errors \
    --ignore-ssl-errors \
    --allow-insecure-localhost \
    http://localhost:3000 &

echo "✅ Chrome launched for FlipSync development"
echo "📱 Navigate to: http://localhost:3000"
echo "🔧 Development mode: CORS disabled, insecure content allowed"
echo ""
echo "⚠️  WARNING: Only use this for development. Do not browse other sites."
