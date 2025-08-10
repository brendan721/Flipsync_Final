#!/bin/bash
# FlipSync VM 201 Ubuntu Setup Script
# Run this script after Ubuntu 24.04 installation is complete

set -e

echo "🚀 FlipSync VM 201 Ubuntu Setup"
echo "================================"

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root. Please run as the flipsync user."
   exit 1
fi

# Check if flipsync user exists
if [[ $(whoami) != "flipsync" ]]; then
    print_error "This script should be run as the 'flipsync' user."
    print_info "Current user: $(whoami)"
    exit 1
fi

print_status "Starting FlipSync VM setup as user: $(whoami)"

# Update system packages
print_info "Updating system packages..."
sudo apt update && sudo apt upgrade -y
print_status "System packages updated"

# Install essential packages
print_info "Installing essential packages..."
sudo apt install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    curl \
    wget \
    htop \
    nano \
    vim \
    unzip \
    build-essential \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    net-tools \
    openssh-server

print_status "Essential packages installed"

# Configure SSH
print_info "Configuring SSH..."
sudo systemctl enable ssh
sudo systemctl start ssh

# Create SSH directory for flipsync user
mkdir -p ~/.ssh
chmod 700 ~/.ssh

print_status "SSH configured and enabled"

# Configure static IP (this should match the installation settings)
print_info "Verifying network configuration..."
ip addr show
print_warning "Ensure static IP 192.168.1.201/24 is configured during Ubuntu installation"

# Install Python dependencies for FlipSync
print_info "Setting up Python environment..."
python3 -m venv /opt/flipsync/venv_agentic || {
    sudo mkdir -p /opt/flipsync
    sudo chown flipsync:flipsync /opt/flipsync
    python3 -m venv /opt/flipsync/venv_agentic
}

print_status "Python virtual environment created"

# Install PostgreSQL client (for connecting to external DB)
print_info "Installing PostgreSQL client..."
sudo apt install -y postgresql-client-16 || sudo apt install -y postgresql-client
print_status "PostgreSQL client installed"

# Install Redis client
print_info "Installing Redis client..."
sudo apt install -y redis-tools
print_status "Redis client installed"

# Create FlipSync directories
print_info "Creating FlipSync directory structure..."
sudo mkdir -p /opt/flipsync/{logs,data,config,scripts}
sudo chown -R flipsync:flipsync /opt/flipsync
print_status "Directory structure created"

# Configure firewall
print_info "Configuring firewall..."
sudo ufw allow ssh
sudo ufw allow 8000/tcp  # FlipSync API
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw --force enable
print_status "Firewall configured"

# Install Docker (for potential containerized services)
print_info "Installing Docker..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add flipsync user to docker group
sudo usermod -aG docker flipsync
print_status "Docker installed and configured"

# Install Nginx (for reverse proxy)
print_info "Installing Nginx..."
sudo apt install -y nginx
sudo systemctl enable nginx
print_status "Nginx installed"

# Create systemd service for FlipSync
print_info "Creating FlipSync systemd service..."
sudo tee /etc/systemd/system/flipsync.service > /dev/null <<EOF
[Unit]
Description=FlipSync Agentic System
After=network.target

[Service]
Type=simple
User=flipsync
Group=flipsync
WorkingDirectory=/opt/flipsync
Environment=PATH=/opt/flipsync/venv_agentic/bin
ExecStart=/opt/flipsync/venv_agentic/bin/python -m fs_agt_clean.app.main --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
print_status "FlipSync systemd service created"

# Test external service connectivity
print_info "Testing external service connectivity..."

# Test database connectivity
print_info "Testing database connectivity to 174.138.77.110:5432..."
nc -zv 174.138.77.110 5432 && print_status "Database connection successful" || print_warning "Database connection failed"

# Test Redis connectivity
print_info "Testing Redis connectivity to 174.138.77.110:6379..."
nc -zv 174.138.77.110 6379 && print_status "Redis connection successful" || print_warning "Redis connection failed"

# Test Qdrant connectivity
print_info "Testing Qdrant connectivity to 174.138.77.110:6333..."
nc -zv 174.138.77.110 6333 && print_status "Qdrant connection successful" || print_warning "Qdrant connection failed"

# Display system information
print_info "System Information:"
echo "==================="
echo "Hostname: $(hostname)"
echo "IP Address: $(hostname -I)"
echo "OS: $(lsb_release -d | cut -f2)"
echo "Kernel: $(uname -r)"
echo "Memory: $(free -h | grep Mem | awk '{print $2}')"
echo "CPU Cores: $(nproc)"
echo "Disk Space: $(df -h / | tail -1 | awk '{print $4}' | sed 's/G/ GB/')"

print_status "VM setup completed successfully!"

echo ""
echo "📋 NEXT STEPS:"
echo "=============="
echo "1. Transfer FlipSync codebase to /opt/flipsync/"
echo "2. Install Python dependencies: pip install -r requirements.txt"
echo "3. Configure environment variables"
echo "4. Set up Cloudflare tunnel on Proxmox host"
echo "5. Start FlipSync service: sudo systemctl start flipsync"
echo ""
echo "🔗 SSH Access: ssh flipsync@192.168.1.201"
echo "🌐 Proxmox Console: https://proxmox.proxy.equipment"
echo ""
