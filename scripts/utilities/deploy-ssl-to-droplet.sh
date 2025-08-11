#!/bin/bash

# FlipSync SSL Deployment Script
# This script deploys the SSL setup to your DigitalOcean droplet

set -e

# Configuration
DROPLET_IP="192.168.110.71"
DROPLET_USER="root"  # Change if you use a different user
SSH_KEY_PATH="$HOME/.ssh/id_rsa"  # Change to your SSH key path

echo "🚀 FlipSync SSL Deployment to Droplet"
echo "======================================"
echo "Droplet IP: $DROPLET_IP"
echo "User: $DROPLET_USER"
echo ""

# Check if SSH key exists
if [ ! -f "$SSH_KEY_PATH" ]; then
    echo "❌ SSH key not found at $SSH_KEY_PATH"
    echo "Please update SSH_KEY_PATH in this script or create an SSH key"
    exit 1
fi

# Function to run commands on the droplet
run_remote() {
    local command=$1
    echo "🔄 Running on droplet: $command"
    ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$DROPLET_USER@$DROPLET_IP" "$command"
}

# Function to copy files to droplet
copy_to_droplet() {
    local local_file=$1
    local remote_path=$2
    echo "📤 Copying $local_file to droplet:$remote_path"
    scp -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no "$local_file" "$DROPLET_USER@$DROPLET_IP:$remote_path"
}

# Test SSH connection
echo "🧪 Testing SSH connection to droplet..."
if ! ssh -i "$SSH_KEY_PATH" -o StrictHostKeyChecking=no -o ConnectTimeout=10 "$DROPLET_USER@$DROPLET_IP" "echo 'SSH connection successful'" 2>/dev/null; then
    echo "❌ SSH connection failed"
    echo "Please check:"
    echo "  1. SSH key path: $SSH_KEY_PATH"
    echo "  2. Droplet IP: $DROPLET_IP"
    echo "  3. User: $DROPLET_USER"
    echo "  4. SSH key is added to droplet"
    exit 1
fi

echo "✅ SSH connection successful"

# Check if scripts exist locally
if [ ! -f "setup-ssl-certificates.sh" ]; then
    echo "❌ setup-ssl-certificates.sh not found in current directory"
    exit 1
fi

if [ ! -f "verify-ssl-setup.sh" ]; then
    echo "❌ verify-ssl-setup.sh not found in current directory"
    exit 1
fi

# Copy SSL setup scripts to droplet
echo "📤 Copying SSL setup scripts to droplet..."
copy_to_droplet "setup-ssl-certificates.sh" "/tmp/setup-ssl-certificates.sh"
copy_to_droplet "verify-ssl-setup.sh" "/tmp/verify-ssl-setup.sh"

# Make scripts executable on droplet
echo "🔧 Making scripts executable on droplet..."
run_remote "chmod +x /tmp/setup-ssl-certificates.sh"
run_remote "chmod +x /tmp/verify-ssl-setup.sh"

# Check current status on droplet
echo "🔍 Checking current status on droplet..."
echo ""
echo "Current Nginx status:"
run_remote "systemctl status nginx --no-pager -l" || echo "Nginx not running or not installed"

echo ""
echo "Current SSL certificates:"
run_remote "ls -la /etc/letsencrypt/live/ 2>/dev/null || echo 'No SSL certificates found'"

echo ""
echo "Current Nginx sites:"
run_remote "ls -la /etc/nginx/sites-enabled/ 2>/dev/null || echo 'No Nginx sites found'"

# Ask for confirmation
echo ""
echo "⚠️  IMPORTANT: This will modify your droplet's Nginx configuration and install SSL certificates."
echo ""
read -p "Do you want to proceed with SSL setup? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ SSL setup cancelled"
    exit 1
fi

# Run SSL setup on droplet
echo ""
echo "🔐 Running SSL setup on droplet..."
echo "This may take several minutes..."
echo ""

# Execute the SSL setup script on the droplet
if run_remote "/tmp/setup-ssl-certificates.sh"; then
    echo ""
    echo "✅ SSL setup completed successfully!"
else
    echo ""
    echo "❌ SSL setup failed. Please check the error messages above."
    exit 1
fi

# Wait a moment for services to stabilize
echo "⏳ Waiting for services to stabilize..."
sleep 5

# Run verification script
echo ""
echo "🔍 Running SSL verification..."
echo ""

if run_remote "/tmp/verify-ssl-setup.sh"; then
    echo ""
    echo "✅ SSL verification completed!"
else
    echo ""
    echo "⚠️  SSL verification had some issues. Please check the results above."
fi

# Test the eBay OAuth endpoint specifically
echo ""
echo "🧪 Testing eBay OAuth endpoint from local machine..."

# Test HTTPS access to eBay OAuth endpoint
OAUTH_TEST_URL="https://flipsyncai.com/ebay-oauth?test=1"
echo "Testing: $OAUTH_TEST_URL"

if curl -s --max-time 10 "$OAUTH_TEST_URL" > /dev/null 2>&1; then
    echo "✅ eBay OAuth endpoint accessible via HTTPS!"
else
    echo "⚠️  eBay OAuth endpoint test failed (may need a few minutes to propagate)"
fi

# Clean up temporary files on droplet
echo ""
echo "🧹 Cleaning up temporary files on droplet..."
run_remote "rm -f /tmp/setup-ssl-certificates.sh /tmp/verify-ssl-setup.sh"

echo ""
echo "🎉 SSL Deployment Complete!"
echo "=========================="
echo ""
echo "✅ SSL certificates installed on droplet"
echo "✅ Nginx configured with HTTPS"
echo "✅ eBay OAuth endpoint configured"
echo ""
echo "🔗 Your domain should now be accessible at:"
echo "   • https://flipsyncai.com"
echo "   • https://www.flipsyncai.com"
echo "   • https://flipsyncai.com/ebay-oauth"
echo ""
echo "📱 Next Steps:"
echo "   1. Test your React app's OAuth flow"
echo "   2. Generate an OAuth URL in the testing dashboard"
echo "   3. Complete the eBay authorization"
echo "   4. Verify tokens are stored in Redis"
echo ""
echo "🔧 If you need to make changes:"
echo "   • SSH to droplet: ssh -i $SSH_KEY_PATH $DROPLET_USER@$DROPLET_IP"
echo "   • Nginx config: /etc/nginx/sites-available/flipsyncai"
echo "   • SSL certs: /etc/letsencrypt/live/flipsyncai.com/"
echo ""
echo "🆘 If something goes wrong:"
echo "   • Check logs: ssh -i $SSH_KEY_PATH $DROPLET_USER@$DROPLET_IP 'journalctl -u nginx -f'"
echo "   • Restart Nginx: ssh -i $SSH_KEY_PATH $DROPLET_USER@$DROPLET_IP 'systemctl restart nginx'"
echo ""
