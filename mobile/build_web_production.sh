#!/bin/bash

# FlipSync Flutter Web Production Build Script
# ============================================
# Builds the Flutter web application for production deployment with eBay showcase requirements

set -e

echo "🚀 Building FlipSync Flutter Web Application for Production..."
echo "📅 $(date)"
echo ""

# Check if we're in the mobile directory
if [ ! -f "pubspec.yaml" ]; then
    echo "❌ Error: pubspec.yaml not found. Please run this script from the mobile directory."
    exit 1
fi

# Check Flutter installation
if ! command -v flutter &> /dev/null; then
    echo "❌ Error: Flutter is not installed or not in PATH."
    exit 1
fi

echo "📋 Flutter Version Information:"
flutter --version
echo ""

# Clean previous builds
echo "🧹 Cleaning previous builds..."
flutter clean
echo "✅ Clean completed"
echo ""

# Get dependencies
echo "📦 Getting Flutter dependencies..."
flutter pub get
echo "✅ Dependencies updated"
echo ""

# Configure build environment for HTTPS backend
echo "🔧 Configuring build environment for HTTPS backend..."

# Create build-time configuration - STANDARDIZED for DigitalOcean Droplet
cat > lib/config/build_config.dart << 'EOF'
// Build-time configuration for FlipSync web application - DigitalOcean Droplet
class BuildConfig {
  static const String environment = String.fromEnvironment('ENVIRONMENT', defaultValue: 'production');
  static const String apiBaseUrl = String.fromEnvironment('API_BASE_URL', defaultValue: 'http://174.138.77.110:8000');
  static const String websocketUrl = String.fromEnvironment('WEBSOCKET_URL', defaultValue: 'ws://174.138.77.110:8000/ws/flipsync');
  static const String baseUrl = String.fromEnvironment('BASE_URL', defaultValue: 'http://174.138.77.110:8000');

  // eBay Configuration - STANDARDIZED for DigitalOcean Droplet
  static const String ebayCallbackUrl = String.fromEnvironment('EBAY_CALLBACK_URL', defaultValue: 'http://174.138.77.110:8000/api/v1/marketplace/ebay/oauth/callback');
  static const bool ebayOAuthEnabled = bool.fromEnvironment('EBAY_OAUTH_ENABLED', defaultValue: true);

  // Security Configuration - HTTP for DigitalOcean Droplet (no SSL setup yet)
  static const bool sslEnabled = bool.fromEnvironment('SSL_ENABLED', defaultValue: false);
  static const bool httpsRedirect = bool.fromEnvironment('HTTPS_REDIRECT', defaultValue: false);

  // Feature Flags
  static const bool enableAnalytics = bool.fromEnvironment('ENABLE_ANALYTICS', defaultValue: true);
  static const bool debugMode = bool.fromEnvironment('DEBUG_MODE', defaultValue: false);

  // Performance Configuration
  static const bool cacheEnabled = bool.fromEnvironment('CACHE_ENABLED', defaultValue: true);
  static const int apiTimeout = int.fromEnvironment('API_TIMEOUT', defaultValue: 30000);
}
EOF

echo "✅ Build configuration created"
echo ""

# Build for production with optimizations
echo "🔨 Building Flutter web application for production..."
echo "   Target: Web (JavaScript + WASM support)"
echo "   Mode: Release (optimized)"
echo "   Features: Tree-shaking enabled, minification enabled"
echo ""

# Build command for Flutter 3.32.6 - STANDARDIZED for DigitalOcean Droplet
flutter build web \
  --release \
  --tree-shake-icons \
  --dart-define=ENVIRONMENT=production \
  --dart-define=API_BASE_URL=https://flipsyncai.com/api/v1 \
  --dart-define=WEBSOCKET_URL=wss://flipsyncai.com/ws/flipsync \
  --dart-define=BASE_URL=https://flipsyncai.com \
  --dart-define=EBAY_CALLBACK_URL=https://flipsyncai.com/api/v1/marketplace/ebay/oauth/callback \
  --dart-define=EBAY_OAUTH_ENABLED=true \
  --dart-define=SSL_ENABLED=true \
  --dart-define=HTTPS_REDIRECT=true \
  --dart-define=ENABLE_ANALYTICS=true \
  --dart-define=DEBUG_MODE=false \
  --dart-define=CACHE_ENABLED=true \
  --dart-define=API_TIMEOUT=30000 \
  --base-href="/" \
  --build-name="1.0.0" \
  --build-number=1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Flutter web build completed successfully!"
    echo ""
    
    # Display build information
    echo "📊 Build Information:"
    echo "   Build Directory: build/web/"
    echo "   Main Files:"
    ls -la build/web/ | head -10
    echo ""
    
    # Check build size
    if [ -d "build/web" ]; then
        BUILD_SIZE=$(du -sh build/web | cut -f1)
        echo "   Build Size: $BUILD_SIZE"
        echo ""
    fi
    
    # Verify critical files exist
    echo "🔍 Verifying build output..."
    
    CRITICAL_FILES=(
        "build/web/index.html"
        "build/web/main.dart.js"
        "build/web/flutter_service_worker.js"
        "build/web/manifest.json"
    )
    
    ALL_FILES_EXIST=true
    for file in "${CRITICAL_FILES[@]}"; do
        if [ -f "$file" ]; then
            echo "   ✅ $file"
        else
            echo "   ❌ $file (missing)"
            ALL_FILES_EXIST=false
        fi
    done
    
    echo ""
    
    if [ "$ALL_FILES_EXIST" = true ]; then
        echo "🎉 Build verification successful!"
        echo ""
        echo "📍 Deployment Information:"
        echo "   Build Output: build/web/"
        echo "   Entry Point: build/web/index.html"
        echo "   Backend URL: http://174.138.77.110:8000"
        echo "   WebSocket URL: ws://174.138.77.110:8000/ws/flipsync"
        echo "   eBay OAuth URL: http://174.138.77.110:8000/api/v1/marketplace/ebay/oauth/callback"
        echo ""
        echo "🚀 Ready for deployment!"
        echo ""
        echo "📋 Next Steps:"
        echo "   1. Deploy to production: ../deploy_flutter_frontend.sh"
        echo "   2. Check deployment status: ../deploy_flutter_frontend.sh status"
        echo "   3. Access frontend: http://174.138.77.110:3000"
        echo ""
    else
        echo "❌ Build verification failed - some critical files are missing"
        exit 1
    fi
    
else
    echo ""
    echo "❌ Flutter web build failed!"
    echo "Please check the error messages above and resolve any issues."
    exit 1
fi
