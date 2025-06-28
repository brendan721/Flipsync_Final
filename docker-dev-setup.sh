#!/bin/bash

# FlipSync Docker Development Environment Setup
# This script sets up the complete Docker development environment

set -e

echo "🐳 FlipSync Docker Development Environment Setup"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    print_error "Docker is not running. Please start Docker and try again."
    exit 1
fi

print_status "Docker is running"

# Check if Docker Compose is available
if ! command -v docker-compose > /dev/null 2>&1; then
    print_error "Docker Compose is not installed. Please install Docker Compose and try again."
    exit 1
fi

print_status "Docker Compose is available"

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p logs uploads scripts

# Set up environment file
if [ ! -f .env ]; then
    print_info "Creating .env file from PostgreSQL template..."
    cp .env.postgresql .env
    print_status ".env file created"
else
    print_warning ".env file already exists, skipping creation"
fi

# Stop any existing containers
print_info "Stopping any existing FlipSync containers..."
docker-compose -f docker-compose.development.yml down --remove-orphans 2>/dev/null || true

# Pull latest images
print_info "Pulling latest Docker images..."
docker-compose -f docker-compose.development.yml pull

# Build FlipSync API image
print_info "Building FlipSync API image..."
docker-compose -f docker-compose.development.yml build flipsync-api

# Start infrastructure services first
print_info "Starting infrastructure services (PostgreSQL, Redis)..."
docker-compose -f docker-compose.development.yml up -d postgres redis

# Wait for database to be ready
print_info "Waiting for PostgreSQL to be ready..."
timeout=60
counter=0
while ! docker exec flipsync-dev-postgres pg_isready -U postgres -d flipsync > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        print_error "PostgreSQL failed to start within $timeout seconds"
        exit 1
    fi
    sleep 1
    counter=$((counter + 1))
done

print_status "PostgreSQL is ready"

# Wait for Redis to be ready
print_info "Waiting for Redis to be ready..."
timeout=30
counter=0
while ! docker exec flipsync-dev-redis redis-cli ping > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        print_error "Redis failed to start within $timeout seconds"
        exit 1
    fi
    sleep 1
    counter=$((counter + 1))
done

print_status "Redis is ready"

# Start application services
print_info "Starting FlipSync API service..."
docker-compose -f docker-compose.development.yml up -d flipsync-api

# Start management UIs
print_info "Starting management UIs..."
docker-compose -f docker-compose.development.yml up -d adminer redis-commander

# Wait for API to be ready
print_info "Waiting for FlipSync API to be ready..."
timeout=120
counter=0
while ! curl -f http://localhost:8000/health > /dev/null 2>&1; do
    if [ $counter -ge $timeout ]; then
        print_warning "FlipSync API health check failed, but continuing..."
        break
    fi
    sleep 2
    counter=$((counter + 2))
done

# Show status
echo ""
echo "🎉 FlipSync Docker Development Environment Setup Complete!"
echo "=========================================================="
echo ""
echo "📊 Service Status:"
docker-compose -f docker-compose.development.yml ps

echo ""
echo "🔗 Access URLs:"
echo "  • FlipSync API:        http://localhost:8000"
echo "  • API Health Check:    http://localhost:8000/health"
echo "  • API Documentation:   http://localhost:8000/docs"
echo "  • Database Admin:      http://localhost:8080"
echo "  • Redis Commander:     http://localhost:8081"
echo ""
echo "🗄️  Database Connection:"
echo "  • Host: localhost"
echo "  • Port: 5432"
echo "  • Database: flipsync"
echo "  • Username: postgres"
echo "  • Password: postgres"
echo ""
echo "📝 Useful Commands:"
echo "  • View logs:           docker-compose -f docker-compose.development.yml logs -f"
echo "  • Stop services:       docker-compose -f docker-compose.development.yml down"
echo "  • Restart API:         docker-compose -f docker-compose.development.yml restart flipsync-api"
echo "  • Database shell:      docker exec -it flipsync-dev-postgres psql -U postgres -d flipsync"
echo "  • Redis shell:         docker exec -it flipsync-dev-redis redis-cli"
echo ""
echo "🚀 Your FlipSync development environment is ready!"

# Test database connection
print_info "Testing database connection..."
if docker exec flipsync-dev-postgres psql -U postgres -d flipsync -c "SELECT 'Database connection successful' AS status;" > /dev/null 2>&1; then
    print_status "Database connection test successful"
else
    print_warning "Database connection test failed, but services are running"
fi

echo ""
print_status "Setup completed successfully!"
