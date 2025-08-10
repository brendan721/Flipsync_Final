#!/bin/bash
# Cloudflare Tunnel Setup for FlipSync
# Run this script on the Proxmox host (not the VM)

set -e

echo "🌐 FlipSync Cloudflare Tunnel Setup"
echo "==================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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
if [[ $EUID -ne 0 ]]; then
   print_error "This script must be run as root on the Proxmox host"
   exit 1
fi

# Cloudflare tunnel configuration
TUNNEL_ID="eafc3d89-8b6b-4459-8e46-0c5186c22e1a"
ACCOUNT_TAG="81ae7b9517d65c92a227e5e0c5d59c7f"
TUNNEL_SECRET="NTc5NDBlZmQtMjk2ZC00OWQyLWIwNjktZGE4MTQxMDhlNjcx"
VM_IP="192.168.110.201"

print_info "Installing cloudflared..."

# Download and install cloudflared
if ! command -v cloudflared &> /dev/null; then
    print_info "Downloading cloudflared..."
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
    dpkg -i cloudflared-linux-amd64.deb
    rm cloudflared-linux-amd64.deb
    print_status "cloudflared installed"
else
    print_status "cloudflared already installed"
fi

# Create cloudflared configuration directory
print_info "Creating cloudflared configuration..."
mkdir -p /etc/cloudflared

# Create tunnel credentials file
print_info "Creating tunnel credentials..."
cat > /etc/cloudflared/${TUNNEL_ID}.json << EOF
{
  "AccountTag": "${ACCOUNT_TAG}",
  "TunnelSecret": "${TUNNEL_SECRET}",
  "TunnelID": "${TUNNEL_ID}"
}
EOF

chmod 600 /etc/cloudflared/${TUNNEL_ID}.json
print_status "Tunnel credentials created"

# Create tunnel configuration file
print_info "Creating tunnel configuration..."
cat > /etc/cloudflared/flipsync-config.yml << EOF
tunnel: ${TUNNEL_ID}
credentials-file: /etc/cloudflared/${TUNNEL_ID}.json

ingress:
  - hostname: flipsyncai.com
    service: http://${VM_IP}:80
  - hostname: www.flipsyncai.com
    service: http://${VM_IP}:80
  - hostname: api.flipsyncai.com
    service: http://${VM_IP}:8000
  - hostname: ws.flipsyncai.com
    service: http://${VM_IP}:8000
  - service: http_status:404
EOF

print_status "Tunnel configuration created"

# Create systemd service for the tunnel
print_info "Creating systemd service..."
cat > /etc/systemd/system/cloudflared-flipsync.service << EOF
[Unit]
Description=Cloudflare Tunnel for FlipSync
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloudflared tunnel --config /etc/cloudflared/flipsync-config.yml run
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd and enable the service
systemctl daemon-reload
systemctl enable cloudflared-flipsync

print_status "Systemd service created and enabled"

# Test tunnel configuration
print_info "Testing tunnel configuration..."
cloudflared tunnel --config /etc/cloudflared/flipsync-config.yml validate

if [ $? -eq 0 ]; then
    print_status "Tunnel configuration is valid"
else
    print_error "Tunnel configuration validation failed"
    exit 1
fi

# Set up DNS routing (requires cloudflared to be authenticated)
print_info "Setting up DNS routing..."
print_warning "Note: DNS routing requires cloudflared to be authenticated with your Cloudflare account"

# Start the tunnel service
print_info "Starting Cloudflare tunnel service..."
systemctl start cloudflared-flipsync

# Check service status
sleep 5
if systemctl is-active --quiet cloudflared-flipsync; then
    print_status "Cloudflare tunnel service is running"
else
    print_error "Cloudflare tunnel service failed to start"
    print_info "Checking service logs..."
    journalctl -u cloudflared-flipsync --no-pager -n 20
    exit 1
fi

# Display service status
print_info "Service Status:"
systemctl status cloudflared-flipsync --no-pager -l

print_status "Cloudflare tunnel setup completed!"

echo ""
echo "📋 TUNNEL INFORMATION:"
echo "====================="
echo "Tunnel ID: ${TUNNEL_ID}"
echo "VM IP: ${VM_IP}"
echo "Domains:"
echo "  - https://flipsyncai.com → http://${VM_IP}:80"
echo "  - https://www.flipsyncai.com → http://${VM_IP}:80"
echo "  - https://api.flipsyncai.com → http://${VM_IP}:8000"
echo "  - https://ws.flipsyncai.com → http://${VM_IP}:8000"
echo ""
echo "🔧 MANAGEMENT COMMANDS:"
echo "======================"
echo "Start tunnel:   systemctl start cloudflared-flipsync"
echo "Stop tunnel:    systemctl stop cloudflared-flipsync"
echo "Restart tunnel: systemctl restart cloudflared-flipsync"
echo "Check status:   systemctl status cloudflared-flipsync"
echo "View logs:      journalctl -u cloudflared-flipsync -f"
echo ""
echo "⚠️  IMPORTANT NOTES:"
echo "==================="
echo "1. Ensure VM 201 is running with IP ${VM_IP}"
echo "2. Configure Nginx on VM to serve on ports 80 and 8000"
echo "3. FlipSync application should run on port 8000"
echo "4. DNS records should automatically be created by Cloudflare"
echo ""
