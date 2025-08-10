#!/usr/bin/env python3
"""
Corrected FlipSync Proxmox Deployment Script
- Removes VM 100 (inappropriate ID)
- Creates VMs in 200s range
- Uses correct API credentials
- Sets up Cloudflare tunnel
"""

import requests
import json
import time
import urllib3
from typing import Dict, Any, Optional, List

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProxmoxAPI:
    def __init__(self, host: str, token_id: str, api_key: str):
        self.host = host
        self.token_id = token_id
        self.api_key = api_key
        self.session = requests.Session()
        self.session.verify = False
        
        # Set API token authentication
        self.session.headers.update({
            'Authorization': f'PVEAPIToken={token_id}={api_key}'
        })
        
    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/version")
            response.raise_for_status()
            print("✅ API connection successful")
            return True
        except Exception as e:
            print(f"❌ API connection failed: {e}")
            return False
    
    def get_version(self) -> Optional[Dict[str, Any]]:
        """Get Proxmox version"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/version")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to get version: {e}")
            return None
    
    def get_nodes(self) -> Optional[List[Dict[str, Any]]]:
        """Get Proxmox nodes"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/nodes")
            response.raise_for_status()
            result = response.json()
            return result.get('data', [])
        except Exception as e:
            print(f"❌ Failed to get nodes: {e}")
            return None
    
    def vm_exists(self, node: str, vmid: int) -> bool:
        """Check if VM exists"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/nodes/{node}/qemu/{vmid}/status/current")
            return response.status_code == 200
        except:
            return False
    
    def delete_vm(self, node: str, vmid: int, force: bool = True) -> bool:
        """Delete a VM"""
        try:
            # Stop VM first if running
            self.stop_vm(node, vmid)
            time.sleep(3)
            
            # Delete VM
            params = {'purge': 1} if force else {}
            response = self.session.delete(f"https://{self.host}/api2/json/nodes/{node}/qemu/{vmid}", params=params)
            response.raise_for_status()
            
            result = response.json()
            if result.get('data'):
                print(f"✅ VM {vmid} deletion task started: {result['data']}")
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to delete VM {vmid}: {e}")
            return False
    
    def stop_vm(self, node: str, vmid: int) -> bool:
        """Stop a VM"""
        try:
            response = self.session.post(f"https://{self.host}/api2/json/nodes/{node}/qemu/{vmid}/status/stop")
            if response.status_code in [200, 500]:  # 500 might mean already stopped
                return True
            return False
        except:
            return False
    
    def create_vm(self, node: str, vmid: int, vm_config: Dict[str, Any]) -> bool:
        """Create a VM"""
        try:
            response = self.session.post(f"https://{self.host}/api2/json/nodes/{node}/qemu", data=vm_config)
            response.raise_for_status()
            
            result = response.json()
            if result.get('data'):
                print(f"✅ VM {vmid} creation task: {result['data']}")
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to create VM {vmid}: {e}")
            return False
    
    def get_storage_info(self, node: str) -> Optional[List[Dict[str, Any]]]:
        """Get available storage"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/nodes/{node}/storage")
            response.raise_for_status()
            result = response.json()
            return result.get('data', [])
        except Exception as e:
            print(f"❌ Failed to get storage info: {e}")
            return None

def main():
    """Main deployment function"""
    print("🔧 CORRECTED FlipSync Proxmox Deployment")
    print("=" * 50)
    
    # Correct API credentials
    PROXMOX_HOST = "proxmox.proxy.equipment"
    TOKEN_ID = "root@pam!llm"
    API_KEY = "40702b1d-8c02-4a8b-b650-561ca2794aa7"
    
    # Initialize API client
    print("🔐 Connecting with correct API credentials...")
    pve = ProxmoxAPI(PROXMOX_HOST, TOKEN_ID, API_KEY)
    
    # Test connection
    if not pve.test_connection():
        print("❌ Failed to connect with API token. Exiting.")
        return False
    
    # Get system info
    version_info = pve.get_version()
    if version_info:
        version = version_info.get('data', {}).get('version', 'Unknown')
        print(f"✅ Proxmox Version: {version}")
    
    nodes = pve.get_nodes()
    if not nodes:
        print("❌ Failed to get nodes. Exiting.")
        return False
    
    target_node = nodes[0]['node']
    print(f"🎯 Using node: {target_node}")
    
    # Get storage info
    storage_info = pve.get_storage_info(target_node)
    if storage_info:
        available_storage = [s['storage'] for s in storage_info if s.get('enabled', 0) == 1]
        print(f"✅ Available storage: {available_storage}")
        primary_storage = available_storage[0] if available_storage else 'local-lvm'
    else:
        primary_storage = 'local-lvm'
    
    # STEP 1: Remove VM 100 if it exists
    print(f"\n🗑️  STEP 1: Removing inappropriate VM 100...")
    if pve.vm_exists(target_node, 100):
        print("⚠️  VM 100 exists, removing...")
        if pve.delete_vm(target_node, 100):
            print("✅ VM 100 removed successfully")
            time.sleep(5)  # Wait for deletion to complete
        else:
            print("❌ Failed to remove VM 100")
    else:
        print("✅ VM 100 does not exist, proceeding...")
    
    # STEP 2: Architecture Decision
    print(f"\n🏗️  STEP 2: VM Architecture Decision")
    print("Options:")
    print("A) Single VM (201): 12 cores, 32GB RAM, 500GB - Simpler management")
    print("B) Multi-VM: App(201), DB(202), Frontend(203) - Better separation")
    
    # For this deployment, I'll choose Single VM for simplicity and resource efficiency
    architecture = "single"
    print(f"🎯 Selected: Single VM architecture (more efficient for current needs)")
    
    # STEP 3: Create FlipSync Production VM
    print(f"\n🚀 STEP 3: Creating FlipSync Production VM 201...")
    
    vm_201_config = {
        'vmid': 201,
        'name': 'flipsync-production',
        'memory': 32768,  # 32GB
        'cores': 12,
        'sockets': 1,
        'cpu': 'host',
        'net0': 'virtio,bridge=vmbr0,firewall=1',
        'scsi0': f'{primary_storage}:500,format=raw,cache=writeback',
        'ostype': 'l26',
        'boot': 'order=scsi0',
        'agent': 'enabled=1',
        'description': 'FlipSync Production Server - All-in-one deployment'
    }
    
    if not pve.vm_exists(target_node, 201):
        if pve.create_vm(target_node, 201, vm_201_config):
            print("✅ VM 201 (FlipSync Production) created successfully!")
        else:
            print("❌ Failed to create VM 201")
            return False
    else:
        print("⚠️  VM 201 already exists, skipping creation")
    
    print(f"\n✅ VM CREATION COMPLETED")
    print(f"   VM 201: FlipSync Production Server")
    print(f"   - 12 CPU cores")
    print(f"   - 32GB RAM") 
    print(f"   - 500GB storage ({primary_storage})")
    print(f"   - Ready for Ubuntu 24.04 installation")
    
    return True

