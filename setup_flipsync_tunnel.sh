#!/bin/bash
# FlipSync Cloudflare Tunnel Complete Setup
set -e

echo "🚀 Starting FlipSync Cloudflare Tunnel Setup..."

# Install cloudflared
echo "📥 Installing cloudflared..."
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -O /tmp/cloudflared.deb
dpkg -i /tmp/cloudflared.deb
echo "✅ cloudflared installed"

# Create configuration directory
echo "📁 Creating configuration directory..."
mkdir -p /etc/cloudflared

# Create tunnel configuration
echo "📝 Creating tunnel configuration..."
cat > /etc/cloudflared/flipsync-config.yml << 'EOF'
tunnel: eafc3d89-8b6b-4459-8e46-0c5186c22e1a
credentials-file: /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json

ingress:
  - hostname: flipsyncai.com
    service: http://192.168.1.201:80
  - hostname: www.flipsyncai.com
    service: http://192.168.1.201:80
  - hostname: api.flipsyncai.com
    service: http://192.168.1.201:8000
  - hostname: ws.flipsyncai.com
    service: http://192.168.1.201:8000
    originRequest:
      noTLSVerify: true
  - service: http_status:404
EOF

# Create credentials file
echo "🔑 Creating credentials file..."
cat > /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json << 'EOF'
{
  "AccountTag": "81ae7b9517d65c92a227e5e0c5d59c7f",
  "TunnelSecret": "NTc5NDBlZmQtMjk2ZC00OWQyLWIwNjktZGE4MTQxMDhlNjcx",
  "TunnelID": "eafc3d89-8b6b-4459-8e46-0c5186c22e1a"
}
EOF

chmod 600 /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json
echo "✅ Configuration files created"

# Set up DNS routing
echo "🌐 Setting up DNS routing..."
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a flipsyncai.com
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a www.flipsyncai.com
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a api.flipsyncai.com
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a ws.flipsyncai.com
echo "✅ DNS routing configured"

# Create systemd service
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/cloudflared-flipsync.service << 'EOF'
[Unit]
Description=Cloudflare Tunnel for FlipSync
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloudflared tunnel --config /etc/cloudflared/flipsync-config.yml run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "🚀 Starting tunnel service..."
systemctl daemon-reload
systemctl enable cloudflared-flipsync
systemctl start cloudflared-flipsync

# Wait a moment for service to start
sleep 5

# Check service status
echo "📊 Checking service status..."
systemctl status cloudflared-flipsync --no-pager

echo ""
echo "✅ FlipSync Cloudflare tunnel setup completed!"
echo ""
echo "🔍 Monitor tunnel:"
echo "   systemctl status cloudflared-flipsync"
echo "   journalctl -u cloudflared-flipsync -f"
echo ""
echo "🌐 Test tunnel:"
echo "   curl -I https://flipsyncai.com"
echo "   curl -I https://api.flipsyncai.com"
echo ""
echo "🎉 Tunnel is ready for FlipSync traffic!"
