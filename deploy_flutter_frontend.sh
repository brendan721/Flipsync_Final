#!/bin/bash

# FlipSync Flutter Frontend Deployment Script
# ============================================
# Single source of truth for building and deploying Flutter web frontend

set -e

# Configuration
DROPLET_IP="174.138.77.110"
DROPLET_USER="root"
PRODUCTION_PATH="/opt/flipsync"
LOCAL_MOBILE_DIR="mobile"
REMOTE_MOBILE_DIR="$PRODUCTION_PATH/mobile"
REMOTE_WEB_DIR="/var/www/flipsyncai.com"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
    exit 1
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Function to run SSH commands
run_ssh() {
    ssh -o StrictHostKeyChecking=no ${DROPLET_USER}@${DROPLET_IP} "$1"
}

# Function to check SSH connectivity
check_ssh() {
    log "Checking SSH connectivity to droplet..."
    if ! run_ssh "echo 'SSH connection successful'"; then
        error "SSH connection failed to ${DROPLET_IP}"
    fi
    success "SSH connection verified"
}

# Function to build Flutter web locally
build_flutter_local() {
    log "Building Flutter web application locally..."
    
    if [ ! -d "$LOCAL_MOBILE_DIR" ]; then
        error "Mobile directory not found: $LOCAL_MOBILE_DIR"
    fi
    
    cd "$LOCAL_MOBILE_DIR"
    
    # Check if pubspec.yaml exists
    if [ ! -f "pubspec.yaml" ]; then
        error "pubspec.yaml not found in $LOCAL_MOBILE_DIR"
    fi
    
    # Clean previous builds
    log "Cleaning previous builds..."
    flutter clean
    
    # Get dependencies
    log "Getting Flutter dependencies..."
    flutter pub get
    
    # Generate current build timestamp
    BUILD_TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
    log "Building Flutter web for production with timestamp: $BUILD_TIMESTAMP"

    # Build for production
    # NOTE: API_BASE_URL is NOT specified here to use the corrected value from assets/config/env.production
    # This prevents API path duplication (e.g., /api/v1/api/v1/endpoint)
    flutter build web \
      --release \
      --tree-shake-icons \
      --dart-define=ENVIRONMENT=production \
      --dart-define=WEBSOCKET_URL=wss://www.flipsyncai.com/ws/flipsync \
      --dart-define=BASE_URL=https://www.flipsyncai.com \
      --dart-define=EBAY_CALLBACK_URL=https://www.flipsyncai.com/api/v1/marketplace/ebay/oauth/callback \
      --dart-define=EBAY_OAUTH_ENABLED=true \
      --dart-define=SSL_ENABLED=true \
      --dart-define=HTTPS_REDIRECT=true \
      --dart-define=ENABLE_ANALYTICS=true \
      --dart-define=DEBUG_MODE=false \
      --dart-define=CACHE_ENABLED=true \
      --dart-define=API_TIMEOUT=30000 \
      --dart-define=BUILD_TIMESTAMP="$BUILD_TIMESTAMP" \
      --base-href="/" \
      --build-name="1.0.2" \
      --build-number=3
    
    # Verify build
    if [ ! -d "build/web" ]; then
        error "Flutter build failed - build/web directory not found"
    fi
    
    # Check critical files
    CRITICAL_FILES=("build/web/index.html" "build/web/main.dart.js" "build/web/flutter_service_worker.js")
    for file in "${CRITICAL_FILES[@]}"; do
        if [ ! -f "$file" ]; then
            error "Critical file missing: $file"
        fi
    done
    
    # Verify build configuration
    log "Verifying build configuration..."
    if grep -q "API BASE URL: https://flipsyncai.com/api/v1" build/web/main.dart.js; then
        error "Build contains incorrect API base URL (with /api/v1 suffix) - this will cause path duplication"
    fi

    if grep -q "BUILD TIMESTAMP: $BUILD_TIMESTAMP" build/web/main.dart.js; then
        success "Build timestamp verified in compiled output"
    else
        warning "Build timestamp not found in compiled output"
    fi

    # Generate build ID
    BUILD_ID=$(find build/web -type f -exec md5sum {} \; | sort | md5sum | cut -d' ' -f1)
    echo "$BUILD_ID" > build/web/.last_build_id

    success "Flutter build completed successfully (Build ID: $BUILD_ID)"

    cd ..
}

