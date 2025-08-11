#!/bin/bash

echo "🚀 FlipSync Cloudflared Setup Script"
echo "===================================="

# Update system
echo "📦 Updating system packages..."
apt update

# Download and install cloudflared
echo "⬇️ Downloading cloudflared..."
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

echo "📦 Installing cloudflared..."
dpkg -i cloudflared.deb

# Verify installation
echo "✅ Verifying installation..."
cloudflared --version

# Create cloudflared directory
echo "📁 Creating cloudflared directory..."
mkdir -p /root/.cloudflared

# Create cert.pem file
echo "🔑 Creating certificate file..."
cat > /root/.cloudflared/cert.pem << 'EOF'
-----BEGIN ARGO TUNNEL TOKEN-----
eyJ6b25lSUQiOiIzNjAwYTI0YjQ0YjgwYzhkM2NjMGMxOGZhM2QzYTM0ZiIsImFj
Y291bnRJRCI6IjgxYWU3Yjk1MTdkNjVjOTJhMjI3ZTVlMGM1ZDU5YzdmIiwic2Vy
dmljZUtleSI6InYxLjAtYjhhYmIwMWM4OGU2M2JkMzY3M2FhZTZiLWMxMjc4YmQx
ZjgwMjRmNzU2NDI2YWUxMGRmNjk1NDMzZjJlNWI3YTJkM2ViZTIwZTI4MTdhMzIw
MGY1ZWU3OGFmZDdjN2YzMzdhNzdlMTVhYzA5OTVjNmVmOTFkM2M0MDgwOWEyYzQ1
MmI4NmJlMjg4YzI5OTAxMGU4OGQxY2FlMjU1ZTk3NTQ5Nzg3NmQxYzllYjBmZDRk
YTMwZTM3MTgiLCJhcGlUb2tlbiI6InhJUmgwUXRsbmpORWU1bThWcVZZM1BKMlBk
M2pDWHRKNE84Y3R6Q20ifQ==
-----END ARGO TUNNEL TOKEN-----
EOF

# Create tunnel
echo "🌐 Creating tunnel..."
cloudflared tunnel create flipsync-production

# Get tunnel ID
TUNNEL_ID=$(cloudflared tunnel list | grep flipsync-production | awk '{print $1}')
echo "📋 Tunnel ID: $TUNNEL_ID"

# Create config file
echo "⚙️ Creating configuration file..."
cat > /root/.cloudflared/config.yml << EOF
tunnel: flipsync-production
credentials-file: /root/.cloudflared/$TUNNEL_ID.json

ingress:
  - hostname: flipsyncai.com
    service: http://localhost:8000
  - hostname: www.flipsyncai.com
    service: http://localhost:8000
  - service: http_status:404
EOF

# Set up DNS routes
echo "🌍 Setting up DNS routes..."
cloudflared tunnel route dns $TUNNEL_ID flipsyncai.com
cloudflared tunnel route dns $TUNNEL_ID www.flipsyncai.com

# Install service
echo "🔧 Installing cloudflared service..."
cloudflared service install

# Enable and start service
echo "🚀 Starting cloudflared service..."
systemctl enable cloudflared
systemctl start cloudflared

# Check status
echo "📊 Service status:"
systemctl status cloudflared --no-pager

echo ""
echo "✅ Cloudflared setup complete!"
echo "🌐 Your domains should now be accessible:"
echo "   - https://flipsyncai.com"
echo "   - https://www.flipsyncai.com"
echo ""
echo "🔍 To check tunnel status: cloudflared tunnel list"
echo "📊 To check service status: systemctl status cloudflared"
