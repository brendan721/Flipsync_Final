#!/bin/bash

# FlipSync Backend Production Deployment Script (RSYNC Version)
# Deploys to fresh DigitalOcean droplet at 174.138.77.110

set -e  # Exit on any error

# Configuration
DROPLET_IP="174.138.77.110"
DROPLET_USER="root"
DEPLOYMENT_PATH="/opt/flipsync"
LOCAL_PATH="/home/brend/Flipsync_Final"

echo "🚀 Starting FlipSync Backend Production Deployment (RSYNC)"
echo "=========================================================="
echo "Target: ${DROPLET_USER}@${DROPLET_IP}:${DEPLOYMENT_PATH}"
echo "Source: ${LOCAL_PATH}"
echo ""

# Function to run commands on the droplet
run_remote() {
    ssh -o StrictHostKeyChecking=no ${DROPLET_USER}@${DROPLET_IP} "$1"
}

echo "1️⃣ Preparing Droplet Environment..."

# Update system and install dependencies
run_remote "apt update && apt upgrade -y"
run_remote "apt install -y python3 python3-pip python3-venv git nginx postgresql postgresql-contrib redis-server curl wget build-essential python3-dev libpq-dev"

echo "✅ System dependencies installed"

echo "2️⃣ Setting up PostgreSQL..."

# Configure PostgreSQL
run_remote "sudo -u postgres psql -c \"ALTER USER postgres PASSWORD 'FlipSync_DB_Prod_2024_Secure_Key_9x7z';\""
run_remote "sudo -u postgres createdb flipsync_agentic_test || echo 'Database already exists'"

# Configure PostgreSQL for production
run_remote "sed -i \"s/#listen_addresses = 'localhost'/listen_addresses = '*'/g\" /etc/postgresql/*/main/postgresql.conf"
run_remote "echo \"host all all 0.0.0.0/0 md5\" >> /etc/postgresql/*/main/pg_hba.conf"
run_remote "systemctl restart postgresql"
run_remote "systemctl enable postgresql"

echo "✅ PostgreSQL configured"

echo "3️⃣ Setting up Redis..."

# Configure Redis
run_remote "sed -i 's/# requirepass foobared/requirepass FlipSync_Redis_Prod_2024_Secure_Key_9x7z/' /etc/redis/redis.conf"
run_remote "sed -i 's/bind 127.0.0.1 ::1/bind 0.0.0.0/' /etc/redis/redis.conf"
run_remote "systemctl restart redis-server"
run_remote "systemctl enable redis-server"

echo "✅ Redis configured"

echo "4️⃣ Installing Qdrant Vector Database..."

# Install Qdrant
run_remote "curl -L https://github.com/qdrant/qdrant/releases/latest/download/qdrant-x86_64-unknown-linux-gnu.tar.gz | tar xz -C /opt/"
run_remote "mv /opt/qdrant /opt/qdrant-bin"
run_remote "mkdir -p /opt/qdrant/storage"

# Create Qdrant systemd service
run_remote "cat > /etc/systemd/system/qdrant.service << 'EOF'
[Unit]
Description=Qdrant Vector Database
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/qdrant
ExecStart=/opt/qdrant-bin/qdrant --config-path /opt/qdrant/config.yaml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

# Create Qdrant config
run_remote "mkdir -p /opt/qdrant && cat > /opt/qdrant/config.yaml << 'EOF'
service:
  host: 0.0.0.0
  http_port: 6333
  grpc_port: 6334

storage:
  storage_path: /opt/qdrant/storage
EOF"

run_remote "systemctl daemon-reload"
run_remote "systemctl enable qdrant"
run_remote "systemctl start qdrant"

echo "✅ Qdrant installed and started"

echo "5️⃣ Transferring FlipSync Codebase..."

# Create deployment directory
run_remote "mkdir -p ${DEPLOYMENT_PATH}"

# Transfer codebase using rsync (excluding unnecessary files)
echo "Transferring files via rsync..."
rsync -avz --progress \
    --exclude='.git/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.pytest_cache/' \
    --exclude='node_modules/' \
    --exclude='venv*/' \
    --exclude='.env*' \
    --exclude='*.log' \
    --exclude='test_*.py' \
    --exclude='deploy_*.sh' \
    --exclude='COMPREHENSIVE_VALIDATION_REPORT.md' \
    ${LOCAL_PATH}/ ${DROPLET_USER}@${DROPLET_IP}:${DEPLOYMENT_PATH}/

echo "✅ Codebase transferred"

echo "6️⃣ Setting up Python Environment..."