# Function to deploy to droplet
deploy_to_droplet() {
    log "Deploying Flutter build to droplet..."
    
    # Create backup of current web directory
    BACKUP_DIR="web_backup_$(date +%s)"
    log "Creating backup of current web directory..."
    run_ssh "cd $PRODUCTION_PATH && cp -r $REMOTE_WEB_DIR $BACKUP_DIR" || warning "Backup failed or web directory doesn't exist"
    
    # Transfer build files
    log "Transferring build files to droplet..."
    rsync -avz --progress --delete \
          ${LOCAL_MOBILE_DIR}/build/web/ \
          ${DROPLET_USER}@${DROPLET_IP}:${REMOTE_WEB_DIR}/
    
    # Verify deployment
    log "Verifying deployment..."
    REMOTE_BUILD_ID=$(run_ssh "cat $REMOTE_WEB_DIR/.last_build_id 2>/dev/null || echo 'unknown'")
    LOCAL_BUILD_ID=$(cat ${LOCAL_MOBILE_DIR}/build/web/.last_build_id)
    
    if [ "$REMOTE_BUILD_ID" = "$LOCAL_BUILD_ID" ]; then
        success "Deployment verified - Build IDs match: $LOCAL_BUILD_ID"
    else
        error "Deployment verification failed - Build ID mismatch (Local: $LOCAL_BUILD_ID, Remote: $REMOTE_BUILD_ID)"
    fi
    
    # Test frontend accessibility
    log "Testing frontend accessibility..."
    if curl -f -s https://flipsyncai.com > /dev/null; then
        success "Frontend is accessible at https://flipsyncai.com"
    else
        error "Frontend is not accessible at https://flipsyncai.com"
    fi

    # Verify deployed build configuration
    log "Verifying deployed build configuration..."
    DEPLOYED_TIMESTAMP=$(curl -s https://flipsyncai.com/main.dart.js | grep -o "BUILD TIMESTAMP: [^\"]*" | head -1)
    if [ "$DEPLOYED_TIMESTAMP" = "BUILD TIMESTAMP: $BUILD_TIMESTAMP" ]; then
        success "Deployed build timestamp matches: $BUILD_TIMESTAMP"
    else
        warning "Deployed build timestamp mismatch. Expected: $BUILD_TIMESTAMP, Got: $DEPLOYED_TIMESTAMP"
    fi

    # Check for API path duplication in deployed build
    if curl -s https://flipsyncai.com/main.dart.js | grep -q "API BASE URL: https://flipsyncai.com/api/v1"; then
        error "Deployed build still contains incorrect API base URL - path duplication will occur"
    else
        success "Deployed build has correct API base URL configuration"
    fi

    success "Deployment completed successfully"
    log "Backup available at: $PRODUCTION_PATH/$BACKUP_DIR"
}

# Function to show deployment status
show_status() {
    log "Deployment Status:"
    echo "=================="
    
    # Local build info
    if [ -f "${LOCAL_MOBILE_DIR}/build/web/.last_build_id" ]; then
        LOCAL_BUILD_ID=$(cat ${LOCAL_MOBILE_DIR}/build/web/.last_build_id)
        echo "Local Build ID:  $LOCAL_BUILD_ID"
    else
        echo "Local Build ID:  Not found"
    fi
    
    # Remote build info
    REMOTE_BUILD_ID=$(run_ssh "cat $REMOTE_WEB_DIR/.last_build_id 2>/dev/null || echo 'Not found'")
    echo "Remote Build ID: $REMOTE_BUILD_ID"
    
    # Frontend status
    if curl -f -s https://flipsyncai.com > /dev/null; then
        echo "Frontend Status: ✅ Accessible"
    else
        echo "Frontend Status: ❌ Not accessible"
    fi

    echo "Frontend URL:    https://flipsyncai.com"
    echo "Backend URL:     https://flipsyncai.com/api/v1"
}

# Main execution
main() {
    echo "🚀 FlipSync Flutter Frontend Deployment"
    echo "========================================"
    
    case "${1:-deploy}" in
        "build")
            build_flutter_local
            ;;
        "deploy")
            check_ssh
            build_flutter_local
            deploy_to_droplet
            show_status
            ;;
        "status")
            check_ssh
            show_status
            ;;
        "help")
            echo "Usage: $0 [build|deploy|status|help]"
            echo "  build  - Build Flutter web locally only"
            echo "  deploy - Build and deploy to droplet (default)"
            echo "  status - Show deployment status"
            echo "  help   - Show this help message"
            ;;
        *)
            error "Unknown command: $1. Use 'help' for usage information."
            ;;
    esac
}

# Run main function with all arguments
main "$@"
