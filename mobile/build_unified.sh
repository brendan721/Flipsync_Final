#!/bin/bash

# FlipSync Unified Build Script
# =============================
# Single build script for all environments using unified configuration
# Replaces multiple redundant build scripts with environment-aware approach

set -e

# Default values
ENVIRONMENT="development"
SKIP_VALIDATION=false
VERBOSE=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case $1 in
    -e|--environment)
      ENVIRONMENT="$2"
      shift 2
      ;;
    --skip-validation)
      SKIP_VALIDATION=true
      shift
      ;;
    -v|--verbose)
      VERBOSE=true
      shift
      ;;
    -h|--help)
      echo "FlipSync Unified Build Script"
      echo ""
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  -e, --environment ENV    Set environment (development|staging|production)"
      echo "  --skip-validation        Skip credential validation"
      echo "  -v, --verbose           Enable verbose output"
      echo "  -h, --help              Show this help message"
      echo ""
      echo "Examples:"
      echo "  $0                                    # Development build"
      echo "  $0 -e production                     # Production build"
      echo "  $0 -e production --skip-validation   # Production build without validation"
      echo ""
      exit 0
      ;;
    *)
      echo "Unknown option: $1"
      echo "Use -h or --help for usage information"
      exit 1
      ;;
  esac
done

echo "🚀 FlipSync Unified Build Script"
echo "================================"
echo "Environment: $ENVIRONMENT"
echo "Date: $(date)"
echo ""

# Validate environment
case $ENVIRONMENT in
  development|staging|production)
    ;;
  *)
    echo "❌ Error: Invalid environment '$ENVIRONMENT'"
    echo "   Valid environments: development, staging, production"
    exit 1
    ;;
esac

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

if [ "$VERBOSE" = true ]; then
    echo "📋 Flutter Version Information:"
    flutter --version
    echo ""
fi

# Environment-specific configuration
case $ENVIRONMENT in
  production)
    API_BASE_URL="${API_BASE_URL:-https://flipsyncai.com}"
    BASE_URL="${BASE_URL:-https://flipsyncai.com}"
    WEBSOCKET_URL="${WEBSOCKET_URL:-wss://flipsyncai.com/ws/flipsync}"
    SSL_ENABLED="${SSL_ENABLED:-true}"
    DEBUG_MODE="${DEBUG_MODE:-false}"
    ENABLE_ANALYTICS="${ENABLE_ANALYTICS:-true}"
    
    # Production credential validation
    if [ "$SKIP_VALIDATION" = false ]; then
      echo "🔍 Validating production credentials..."
      REQUIRED_VARS=(
        "EBAY_APP_ID"
        "EBAY_DEV_ID" 
        "EBAY_CERT_ID"
        "EBAY_RU_NAME"
        "AUTH_SECRET"
      )
      
      MISSING_VARS=()
      for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ]; then
          MISSING_VARS+=("$var")
        fi
      done
      
      if [ ${#MISSING_VARS[@]} -gt 0 ]; then
        echo "❌ Error: Missing required production credentials:"
        for var in "${MISSING_VARS[@]}"; do
          echo "   - $var"
        done
        echo ""
        echo "Set credentials via environment variables or use --skip-validation for testing"
        echo "Example: export EBAY_APP_ID='your_app_id'"
        exit 1
      fi
      
      echo "✅ All required credentials are set"
    fi
    ;;
    
  staging)
    API_BASE_URL="${API_BASE_URL:-https://staging.flipsyncai.com}"
    BASE_URL="${BASE_URL:-https://staging.flipsyncai.com}"
    WEBSOCKET_URL="${WEBSOCKET_URL:-wss://staging.flipsyncai.com/ws/flipsync}"
    SSL_ENABLED="${SSL_ENABLED:-true}"
    DEBUG_MODE="${DEBUG_MODE:-true}"
    ENABLE_ANALYTICS="${ENABLE_ANALYTICS:-false}"
    ;;
    
  development)
    API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
    BASE_URL="${BASE_URL:-http://localhost:8000}"
    WEBSOCKET_URL="${WEBSOCKET_URL:-ws://localhost:8000/ws/flipsync}"
    SSL_ENABLED="${SSL_ENABLED:-false}"
    DEBUG_MODE="${DEBUG_MODE:-true}"
    ENABLE_ANALYTICS="${ENABLE_ANALYTICS:-false}"
    ;;
