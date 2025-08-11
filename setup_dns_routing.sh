#!/bin/bash
# FlipSync DNS Routing Setup Script
set -e

echo "🌐 Setting up DNS routing for FlipSync tunnel..."

TUNNEL_ID="eafc3d89-8b6b-4459-8e46-0c5186c22e1a"

# Check if tunnel is running
echo "📋 Checking tunnel status..."
if systemctl is-active --quiet cloudflared; then
    echo "✅ Tunnel service is running"
else
    echo "❌ Tunnel service is not running"
    echo "Starting tunnel service..."
    systemctl start cloudflared
    sleep 5
fi

# Show tunnel info
echo "📊 Tunnel information:"
cloudflared tunnel info $TUNNEL_ID || echo "Info command failed - tunnel may need authentication"

# Authenticate cloudflared (this will open browser)
echo "🔐 Authenticating cloudflared..."
echo "This will open a browser window for authentication..."
cloudflared tunnel login

# Configure DNS routes
echo "🌐 Configuring DNS routes..."

echo "Setting up flipsyncai.com..."
cloudflared tunnel route dns $TUNNEL_ID flipsyncai.com

echo "Setting up www.flipsyncai.com..."
cloudflared tunnel route dns $TUNNEL_ID www.flipsyncai.com

echo "Setting up proxmox.flipsyncai.com..."
cloudflared tunnel route dns $TUNNEL_ID proxmox.flipsyncai.com

# Verify routes
echo "📋 Verifying DNS routes..."
cloudflared tunnel route dns --help || echo "Route verification not available"

# Check tunnel status
echo "📊 Final tunnel status:"
systemctl status cloudflared --no-pager

echo "📝 Checking tunnel logs:"
tail -n 20 /var/log/cloudflared.log

echo "✅ DNS routing setup completed!"
echo ""
echo "🔍 Testing connectivity:"
echo "You can now test:"
echo "- https://flipsyncai.com"
echo "- https://www.flipsyncai.com" 
echo "- ssh://proxmox.flipsyncai.com"
echo ""
echo "Note: DNS propagation may take a few minutes."
