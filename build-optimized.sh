#!/bin/bash

# FlipSync Optimized Build Script
# Provides fast development workflows and reliable production builds

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show usage
show_usage() {
    echo "FlipSync Optimized Build Script"
    echo ""
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  dev-start       Start development environment with hot reload"
    echo "  dev-rebuild     Rebuild development image (dependencies only)"
    echo "  dev-full        Full rebuild of development environment"
    echo "  prod-build      Build production image"
    echo "  prod-start      Start production environment"
    echo "  prod-deploy     Build and deploy production"
    echo "  clean           Clean up Docker resources"
    echo "  test-oauth      Test OAuth fix"
    echo ""
    echo "Options:"
    echo "  --no-cache      Force rebuild without cache"
    echo "  --verbose       Show detailed output"
    echo ""
    echo "Examples:"
    echo "  $0 dev-start                    # Start development with volume mounts"
    echo "  $0 dev-rebuild                  # Rebuild only if dependencies changed"
    echo "  $0 prod-deploy --no-cache       # Full production rebuild"
    echo "  $0 clean                        # Clean up all containers and images"
}

# Function to check if dependencies changed
dependencies_changed() {
    if [ ! -f .build-cache/requirements.hash ]; then
        return 0  # No cache, assume changed
    fi
    
    current_hash=$(sha256sum requirements.txt requirements-minimal.txt | sha256sum | cut -d' ' -f1)
    cached_hash=$(cat .build-cache/requirements.hash 2>/dev/null || echo "")
    
    if [ "$current_hash" != "$cached_hash" ]; then
        return 0  # Changed
    else
        return 1  # Not changed
    fi
}

# Function to update dependency cache
update_dependency_cache() {
    mkdir -p .build-cache
    sha256sum requirements.txt requirements-minimal.txt | sha256sum | cut -d' ' -f1 > .build-cache/requirements.hash
}

# Function to start development environment
dev_start() {
    print_status "Starting FlipSync development environment..."
    
    # Check if we need to rebuild dependencies
    if dependencies_changed; then
        print_warning "Dependencies changed, rebuilding..."
        docker-compose -f docker-compose.dev-optimized.yml build --target development api-dev
        update_dependency_cache
    else
        print_success "Dependencies unchanged, using cached build"
    fi
    
    # Start development services
    docker-compose -f docker-compose.dev-optimized.yml up -d api-dev db redis qdrant
    
    print_success "Development environment started!"
    print_status "API available at: http://localhost:8001"
    print_status "Code changes will be automatically reloaded"
    print_status "View logs with: docker-compose -f docker-compose.dev-optimized.yml logs -f api-dev"
}

# Function to rebuild development dependencies
dev_rebuild() {
    print_status "Rebuilding development dependencies..."
    
    if [ "$1" = "--no-cache" ]; then
        docker-compose -f docker-compose.dev-optimized.yml build --no-cache --target development api-dev
    else
        docker-compose -f docker-compose.dev-optimized.yml build --target development api-dev
    fi
    
    update_dependency_cache
    print_success "Development dependencies rebuilt!"
}

# Function for full development rebuild
dev_full() {
    print_status "Full development rebuild..."
    docker-compose -f docker-compose.dev-optimized.yml down
    docker-compose -f docker-compose.dev-optimized.yml build --no-cache api-dev
    update_dependency_cache
    docker-compose -f docker-compose.dev-optimized.yml up -d
    print_success "Full development rebuild complete!"
}

# Function to build production image
prod_build() {
    print_status "Building production image..."
    
    if [ "$1" = "--no-cache" ]; then
        docker build --no-cache -f Dockerfile.optimized --target production -t flipsync-production .
    else
        docker build -f Dockerfile.optimized --target production -t flipsync-production .
    fi
    
    print_success "Production image built!"
}

# Function to start production environment
prod_start() {
    print_status "Starting production environment..."
    docker-compose -f docker-compose.dev-optimized.yml --profile production up -d
    print_success "Production environment started at http://localhost:8002"
}

# Function to deploy production
prod_deploy() {
    print_status "Deploying production environment..."
    
    # Build production image
    prod_build "$1"
    
    # Start production services
    docker-compose -f docker-compose.production.yml up -d
    
    print_success "Production deployment complete!"
    print_status "API available at: http://localhost:8001"
}

# Function to clean up Docker resources
clean() {
    print_status "Cleaning up Docker resources..."
    
    # Stop all containers
    docker-compose -f docker-compose.dev-optimized.yml down 2>/dev/null || true
    docker-compose -f docker-compose.production.yml down 2>/dev/null || true
    
    # Remove FlipSync images
    docker images | grep flipsync | awk '{print $3}' | xargs docker rmi -f 2>/dev/null || true
    
    # Clean up build cache
    docker builder prune -f
    
    # Remove build cache directory
    rm -rf .build-cache
    
    print_success "Cleanup complete!"
}

# Function to test OAuth fix
test_oauth() {
    print_status "Testing OAuth fix..."
    
    # Check if API is running
    if ! curl -s http://localhost:8001/health > /dev/null; then
        print_error "API is not running. Start it first with: $0 dev-start"
        exit 1
    fi
    
    # Run OAuth test
    python test_oauth_fix.py
}

# Main script logic
case "$1" in
    "dev-start")
        dev_start
        ;;
    "dev-rebuild")
        dev_rebuild "$2"
        ;;
    "dev-full")
        dev_full
        ;;
    "prod-build")
        prod_build "$2"
        ;;
    "prod-start")
        prod_start
        ;;
    "prod-deploy")
        prod_deploy "$2"
        ;;
    "clean")
        clean
        ;;
    "test-oauth")
        test_oauth
        ;;
    "help"|"--help"|"-h"|"")
        show_usage
        ;;
    *)
        print_error "Unknown command: $1"
        show_usage
        exit 1
        ;;
esac
