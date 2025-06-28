#!/bin/bash

# FlipSync Production Deployment Script
# Fixes Docker networking issues and deploys with proper configuration

set -e

echo "🚀 FlipSync Production Deployment Script"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker-compose &> /dev/null; then
    print_error "docker-compose is not installed. Please install it and try again."
    exit 1
fi

print_status "Checking environment configuration..."

# Check if .env.production exists
if [ ! -f ".env.production" ]; then
    print_warning ".env.production not found. Creating from template..."
    cp .env.production.template .env.production
    print_warning "Please edit .env.production and replace all CHANGE_ME_ values with actual secrets."
    print_warning "Then run this script again."
    exit 1
fi

# Validate critical environment variables
print_status "Validating environment variables..."

# Source the environment file
set -a
source .env.production
set +a

# Check critical variables
MISSING_VARS=()

if [ -z "$OPENAI_API_KEY" ] || [ "$OPENAI_API_KEY" = "CHANGE_ME_YOUR_OPENAI_API_KEY_HERE" ]; then
    MISSING_VARS+=("OPENAI_API_KEY")
fi

if [ -z "$EBAY_CLIENT_SECRET" ] || [ "$EBAY_CLIENT_SECRET" = "CHANGE_ME_YOUR_EBAY_CLIENT_SECRET_HERE" ]; then
    MISSING_VARS+=("EBAY_CLIENT_SECRET")
fi

if [ -z "$JWT_SECRET" ] || [ "$JWT_SECRET" = "CHANGE_ME_GENERATE_SECURE_JWT_SECRET_HERE" ]; then
    MISSING_VARS+=("JWT_SECRET")
fi

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    print_error "Missing or placeholder values for critical environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        print_error "  - $var"
    done
    print_error "Please update .env.production with actual values."
    exit 1
fi

print_success "Environment validation passed"

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down 2>/dev/null || true
docker-compose -f docker-compose.flipsync-app.yml down 2>/dev/null || true
docker-compose -f docker-compose.infrastructure.yml down 2>/dev/null || true

# Clean up old networks if they exist
print_status "Cleaning up old networks..."
docker network rm flipsync_final_default 2>/dev/null || true

# Build the production image
print_status "Building production Docker image..."
docker-compose -f docker-compose.production.yml build --no-cache

# Start the production environment
print_status "Starting production environment..."
docker-compose -f docker-compose.production.yml --env-file .env.production up -d

# Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 30

# Check service health
print_status "Checking service health..."

# Check database
if docker-compose -f docker-compose.production.yml exec -T db pg_isready -U postgres > /dev/null 2>&1; then
    print_success "Database is healthy"
else
    print_error "Database is not healthy"
fi

# Check Redis
if docker-compose -f docker-compose.production.yml exec -T redis redis-cli --no-auth-warning -a "$REDIS_PASSWORD" ping > /dev/null 2>&1; then
    print_success "Redis is healthy"
else
    print_error "Redis is not healthy"
fi

# Check API
sleep 10
if curl -f http://localhost:8001/health > /dev/null 2>&1; then
    print_success "API is healthy"
else
    print_warning "API health check failed - checking logs..."
    docker-compose -f docker-compose.production.yml logs api --tail 20
fi

# Display final status
echo ""
echo "=========================================="
print_success "FlipSync Production Deployment Complete!"
echo "=========================================="
echo ""
print_status "Services running:"
print_status "  - API: http://localhost:8001"
print_status "  - Database: localhost:5432"
print_status "  - Redis: localhost:6379"
print_status "  - Qdrant: localhost:6333"
echo ""
print_status "To view logs: docker-compose -f docker-compose.production.yml logs -f"
print_status "To stop: docker-compose -f docker-compose.production.yml down"
echo ""

# Show container status
print_status "Container status:"
docker-compose -f docker-compose.production.yml ps
