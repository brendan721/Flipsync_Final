#!/usr/bin/env python3
"""
FlipSync Proxmox Deployment Script
Uses Proxmox API through existing tunnel to create and configure VMs
"""

import requests
import json
import time
import urllib3
from typing import Dict, Any, Optional

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class ProxmoxAPI:
    def __init__(self, host: str, username: str, password: str):
        self.host = host
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.verify = False  # Disable SSL verification
        self.ticket = None
        self.csrf_token = None
        
    def authenticate(self) -> bool:
        """Authenticate with Proxmox API"""
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
                
                # Set authentication headers
                self.session.headers.update({
                    'Cookie': f'PVEAuthCookie={self.ticket}',
                    'CSRFPreventionToken': self.csrf_token
                })
                
                print("✅ Successfully authenticated with Proxmox API")
                return True
            else:
                print("❌ Authentication failed: No data in response")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def get_version(self) -> Optional[Dict[str, Any]]:
        """Get Proxmox version information"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/version")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to get version: {e}")
            return None
    
    def get_nodes(self) -> Optional[Dict[str, Any]]:
        """Get list of Proxmox nodes"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/nodes")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to get nodes: {e}")
            return None
    
    def create_vm(self, node: str, vmid: int, vm_config: Dict[str, Any]) -> bool:
        """Create a new VM"""
        try:
            url = f"https://{self.host}/api2/json/nodes/{node}/qemu"
            response = self.session.post(url, data=vm_config)
            response.raise_for_status()
            
            result = response.json()
            if result.get('data'):
                print(f"✅ VM {vmid} creation task started: {result['data']}")
                return True
            else:
                print(f"❌ Failed to create VM {vmid}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to create VM {vmid}: {e}")
            return False
    
    def get_vm_status(self, node: str, vmid: int) -> Optional[Dict[str, Any]]:
        """Get VM status"""
        try:
            url = f"https://{self.host}/api2/json/nodes/{node}/qemu/{vmid}/status/current"
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to get VM {vmid} status: {e}")
            return None
    
    def start_vm(self, node: str, vmid: int) -> bool:
        """Start a VM"""
        try:
            url = f"https://{self.host}/api2/json/nodes/{node}/qemu/{vmid}/status/start"
            response = self.session.post(url)
            response.raise_for_status()
            
            result = response.json()
            if result.get('data'):
                print(f"✅ VM {vmid} start task initiated: {result['data']}")
                return True
            else:
                print(f"❌ Failed to start VM {vmid}")
                return False
                
        except Exception as e:
            print(f"❌ Failed to start VM {vmid}: {e}")
            return False

