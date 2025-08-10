#!/usr/bin/env python3
"""
Complete ISO attachment and tunnel setup for FlipSync VM
"""

import requests
import json
import time
import urllib3
from typing import Dict, Any, Optional

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProxmoxAPI:
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False
        self.ticket = None
        self.csrf_token = None
        
    def authenticate(self) -> bool:
        """Authenticate with Proxmox"""
        auth_url = f"https://{self.host}/api2/json/access/ticket"
        auth_data = {
            'username': self.username,
            'password': self.password
        }
        
        try:
            response = self.session.post(auth_url, data=auth_data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('data'):
                self.ticket = result['data']['ticket']
                self.csrf_token = result['data']['CSRFPreventionToken']
                
                self.session.headers.update({
                    'Cookie': f'PVEAuthCookie={self.ticket}',
                    'CSRFPreventionToken': self.csrf_token
                })
                
                return True
            return False
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def get_vm_config(self, node: str, vmid: int) -> Optional[Dict[str, Any]]:
        """Get VM configuration"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/nodes/{node}/qemu/{vmid}/config")
            response.raise_for_status()
            result = response.json()
            return result.get('data', {})
        except Exception as e:
            print(f"❌ Failed to get VM config: {e}")
            return None
    
    def update_vm_config(self, node: str, vmid: int, config: Dict[str, Any]) -> bool:
        """Update VM configuration"""
        try:
            response = self.session.put(f"https://{self.host}/api2/json/nodes/{node}/qemu/{vmid}/config", data=config)
            response.raise_for_status()
            print(f"✅ VM {vmid} configuration updated")
            return True
        except Exception as e:
            print(f"❌ Failed to update VM config: {e}")
            print(f"   Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            return False
    
    def get_storage_content(self, node: str, storage: str) -> Optional[list]:
        """Get storage content"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/nodes/{node}/storage/{storage}/content")
            response.raise_for_status()
            result = response.json()
            return result.get('data', [])
        except Exception as e:
            print(f"❌ Failed to get storage content: {e}")
            return None

def main():
    """Main function to complete deployment"""
    print("🔧 COMPLETING FLIPSYNC VM DEPLOYMENT")
    print("=" * 50)
    
    # Connection details
    PROXMOX_HOST = "proxmox.proxy.equipment"
    USERNAME = "root@pam"
    PASSWORD = "admin123"
    TARGET_NODE = "pve"
    VMID = 201
    
    # Initialize API
    print("🔐 Connecting to Proxmox...")
    pve = ProxmoxAPI(PROXMOX_HOST, USERNAME, PASSWORD)
    
    if not pve.authenticate():
        print("❌ Failed to authenticate")
        return False
    
    # Check current VM configuration
    print(f"\n📋 Checking VM {VMID} configuration...")
    vm_config = pve.get_vm_config(TARGET_NODE, VMID)
    
    if vm_config:
        print("✅ Current VM configuration:")
        for key, value in vm_config.items():
            if key in ['name', 'memory', 'cores', 'net0', 'scsi0', 'ide2']:
                print(f"   {key}: {value}")
    
    # Check for Ubuntu ISO in storage
    print(f"\n💿 Checking for Ubuntu ISO...")
    iso_content = pve.get_storage_content(TARGET_NODE, 'local')
    ubuntu_iso = None
    
    if iso_content:
        for item in iso_content:
            if 'ubuntu-24.04' in item.get('volid', '').lower():
                ubuntu_iso = item['volid']
                print(f"✅ Found Ubuntu ISO: {ubuntu_iso}")
                break
    
    if not ubuntu_iso:
        print("⚠️  Ubuntu ISO not found in local storage")
        print("   The ISO download may still be in progress")
        print("   Check Proxmox web interface for download status")
    
    # Try to attach ISO if found
    if ubuntu_iso:
        print(f"\n💽 Attaching ISO to VM {VMID}...")
        iso_config = {
            'ide2': f'{ubuntu_iso},media=cdrom'
        }
        
        if pve.update_vm_config(TARGET_NODE, VMID, iso_config):
            print("✅ ISO attached successfully")
        else:
            print("❌ Failed to attach ISO")
    
    # Create tunnel setup script for execution on Proxmox host
    create_tunnel_setup_script()
    
    return True

def create_tunnel_setup_script():
    """Create tunnel setup script"""
    print(f"\n🌐 Creating Cloudflare tunnel setup script...")
    
    tunnel_script = '''#!/bin/bash
# FlipSync Cloudflare Tunnel Setup Script
# Execute this script on the Proxmox host

set -e

echo "🌐 FlipSync Cloudflare Tunnel Setup"
echo "=================================="

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

# Set proper permissions
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

# Check service status
echo "📊 Checking service status..."
systemctl status cloudflared-flipsync --no-pager

echo ""
echo "✅ FlipSync Cloudflare tunnel setup completed!"
echo ""
echo "🔍 To monitor the tunnel:"
echo "   systemctl status cloudflared-flipsync"
echo "   journalctl -u cloudflared-flipsync -f"
echo ""
echo "🌐 Test the tunnel:"
echo "   curl -I https://flipsyncai.com"
echo "   curl -I https://api.flipsyncai.com"
'''
    
    try:
        with open('flipsync_tunnel_setup.sh', 'w') as f:
            f.write(tunnel_script)
        
        # Make script executable
        import os
        os.chmod('flipsync_tunnel_setup.sh', 0o755)
        
        print("✅ Tunnel setup script created: flipsync_tunnel_setup.sh")
        print("📋 Transfer this script to Proxmox host and execute it")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create tunnel script: {e}")
        return False

def print_completion_steps():
    """Print completion steps"""
    print("\n" + "=" * 60)
    print("📋 DEPLOYMENT COMPLETION STEPS")
    print("=" * 60)
    
    print("""
🎯 IMMEDIATE NEXT STEPS:

1. 🖥️  UBUNTU INSTALLATION:
   - Access: https://proxmox.proxy.equipment
   - Navigate to VM 201 (flipsync-production)
   - Click "Console" to access VM
   - Install Ubuntu 24.04 with these settings:
     * Static IP: 192.168.1.201/24
     * Gateway: 192.168.1.1 (adjust for your network)
     * DNS: 8.8.8.8, 1.1.1.1
     * Username: flipsync
     * Enable SSH server

2. 🌐 CLOUDFLARE TUNNEL:
   - Transfer flipsync_tunnel_setup.sh to Proxmox host
   - Execute: bash flipsync_tunnel_setup.sh
   - Verify tunnel is running

3. ✅ VALIDATION:
   - SSH to VM: ssh flipsync@192.168.1.201
   - Test tunnel: curl -I https://flipsyncai.com
   - Check tunnel logs: journalctl -u cloudflared-flipsync -f

4. 📦 FLIPSYNC DEPLOYMENT:
   - Transfer cleaned codebase to VM 201
   - Install dependencies and configure services
   - Start FlipSync application

🎉 The infrastructure is ready for FlipSync deployment!
""")

if __name__ == "__main__":
    success = main()
    
    if success:
        print_completion_steps()
    else:
        print("\n❌ Deployment completion failed.")