esac

# Validate backend connectivity (optional)
if [ "$ENVIRONMENT" != "development" ] && [ "$SKIP_VALIDATION" = false ]; then
  echo "🔍 Validating backend connectivity..."
  BACKEND_CHECK_URL="${BASE_URL}/api/v1/health"
  if curl -s --connect-timeout 5 "$BACKEND_CHECK_URL" > /dev/null 2>&1; then
    echo "✅ Backend is accessible at $BASE_URL"
  else
    echo "⚠️  Warning: Backend may not be accessible at $BASE_URL"
    echo "   Continuing with build - ensure backend is running before deployment"
  fi
fi

echo ""
echo "🏗️  Building FlipSync for $ENVIRONMENT environment..."
echo "   API Base URL: $API_BASE_URL"
echo "   WebSocket URL: $WEBSOCKET_URL"
echo "   SSL Enabled: $SSL_ENABLED"
echo "   Debug Mode: $DEBUG_MODE"
echo ""

# Clean previous builds
echo "🧹 Cleaning previous builds..."
flutter clean > /dev/null 2>&1
flutter pub get > /dev/null 2>&1
echo "✅ Clean completed"

# Build with unified configuration
echo "🔨 Building Flutter web application..."

# Common dart-define flags
DART_DEFINES=(
  "--dart-define=ENVIRONMENT=$ENVIRONMENT"
  "--dart-define=API_BASE_URL=$API_BASE_URL"
  "--dart-define=BASE_URL=$BASE_URL"
  "--dart-define=WEBSOCKET_URL=$WEBSOCKET_URL"
  "--dart-define=SSL_ENABLED=$SSL_ENABLED"
  "--dart-define=DEBUG_MODE=$DEBUG_MODE"
  "--dart-define=ENABLE_ANALYTICS=$ENABLE_ANALYTICS"
  "--dart-define=ENHANCED_PRODUCT_CREATION_ENABLED=true"
  "--dart-define=SHIPPING_ARBITRAGE_ENABLED=true"
  "--dart-define=EXTERNAL_ADVERTISING_ENABLED=true"
  "--dart-define=REALTIME_WEBSOCKET_ENABLED=true"
)

# Add credentials if available (for production)
if [ -n "$EBAY_APP_ID" ]; then
  DART_DEFINES+=("--dart-define=EBAY_APP_ID=$EBAY_APP_ID")
fi
if [ -n "$EBAY_DEV_ID" ]; then
  DART_DEFINES+=("--dart-define=EBAY_DEV_ID=$EBAY_DEV_ID")
fi
if [ -n "$EBAY_CERT_ID" ]; then
  DART_DEFINES+=("--dart-define=EBAY_CERT_ID=$EBAY_CERT_ID")
fi
if [ -n "$EBAY_RU_NAME" ]; then
  DART_DEFINES+=("--dart-define=EBAY_RU_NAME=$EBAY_RU_NAME")
fi
if [ -n "$AUTH_SECRET" ]; then
  DART_DEFINES+=("--dart-define=AUTH_SECRET=$AUTH_SECRET")
fi

# Execute build
flutter build web \
  --release \
  --tree-shake-icons \
  "${DART_DEFINES[@]}" \
  --base-href="/" \
  --build-name="3.0.0" \
  --build-number=300

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ FlipSync build completed successfully!"
    echo ""
    
    # Display build information
    echo "📊 Build Information:"
    echo "   Environment: $ENVIRONMENT"
    echo "   Build Directory: build/web/"
    echo "   Version: 3.0.0"
    echo "   API URL: $API_BASE_URL"
    echo "   WebSocket URL: $WEBSOCKET_URL"
    
    if [ -d "build/web" ]; then
        BUILD_SIZE=$(du -sh build/web 2>/dev/null | cut -f1 || echo "Unknown")
        echo "   Build Size: $BUILD_SIZE"
    fi
    
    echo ""
    echo "🎯 Build ready for $ENVIRONMENT deployment!"
    
else
    echo ""
    echo "❌ FlipSync build failed!"
    echo "Please check the error messages above and resolve any issues."
    exit 1
fi
