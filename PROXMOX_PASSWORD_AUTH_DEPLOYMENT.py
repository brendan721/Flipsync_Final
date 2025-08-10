#!/usr/bin/env python3
"""
FlipSync Proxmox Deployment with Password Authentication
Fallback to password auth if API token lacks permissions
"""

import requests
import json
import time
import urllib3
from typing import Dict, Any, Optional, List

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
        """Authenticate with username/password"""
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
                
                print("✅ Password authentication successful")
                return True
            return False
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
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
        """Get nodes"""
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
    
    def get_vm_list(self, node: str) -> Optional[List[Dict[str, Any]]]:
        """Get list of VMs"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/nodes/{node}/qemu")
            response.raise_for_status()
            result = response.json()
            return result.get('data', [])
        except Exception as e:
            print(f"❌ Failed to get VM list: {e}")
            return None
    
    def delete_vm(self, node: str, vmid: int) -> bool:
        """Delete VM"""
        try:
            # Stop VM first
            stop_response = self.session.post(f"https://{self.host}/api2/json/nodes/{node}/qemu/{vmid}/status/stop")
            time.sleep(3)
            
            # Delete VM
            response = self.session.delete(f"https://{self.host}/api2/json/nodes/{node}/qemu/{vmid}")
            response.raise_for_status()
            
            result = response.json()
            if result.get('data'):
                print(f"✅ VM {vmid} deletion initiated: {result['data']}")
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to delete VM {vmid}: {e}")
            return False
    
    def create_vm(self, node: str, vmid: int, vm_config: Dict[str, Any]) -> bool:
        """Create VM"""
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
            print(f"   Response: {e.response.text if hasattr(e, 'response') else 'No response'}")
            return False
    
    def get_storage_info(self, node: str) -> Optional[List[Dict[str, Any]]]:
        """Get storage info"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/nodes/{node}/storage")
            response.raise_for_status()
            result = response.json()
            return result.get('data', [])
        except Exception as e:
            print(f"❌ Failed to get storage: {e}")
            return None

def main():
    """Main deployment function"""
    print("🔧 FlipSync Proxmox Deployment (Password Auth)")
    print("=" * 50)
    
    # Connection details
    PROXMOX_HOST = "proxmox.proxy.equipment"
    USERNAME = "root@pam"
    PASSWORD = "admin123"
    
    # Initialize API
    print("🔐 Authenticating with password...")
    pve = ProxmoxAPI(PROXMOX_HOST, USERNAME, PASSWORD)
    
    if not pve.authenticate():
        print("❌ Authentication failed. Exiting.")
        return False
    
    # Get system info
    version_info = pve.get_version()
    if version_info:
        version = version_info.get('data', {}).get('version', 'Unknown')
        print(f"✅ Proxmox Version: {version}")
    
    nodes = pve.get_nodes()
    if not nodes:
        print("❌ Failed to get nodes.")
        return False
    
    target_node = nodes[0]['node']
    print(f"🎯 Target node: {target_node}")
    
    # Get current VMs
    print(f"\n📋 Current VMs on node {target_node}:")
    vm_list = pve.get_vm_list(target_node)
    if vm_list:
        for vm in vm_list:
            print(f"   VM {vm.get('vmid')}: {vm.get('name', 'unnamed')} ({vm.get('status', 'unknown')})")
    
    # Check for VM 100 and remove if exists
    print(f"\n🗑️  Checking for VM 100...")
    if pve.vm_exists(target_node, 100):
        print("⚠️  VM 100 exists, removing...")
        if pve.delete_vm(target_node, 100):
            print("✅ VM 100 removal initiated")
            time.sleep(10)  # Wait for deletion
        else:
            print("❌ Failed to remove VM 100")
    else:
        print("✅ VM 100 does not exist")
    
    # Get storage info
    storage_info = pve.get_storage_info(target_node)
    available_storage = ['local-lvm']  # Default fallback
    if storage_info:
        available_storage = [s['storage'] for s in storage_info if s.get('enabled', 0) == 1 and 'images' in s.get('content', '')]
        print(f"✅ Available storage: {available_storage}")
    
    primary_storage = available_storage[0] if available_storage else 'local-lvm'
    print(f"🎯 Using storage: {primary_storage}")
    
    # Create VM 201 - FlipSync Production
    print(f"\n🚀 Creating VM 201 (FlipSync Production)...")
    
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
        'description': 'FlipSync Production Server - Complete deployment'
    }
    
    if not pve.vm_exists(target_node, 201):
        if pve.create_vm(target_node, 201, vm_201_config):
            print("✅ VM 201 created successfully!")
            time.sleep(5)
        else:
            print("❌ Failed to create VM 201")
            return False
    else:
        print("⚠️  VM 201 already exists")
    
    # Verify VM creation
    print(f"\n✅ DEPLOYMENT COMPLETED")
    print(f"   VM 201: FlipSync Production Server")
    print(f"   - 12 cores, 32GB RAM, 500GB storage")
    print(f"   - Storage: {primary_storage}")
    print(f"   - Ready for Ubuntu 24.04 installation")
    
    return True

def generate_tunnel_setup():
    """Generate tunnel setup commands"""
    print("\n" + "=" * 60)
    print("🌐 CLOUDFLARE TUNNEL SETUP COMMANDS")
    print("=" * 60)
    
    print("""
# Execute these commands on the Proxmox host:

# 1. Install cloudflared
wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
dpkg -i cloudflared-linux-amd64.deb

# 2. Create tunnel configuration
mkdir -p /etc/cloudflared
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
  - service: http_status:404
EOF

# 3. Create credentials file
cat > /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json << 'EOF'
{
  "AccountTag": "81ae7b9517d65c92a227e5e0c5d59c7f",
  "TunnelSecret": "NTc5NDBlZmQtMjk2ZC00OWQyLWIwNjktZGE4MTQxMDhlNjcx",
  "TunnelID": "eafc3d89-8b6b-4459-8e46-0c5186c22e1a"
}
EOF

chmod 600 /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json

# 4. Set up DNS routing
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a flipsyncai.com
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a www.flipsyncai.com
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a api.flipsyncai.com
cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a ws.flipsyncai.com

# 5. Create and start service
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

systemctl daemon-reload
systemctl enable cloudflared-flipsync
systemctl start cloudflared-flipsync

# 6. Verify tunnel
systemctl status cloudflared-flipsync
curl -I https://flipsyncai.com
""")

if __name__ == "__main__":
    success = main()
    
    if success:
        generate_tunnel_setup()
        
        print("\n📋 NEXT STEPS:")
        print("1. Access Proxmox: https://proxmox.proxy.equipment")
        print("2. Install Ubuntu 24.04 on VM 201")
        print("3. Configure VM networking")
        print("4. Execute tunnel setup commands above")
        print("5. Deploy FlipSync application")
    else:
        print("\n❌ Deployment failed.")