# Create virtual environment and install dependencies
run_remote "cd ${DEPLOYMENT_PATH} && python3 -m venv venv_production"
run_remote "cd ${DEPLOYMENT_PATH} && source venv_production/bin/activate && pip install --upgrade pip"
run_remote "cd ${DEPLOYMENT_PATH} && source venv_production/bin/activate && pip install -r requirements.txt"

echo "✅ Python environment configured"

echo "7️⃣ Configuring Environment..."

# Transfer production configuration
scp -o StrictHostKeyChecking=no production_deployment_config.env ${DROPLET_USER}@${DROPLET_IP}:${DEPLOYMENT_PATH}/.env

echo "✅ Environment configured"

echo "8️⃣ Initializing Database..."

# Initialize database tables
run_remote "cd ${DEPLOYMENT_PATH} && source venv_production/bin/activate && python -c \"
import asyncio
import os
import sys
sys.path.insert(0, 'fs_agt_clean')
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@localhost:5432/flipsync_agentic_test'
from fs_agt_clean.core.db.database import Database
from fs_agt_clean.core.config.config_manager import ConfigManager

async def init_db():
    try:
        config = ConfigManager()
        db = Database(config)
        await db.initialize()
        print('✅ Database initialized successfully')
    except Exception as e:
        print(f'❌ Database initialization failed: {e}')
        raise

asyncio.run(init_db())
\""

echo "✅ Database initialized"

echo "9️⃣ Setting up Nginx..."

# Configure Nginx
run_remote "cat > /etc/nginx/sites-available/flipsync << 'EOF'
server {
    listen 80;
    server_name flipsyncai.com www.flipsyncai.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection \"upgrade\";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF"

run_remote "ln -sf /etc/nginx/sites-available/flipsync /etc/nginx/sites-enabled/"
run_remote "rm -f /etc/nginx/sites-enabled/default"
run_remote "nginx -t"
run_remote "systemctl restart nginx"
run_remote "systemctl enable nginx"

echo "✅ Nginx configured"

echo "🔟 Creating FlipSync Service..."

# Create systemd service for FlipSync
run_remote "cat > /etc/systemd/system/flipsync.service << 'EOF'
[Unit]
Description=FlipSync Backend API
After=network.target postgresql.service redis-server.service qdrant.service
Requires=postgresql.service redis-server.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/flipsync
Environment=PATH=/opt/flipsync/venv_production/bin
ExecStart=/opt/flipsync/venv_production/bin/uvicorn fs_agt_clean.app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF"

run_remote "systemctl daemon-reload"
run_remote "systemctl enable flipsync"
run_remote "systemctl start flipsync"

echo "✅ FlipSync service created and started"

echo "1️⃣1️⃣ Verifying Deployment..."

# Wait for service to start
sleep 15

# Test the deployment
echo "Testing API endpoint..."
if run_remote "curl -f http://localhost:8000/ > /dev/null 2>&1"; then
    echo "✅ API is responding"
else
    echo "❌ API is not responding, checking logs..."
    run_remote "systemctl status flipsync --no-pager"
    run_remote "journalctl -u flipsync --no-pager -n 20"
fi

# Test database connection
echo "Testing database connection..."
if run_remote "cd ${DEPLOYMENT_PATH} && source venv_production/bin/activate && python -c \"
import asyncio
import asyncpg
async def test_db():
    try:
        conn = await asyncpg.connect('postgresql://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@localhost:5432/flipsync_agentic_test')
        result = await conn.fetchval('SELECT 1')
        await conn.close()
        print('✅ Database connection successful')
    except Exception as e:
        print(f'❌ Database connection failed: {e}')
        raise
asyncio.run(test_db())
\""; then
    echo "✅ Database connection successful"
else
    echo "❌ Database connection failed"
fi

echo ""
echo "🎉 DEPLOYMENT COMPLETE!"
echo "======================"
echo "FlipSync Backend is now running at:"
echo "- API: http://flipsyncai.com"
echo "- Docs: http://flipsyncai.com/docs"
echo "- Health: http://flipsyncai.com/api/v1/health"
echo ""
echo "Services Status:"
echo "- FlipSync API: systemctl status flipsync"
echo "- PostgreSQL: systemctl status postgresql"
echo "- Redis: systemctl status redis-server"
echo "- Qdrant: systemctl status qdrant"
echo "- Nginx: systemctl status nginx"
echo ""
echo "Next Steps:"
echo "1. Run comprehensive backend validation tests"
echo "2. Set up SSL certificates with Let's Encrypt"
echo "3. Configure domain DNS to point to ${DROPLET_IP}"
echo "4. Deploy frontend"
