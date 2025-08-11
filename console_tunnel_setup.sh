#!/bin/bash
# FlipSync Console Tunnel Setup - Simplified for copy-paste execution
set -e

echo "🚀 FlipSync Tunnel Setup Starting..."

# Update system
apt update -y

# Install cloudflared
echo "📥 Installing cloudflared..."
wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -O /tmp/cloudflared.deb
dpkg -i /tmp/cloudflared.deb
rm /tmp/cloudflared.deb
echo "✅ cloudflared installed"

# Create configuration directory
mkdir -p /etc/cloudflared

# Create tunnel credentials
echo "🔐 Creating tunnel credentials..."
cat > /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json << 'EOF'
{
  "AccountTag": "81ae7b9517d65c92a227e5e0c5d59c7f",
  "TunnelSecret": "NTc5NDBlZmQtMjk2ZC00OWQyLWIwNjktZGE4MTQxMDhlNjcx",
  "TunnelID": "eafc3d89-8b6b-4459-8e46-0c5186c22e1a"
}
EOF

chmod 600 /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json

# Create tunnel configuration
echo "📝 Creating tunnel configuration..."
cat > /etc/cloudflared/config.yml << 'EOF'
tunnel: eafc3d89-8b6b-4459-8e46-0c5186c22e1a
credentials-file: /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json

ingress:
  - hostname: flipsyncai.com
    service: http://localhost:8000
  - hostname: www.flipsyncai.com
    service: http://localhost:8000
  - hostname: proxmox.flipsyncai.com
    service: ssh://localhost:22
  - service: http_status:404

logfile: /var/log/cloudflared.log
loglevel: info
EOF

# Create systemd service
echo "🔧 Creating systemd service..."
cat > /etc/systemd/system/cloudflared.service << 'EOF'
[Unit]
Description=Cloudflare Tunnel for FlipSync
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloudflared tunnel --config /etc/cloudflared/config.yml run
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
echo "🚀 Starting tunnel service..."
systemctl daemon-reload
systemctl enable cloudflared
systemctl start cloudflared

# Wait and check status
sleep 5
systemctl status cloudflared --no-pager

echo "✅ Tunnel setup completed!"
echo "🔍 Checking tunnel logs..."
tail -n 10 /var/log/cloudflared.log

echo "🌐 Testing connectivity..."
curl -I http://localhost:8000 || echo "Local service not yet running"

echo "📋 Next: Deploy FlipSync application"