def main():
    """Main deployment function"""
    print("🚀 FlipSync Proxmox Deployment Script")
    print("=" * 50)
    
    # Proxmox connection details
    PROXMOX_HOST = "proxmox.proxy.equipment"
    PROXMOX_USER = "root@pam"
    PROXMOX_PASS = "admin123"
    
    # FlipSync VM configuration
    FLIPSYNC_VMID = 100
    VM_CONFIG = {
        'vmid': FLIPSYNC_VMID,
        'name': 'flipsync-production',
        'memory': 32768,  # 32GB RAM
        'cores': 12,
        'sockets': 1,
        'cpu': 'host',
        'net0': 'virtio,bridge=vmbr0,firewall=1',
        'scsi0': 'local-lvm:500,format=raw,cache=writeback',
        'ostype': 'l26',
        'boot': 'order=scsi0',
        'agent': 'enabled=1'
    }
    
    # Initialize Proxmox API client
    print("🔐 Connecting to Proxmox API...")
    pve = ProxmoxAPI(PROXMOX_HOST, PROXMOX_USER, PROXMOX_PASS)
    
    # Authenticate
    if not pve.authenticate():
        print("❌ Failed to authenticate with Proxmox. Exiting.")
        return False
    
    # Get Proxmox version
    print("\n📊 Getting Proxmox information...")
    version_info = pve.get_version()
    if version_info:
        version = version_info.get('data', {}).get('version', 'Unknown')
        print(f"✅ Proxmox Version: {version}")
    
    # Get available nodes
    nodes_info = pve.get_nodes()
    if not nodes_info or not nodes_info.get('data'):
        print("❌ Failed to get node information. Exiting.")
        return False
    
    nodes = nodes_info['data']
    print(f"✅ Available nodes: {[node['node'] for node in nodes]}")
    
    # Use the first available node
    target_node = nodes[0]['node']
    print(f"🎯 Using node: {target_node}")
    
    # Check if VM already exists
    print(f"\n🔍 Checking if VM {FLIPSYNC_VMID} already exists...")
    vm_status = pve.get_vm_status(target_node, FLIPSYNC_VMID)
    
    if vm_status and vm_status.get('data'):
        print(f"⚠️  VM {FLIPSYNC_VMID} already exists")
        current_status = vm_status['data'].get('status', 'unknown')
        print(f"   Current status: {current_status}")
        
        if current_status == 'stopped':
            print(f"🚀 Starting existing VM {FLIPSYNC_VMID}...")
            pve.start_vm(target_node, FLIPSYNC_VMID)
        
        return True
    
    # Create FlipSync VM
    print(f"\n🏗️  Creating FlipSync VM {FLIPSYNC_VMID}...")
    print(f"   Configuration: {VM_CONFIG}")
    
    if pve.create_vm(target_node, FLIPSYNC_VMID, VM_CONFIG):
        print(f"✅ VM {FLIPSYNC_VMID} created successfully!")
        
        # Wait a moment for VM to be ready
        print("⏳ Waiting for VM to be ready...")
        time.sleep(5)
        
        # Start the VM
        print(f"🚀 Starting VM {FLIPSYNC_VMID}...")
        pve.start_vm(target_node, FLIPSYNC_VMID)
        
        return True
    else:
        print(f"❌ Failed to create VM {FLIPSYNC_VMID}")
        return False

def setup_cloudflare_tunnel():
    """Instructions for setting up Cloudflare tunnel"""
    print("\n" + "=" * 50)
    print("🌐 CLOUDFLARE TUNNEL SETUP INSTRUCTIONS")
    print("=" * 50)
    
    tunnel_commands = """
# 1. SSH into Proxmox host (through existing tunnel or console)
# 2. Install cloudflared:
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb

# 3. Create FlipSync tunnel configuration:
mkdir -p /etc/cloudflared
cat > /etc/cloudflared/flipsync-config.yml << 'EOF'
tunnel: eafc3d89-8b6b-4459-8e46-0c5186c22e1a
credentials-file: /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json

ingress:
  - hostname: flipsyncai.com
    service: http://192.168.1.100:80
  - hostname: www.flipsyncai.com
    service: http://192.168.1.100:80
  - hostname: api.flipsyncai.com
    service: http://192.168.1.100:8000
  - hostname: ws.flipsyncai.com
    service: http://192.168.1.100:8000
  - service: http_status:404
EOF

# 4. Create credentials file:
cat > /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json << 'EOF'
{
  "AccountTag": "81ae7b9517d65c92a227e5e0c5d59c7f",
  "TunnelSecret": "NTc5NDBlZmQtMjk2ZC00OWQyLWIwNjktZGE4MTQxMDhlNjcx",
  "TunnelID": "eafc3d89-8b6b-4459-8e46-0c5186c22e1a"
}
EOF

chmod 600 /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json

# 5. Set up DNS routing:
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a flipsyncai.com
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a www.flipsyncai.com
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a api.flipsyncai.com
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a ws.flipsyncai.com

# 6. Start tunnel service:
systemctl enable cloudflared-flipsync
systemctl start cloudflared-flipsync
"""
    
    print(tunnel_commands)
    print("\n✅ Follow these commands to complete the tunnel setup")

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 VM creation completed successfully!")
        setup_cloudflare_tunnel()
        
        print("\n📋 NEXT STEPS:")
        print("1. Access Proxmox web interface: https://proxmox.proxy.equipment")
        print("2. Complete Ubuntu 24.04 installation on VM 100")
        print("3. Configure networking and SSH access")
        print("4. Set up Cloudflare tunnel using the commands above")
        print("5. Deploy FlipSync application to the VM")
    else:
        print("\n❌ VM creation failed. Please check the errors above.")
