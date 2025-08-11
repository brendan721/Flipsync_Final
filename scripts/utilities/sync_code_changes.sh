#!/bin/bash

# FlipSync Code Sync Script
# Syncs only code changes to production droplet (excludes venv)

set -e

# Configuration
DROPLET_IP="192.168.110.71"
DROPLET_USER="root"
REMOTE_DIR="/opt/flipsync"
LOCAL_DIR="/home/brend/Flipsync_Final"

echo "🚀 Syncing FlipSync code changes to production..."

# Check if we can connect to the droplet
echo "📡 Testing connection to droplet..."
if ! ssh -o ConnectTimeout=10 "$DROPLET_USER@$DROPLET_IP" "echo 'Connection successful'"; then
    echo "❌ Cannot connect to droplet. Please check your SSH configuration."
    exit 1
fi

echo "✅ Connection to droplet successful"

# Sync files using rsync (excluding unnecessary files)
echo "📦 Syncing code changes to production droplet..."
rsync -avz --progress \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache' \
    --exclude='node_modules' \
    --exclude='.env.local' \
    --exclude='*.log' \
    --exclude='*.db' \
    --exclude='testing-frontend/node_modules' \
    --exclude='flutter_frontend/build' \
    --exclude='flutter_frontend/.dart_tool' \
    --exclude='*.tar.gz' \
    --exclude='venv_agentic' \
    --exclude='venv_production' \
    --exclude='*.sqlite' \
    --exclude='*.sqlite3' \
    "$LOCAL_DIR/" "$DROPLET_USER@$DROPLET_IP:$REMOTE_DIR/"

echo "✅ Code sync completed"

# Restart the FlipSync service
echo "🔄 Restarting FlipSync service..."
ssh "$DROPLET_USER@$DROPLET_IP" "systemctl restart flipsync"

echo "⏳ Waiting for service to restart..."
sleep 10

# Test the deployment
echo "🧪 Testing API endpoint..."
if ssh "$DROPLET_USER@$DROPLET_IP" "curl -f http://localhost:8000/api/v1/health > /dev/null 2>&1"; then
    echo "✅ API is responding"
else
    echo "❌ API is not responding, checking logs..."
    ssh "$DROPLET_USER@$DROPLET_IP" "systemctl status flipsync --no-pager"
    ssh "$DROPLET_USER@$DROPLET_IP" "journalctl -u flipsync --no-pager -n 20"
fi

echo ""
echo "🎉 Code sync and restart complete!"
echo "FlipSync Backend is running at: http://192.168.110.71:8000"