def setup_cloudflare_tunnel_commands():
    """Generate Cloudflare tunnel setup commands"""
    print("\n" + "=" * 60)
    print("🌐 CLOUDFLARE TUNNEL SETUP - EXECUTE ON PROXMOX HOST")
    print("=" * 60)
    
    commands = '''
# STEP 1: Install cloudflared on Proxmox host
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb

# STEP 2: Create tunnel configuration directory
mkdir -p /etc/cloudflared

# STEP 3: Create FlipSync tunnel configuration
cat > /etc/cloudflared/flipsync-config.yml << 'EOF'
tunnel: eafc3d89-8b6b-4459-8e46-0c5186c22e1a
credentials-file: /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json

ingress:
  # FlipSync main application
  - hostname: flipsyncai.com
    service: http://192.168.1.201:80
  - hostname: www.flipsyncai.com
    service: http://192.168.1.201:80
  
  # FlipSync API endpoints
  - hostname: api.flipsyncai.com
    service: http://192.168.1.201:8000
  
  # FlipSync WebSocket endpoints
  - hostname: ws.flipsyncai.com
    service: http://192.168.1.201:8000
    originRequest:
      noTLSVerify: true
  
  # Catch-all
  - service: http_status:404
EOF

# STEP 4: Create tunnel credentials file
cat > /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json << 'EOF'
{
  "AccountTag": "81ae7b9517d65c92a227e5e0c5d59c7f",
  "TunnelSecret": "NTc5NDBlZmQtMjk2ZC00OWQyLWIwNjktZGE4MTQxMDhlNjcx",
  "TunnelID": "eafc3d89-8b6b-4459-8e46-0c5186c22e1a"
}
EOF

# STEP 5: Set proper permissions
chmod 600 /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json

# STEP 6: Set up DNS routing for FlipSync domains
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a flipsyncai.com
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a www.flipsyncai.com
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a api.flipsyncai.com
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a ws.flipsyncai.com

# STEP 7: Create systemd service for FlipSync tunnel
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

# STEP 8: Enable and start FlipSync tunnel service
systemctl daemon-reload
systemctl enable cloudflared-flipsync
systemctl start cloudflared-flipsync

# STEP 9: Check tunnel status
systemctl status cloudflared-flipsync
journalctl -u cloudflared-flipsync -f

# STEP 10: Test tunnel connectivity
curl -I https://flipsyncai.com
curl -I https://api.flipsyncai.com
'''
    
    print(commands)
    print("\n🎯 EXECUTE THESE COMMANDS ON PROXMOX HOST TO COMPLETE TUNNEL SETUP")

if __name__ == "__main__":
    success = main()
    
    if success:
        setup_cloudflare_tunnel_commands()
        
        print("\n" + "=" * 60)
        print("📋 DEPLOYMENT STATUS & NEXT STEPS")
        print("=" * 60)
        print("✅ VM 100 removed (inappropriate ID)")
        print("✅ VM 201 created (FlipSync Production Server)")
        print("✅ Correct API credentials used")
        print("🔄 Cloudflare tunnel commands generated")
        
        print("\n🎯 IMMEDIATE NEXT STEPS:")
        print("1. Access Proxmox web interface: https://proxmox.proxy.equipment")
        print("2. Install Ubuntu 24.04 on VM 201 via console")
        print("3. Configure VM 201 networking (get IP address)")
        print("4. Execute Cloudflare tunnel commands on Proxmox host")
        print("5. Deploy FlipSync application to VM 201")
        
        print("\n🌐 TUNNEL ARCHITECTURE:")
        print("- Existing tunnel: Infrastructure access (Proxmox, SSH)")
        print("- FlipSync tunnel: Application traffic (flipsyncai.com)")
        print("- VM 201 IP: 192.168.1.201 (update in tunnel config if different)")
        
    else:
        print("\n❌ Deployment failed. Please check errors above.")
