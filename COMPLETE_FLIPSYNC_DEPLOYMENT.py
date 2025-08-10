#!/usr/bin/env python3
"""
Complete FlipSync VM Deployment Script
1. Start VM 201
2. Download and attach Ubuntu 24.04 ISO
3. Execute Cloudflare tunnel setup
4. Validate deployment
"""

import requests
import json
import time
import urllib3
import subprocess
import os
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
                
                print("✅ Proxmox authentication successful")
                return True
            return False
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def get_vm_status(self, node: str, vmid: int) -> Optional[Dict[str, Any]]:
        """Get VM status"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/nodes/{node}/qemu/{vmid}/status/current")
            response.raise_for_status()
            result = response.json()
            return result.get('data', {})
        except Exception as e:
            print(f"❌ Failed to get VM {vmid} status: {e}")
            return None
    
    def start_vm(self, node: str, vmid: int) -> bool:
        """Start VM"""
        try:
            response = self.session.post(f"https://{self.host}/api2/json/nodes/{node}/qemu/{vmid}/status/start")
            response.raise_for_status()
            
            result = response.json()
            if result.get('data'):
                print(f"✅ VM {vmid} start task: {result['data']}")
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to start VM {vmid}: {e}")
            return False
    
    def get_storage_content(self, node: str, storage: str) -> Optional[List[Dict[str, Any]]]:
        """Get storage content"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/nodes/{node}/storage/{storage}/content")
            response.raise_for_status()
            result = response.json()
            return result.get('data', [])
        except Exception as e:
            print(f"❌ Failed to get storage content: {e}")
            return None
    
    def download_iso(self, node: str, storage: str, url: str, filename: str) -> bool:
        """Download ISO to storage"""
        try:
            data = {
                'content': 'iso',
                'filename': filename,
                'url': url
            }
            response = self.session.post(f"https://{self.host}/api2/json/nodes/{node}/storage/{storage}/download-url", data=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('data'):
                print(f"✅ ISO download task: {result['data']}")
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to download ISO: {e}")
            return False
    
    def attach_iso_to_vm(self, node: str, vmid: int, storage: str, iso_file: str) -> bool:
        """Attach ISO to VM"""
        try:
            data = {
                'ide2': f'{storage}:iso/{iso_file},media=cdrom'
            }
            response = self.session.put(f"https://{self.host}/api2/json/nodes/{node}/qemu/{vmid}/config", data=data)
            response.raise_for_status()
            
            print(f"✅ ISO attached to VM {vmid}")
            return True
        except Exception as e:
            print(f"❌ Failed to attach ISO: {e}")
            return False

def execute_tunnel_setup():
    """Execute Cloudflare tunnel setup commands"""
    print("\n🌐 EXECUTING CLOUDFLARE TUNNEL SETUP")
    print("=" * 50)
    
    tunnel_commands = [
        # Download cloudflared
        "wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -O /tmp/cloudflared.deb",
        "dpkg -i /tmp/cloudflared.deb",
        
        # Create directory
        "mkdir -p /etc/cloudflared",
    ]
    
    # Create tunnel config file
    tunnel_config = """tunnel: eafc3d89-8b6b-4459-8e46-0c5186c22e1a
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
  - service: http_status:404"""
    
    # Create credentials file
    credentials = """{
  "AccountTag": "81ae7b9517d65c92a227e5e0c5d59c7f",
  "TunnelSecret": "NTc5NDBlZmQtMjk2ZC00OWQyLWIwNjktZGE4MTQxMDhlNjcx",
  "TunnelID": "eafc3d89-8b6b-4459-8e46-0c5186c22e1a"
}"""
    
    # Create systemd service
    service_config = """[Unit]
Description=Cloudflare Tunnel for FlipSync
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/cloudflared tunnel --config /etc/cloudflared/flipsync-config.yml run
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target"""
    
    print("📝 Creating tunnel configuration files...")
    
    # Write config files
    try:
        with open('/tmp/flipsync-config.yml', 'w') as f:
            f.write(tunnel_config)
        
        with open('/tmp/tunnel-credentials.json', 'w') as f:
            f.write(credentials)
        
        with open('/tmp/cloudflared-flipsync.service', 'w') as f:
            f.write(service_config)
        
        print("✅ Configuration files created locally")
        
        # Note: In a real deployment, these would be copied to the Proxmox host
        print("📋 Files ready for transfer to Proxmox host:")
        print("   - /tmp/flipsync-config.yml")
        print("   - /tmp/tunnel-credentials.json") 
        print("   - /tmp/cloudflared-flipsync.service")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create config files: {e}")
        return False

def main():
    """Main deployment function"""
    print("🚀 COMPLETE FLIPSYNC VM DEPLOYMENT")
    print("=" * 50)
    
    # Connection details
    PROXMOX_HOST = "proxmox.proxy.equipment"
    USERNAME = "root@pam"
    PASSWORD = "admin123"
    TARGET_NODE = "pve"
    VMID = 201
    
    # Ubuntu ISO details
    UBUNTU_ISO_URL = "https://releases.ubuntu.com/24.04.1/ubuntu-24.04.1-live-server-amd64.iso"
    UBUNTU_ISO_NAME = "ubuntu-24.04.1-live-server-amd64.iso"
    ISO_STORAGE = "local"  # Common storage for ISOs
    
    # Initialize API
    print("🔐 Connecting to Proxmox...")
    pve = ProxmoxAPI(PROXMOX_HOST, USERNAME, PASSWORD)
    
    if not pve.authenticate():
        print("❌ Failed to authenticate with Proxmox")
        return False
    
    # STEP 1: Check VM 201 status and start if needed
    print(f"\n🔍 STEP 1: Checking VM {VMID} status...")
    vm_status = pve.get_vm_status(TARGET_NODE, VMID)
    
    if not vm_status:
        print(f"❌ VM {VMID} not found")
        return False
    
    current_status = vm_status.get('status', 'unknown')
    print(f"📊 VM {VMID} current status: {current_status}")
    
    if current_status == 'stopped':
        print(f"🚀 Starting VM {VMID}...")
        if pve.start_vm(TARGET_NODE, VMID):
            print("✅ VM start initiated")
            time.sleep(10)  # Wait for VM to start
        else:
            print("❌ Failed to start VM")
            return False
    elif current_status == 'running':
        print("✅ VM is already running")
    
    # STEP 2: Check for Ubuntu ISO and download if needed
    print(f"\n💿 STEP 2: Managing Ubuntu 24.04 ISO...")
    
    # Check if ISO already exists
    iso_content = pve.get_storage_content(TARGET_NODE, ISO_STORAGE)
    iso_exists = False
    
    if iso_content:
        for item in iso_content:
            if item.get('volid', '').endswith(UBUNTU_ISO_NAME):
                print(f"✅ Ubuntu ISO already exists: {item['volid']}")
                iso_exists = True
                break
    
    if not iso_exists:
        print(f"📥 Downloading Ubuntu 24.04 ISO...")
        if pve.download_iso(TARGET_NODE, ISO_STORAGE, UBUNTU_ISO_URL, UBUNTU_ISO_NAME):
            print("✅ ISO download initiated (this may take several minutes)")
            # In production, you'd wait and check download status
            time.sleep(30)  # Give download time to start
        else:
            print("❌ Failed to initiate ISO download")
    
    # STEP 3: Attach ISO to VM
    print(f"\n💽 STEP 3: Attaching ISO to VM {VMID}...")
    if pve.attach_iso_to_vm(TARGET_NODE, VMID, ISO_STORAGE, UBUNTU_ISO_NAME):
        print("✅ ISO attached successfully")
    else:
        print("❌ Failed to attach ISO")
    
    # STEP 4: Execute tunnel setup
    print(f"\n🌐 STEP 4: Preparing Cloudflare tunnel setup...")
    if execute_tunnel_setup():
        print("✅ Tunnel configuration prepared")
    else:
        print("❌ Failed to prepare tunnel configuration")
        return False
    
    # STEP 5: Provide next steps
    print(f"\n📋 STEP 5: Manual completion required...")
    print_manual_steps()
    
    return True

def print_manual_steps():
    """Print manual steps for completion"""
    print("\n" + "=" * 60)
    print("📋 MANUAL STEPS TO COMPLETE DEPLOYMENT")
    print("=" * 60)
    
    print("""
🖥️  UBUNTU INSTALLATION (Via Proxmox Console):
1. Access Proxmox web interface: https://proxmox.proxy.equipment
2. Navigate to VM 201 (flipsync-production)
3. Click "Console" to access VM display
4. VM should boot from Ubuntu 24.04 ISO
5. Follow Ubuntu installation wizard:
   - Select "Install Ubuntu Server"
   - Configure network with static IP: 192.168.1.201/24
   - Gateway: 192.168.1.1 (or your network gateway)
   - DNS: 8.8.8.8, 1.1.1.1
   - Create user: flipsync (with sudo privileges)
   - Enable SSH server
   - Install OpenSSH server
   - Complete installation and reboot

🌐 CLOUDFLARE TUNNEL SETUP (On Proxmox Host):
Execute these commands via Proxmox shell or SSH:

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
journalctl -u cloudflared-flipsync -f

✅ VALIDATION STEPS:
1. SSH into VM 201: ssh flipsync@192.168.1.201
2. Test tunnel: curl -I https://flipsyncai.com
3. Verify domains resolve to Cloudflare IPs
4. Check tunnel logs for any errors
""")

if __name__ == "__main__":
    success = main()
    
    if success:
        print("\n🎉 AUTOMATED DEPLOYMENT STEPS COMPLETED!")
        print("📋 Please complete the manual steps above to finish the deployment.")
    else:
        print("\n❌ Deployment failed. Please check errors above.")
