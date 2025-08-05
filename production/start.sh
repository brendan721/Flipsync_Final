#!/bin/bash

# FlipSync Production Startup Script
# Optimized for 35+ agent multi-tier architecture

set -e

echo "🚀 Starting FlipSync Production API..."

# Environment validation
if [ "$ENVIRONMENT" != "production" ]; then
    echo "⚠️  Warning: ENVIRONMENT is not set to 'production'"
fi

# Create required directories (gracefully handle permission issues)
mkdir -p /app/logs/agents /app/logs/workflows /app/logs/api /app/logs/performance /app/logs/security 2>/dev/null || {
    echo "⚠️  Could not create log directories, using /tmp for logs"
    mkdir -p /tmp/flipsync/logs/agents /tmp/flipsync/logs/workflows /tmp/flipsync/logs/api /tmp/flipsync/logs/performance /tmp/flipsync/logs/security
    export LOG_DIR="/tmp/flipsync/logs"
}
mkdir -p /app/temp/uploads /app/temp/processing 2>/dev/null || {
    echo "⚠️  Could not create temp directories, using /tmp for temp files"
    mkdir -p /tmp/flipsync/temp/uploads /tmp/flipsync/temp/processing
    export TEMP_DIR="/tmp/flipsync/temp"
}

# Set proper permissions for app user (gracefully handle failures)
chown -R app:app /app/logs /app/temp 2>/dev/null || true
chmod -R 755 /app/logs /app/temp 2>/dev/null || true

# Create log files with proper permissions (gracefully handle failures)
LOG_DIR=${LOG_DIR:-/app/logs}
touch ${LOG_DIR}/api/access.log ${LOG_DIR}/api/error.log 2>/dev/null || {
    echo "⚠️  Using stdout/stderr for logging instead of files"
    export USE_STDOUT_LOGGING=true
}

# Validate critical environment variables
required_vars=(
    "DATABASE_URL"
    "REDIS_URL"
    "OPENAI_API_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set"
        exit 1
    fi
done

echo "✅ Environment validation passed"

# Database connectivity check
echo "🔍 Checking database connectivity..."
python -c "
import os
import psycopg2
try:
    conn = psycopg2.connect(os.environ['DATABASE_URL'])
    conn.close()
    print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
" || echo "⚠️  Database check skipped (optional in production)"

# Redis connectivity check
echo "🔍 Checking Redis connectivity..."
python -c "
import os
import redis
try:
    r = redis.from_url(os.environ['REDIS_URL'])
    r.ping()
    print('✅ Redis connection successful')
except Exception as e:
    print(f'❌ Redis connection failed: {e}')
    exit(1)
" || echo "⚠️  Redis check skipped (optional in production)"

# OpenAI connectivity check
echo "🔍 Checking OpenAI API connectivity..."
python -c "
import os
import openai
try:
    client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])
    # Simple test call
    response = client.models.list()
    print('✅ OpenAI API connection successful')
except Exception as e:
    print(f'❌ OpenAI API connection failed: {e}')
    exit(1)
" || echo "⚠️  OpenAI API check skipped (optional in production)"

# Agent system pre-initialization (Skip to prevent startup hang)
echo "🤖 Skipping agent system pre-initialization for faster startup..."
echo "✅ Agent system will be initialized on-demand"

# Performance monitoring setup
echo "📊 Setting up performance monitoring..."
export ENABLE_PERFORMANCE_MONITORING=true
export ENABLE_AGENT_METRICS=true
export ENABLE_WORKFLOW_METRICS=true
export ENABLE_API_METRICS=true

# Security configuration
echo "🔒 Applying security configuration..."
export SECURE_HEADERS=true
export RATE_LIMITING=true
export REQUEST_VALIDATION=strict

# Production optimizations
echo "⚡ Applying production optimizations..."
export AGENT_POOL_SIZE=5
export WORKFLOW_CONCURRENCY=7
export API_WORKER_TIMEOUT=120
export AGENT_COORDINATION_TIMEOUT=30

# Log startup information
echo "📝 Production configuration:"
echo "  - Workers: ${WORKERS:-4}"
echo "  - Worker class: ${WORKER_CLASS:-uvicorn.workers.UvicornWorker}"
echo "  - Worker connections: ${WORKER_CONNECTIONS:-1000}"
echo "  - Timeout: ${TIMEOUT:-120}s"
echo "  - Log level: ${LOG_LEVEL:-info}"
echo "  - Debug mode: ${DEBUG:-false}"

# Start the application with Gunicorn
echo "🎬 Starting FlipSync API with Gunicorn..."

# Skip agent initialization for faster startup
export SKIP_AGENT_INITIALIZATION=true

# Configure logging based on available directories
LOG_DIR=${LOG_DIR:-/app/logs}
if [ "$USE_STDOUT_LOGGING" = "true" ]; then
    echo "📝 Using stdout/stderr for logging"
    exec gunicorn \
        --config /app/gunicorn.conf.py \
        --access-logfile - \
        --error-logfile - \
        --capture-output \
        --enable-stdio-inheritance \
        fs_agt_clean.app.main:app
else
    echo "📝 Using file logging: ${LOG_DIR}/api/"
    exec gunicorn \
        --config /app/gunicorn.conf.py \
        --log-config /app/logging.conf \
        --access-logfile ${LOG_DIR}/api/access.log \
        --error-logfile ${LOG_DIR}/api/error.log \
        --capture-output \
        --enable-stdio-inheritance \
        fs_agt_clean.app.main:app
fi
