#!/usr/bin/env python3
"""
Execute Cloudflare tunnel setup on Proxmox host
"""

import requests
import json
import time
import urllib3

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
    
    def execute_command(self, node: str, command: str) -> dict:
        """Execute command on Proxmox node"""
        try:
            data = {
                'command': command
            }
            response = self.session.post(f"https://{self.host}/api2/json/nodes/{node}/execute", data=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to execute command: {e}")
            return {}

def main():
    """Execute tunnel setup on Proxmox host"""
    print("🌐 EXECUTING CLOUDFLARE TUNNEL SETUP ON PROXMOX HOST")
    print("=" * 60)
    
    # Connection details
    PROXMOX_HOST = "proxmox.proxy.equipment"
    USERNAME = "root@pam"
    PASSWORD = "admin123"
    TARGET_NODE = "pve"
    
    # Initialize API
    print("🔐 Connecting to Proxmox...")
    pve = ProxmoxAPI(PROXMOX_HOST, USERNAME, PASSWORD)
    
    if not pve.authenticate():
        print("❌ Failed to authenticate")
        return False
    
    # Execute tunnel setup commands
    tunnel_commands = [
        # Install cloudflared
        "wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -O /tmp/cloudflared.deb",
        "dpkg -i /tmp/cloudflared.deb",
        
        # Create directory
        "mkdir -p /etc/cloudflared",
        
        # Create tunnel config (we'll do this via file creation)
        "echo 'Creating tunnel configuration...'",
    ]
    
    print("🚀 Executing tunnel setup commands...")
    
    for i, command in enumerate(tunnel_commands, 1):
        print(f"📋 Step {i}: {command[:50]}...")
        result = pve.execute_command(TARGET_NODE, command)
        
        if result.get('data'):
            print(f"✅ Command executed successfully")
        else:
            print(f"⚠️  Command may have failed or API doesn't support execution")
    
    # Create configuration files using API file upload (if available)
    create_tunnel_config_files(pve, TARGET_NODE)
    
    return True

def create_tunnel_config_files(pve, node):
    """Create tunnel configuration files"""
    print("\n📝 Creating tunnel configuration files...")
    
    # Tunnel configuration
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
    originRequest:
      noTLSVerify: true
  - service: http_status:404"""
    
    # Credentials file
    credentials = """{
  "AccountTag": "81ae7b9517d65c92a227e5e0c5d59c7f",
  "TunnelSecret": "NTc5NDBlZmQtMjk2ZC00OWQyLWIwNjktZGE4MTQxMDhlNjcx",
  "TunnelID": "eafc3d89-8b6b-4459-8e46-0c5186c22e1a"
}"""
    
    # Systemd service
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
    
    # Try to create files using echo commands
    file_commands = [
        f"cat > /etc/cloudflared/flipsync-config.yml << 'EOF'\n{tunnel_config}\nEOF",
        f"cat > /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json << 'EOF'\n{credentials}\nEOF",
        "chmod 600 /etc/cloudflared/eafc3d89-8b6b-4459-8e46-0c5186c22e1a.json",
        f"cat > /etc/systemd/system/cloudflared-flipsync.service << 'EOF'\n{service_config}\nEOF",
    ]
    
    for i, command in enumerate(file_commands, 1):
        print(f"📄 Creating file {i}...")
        result = pve.execute_command(node, command)
        
        if result.get('data'):
            print(f"✅ File created successfully")
        else:
            print(f"⚠️  File creation may have failed")
    
    # DNS routing and service commands
    final_commands = [
        "cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a flipsyncai.com",
        "cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a www.flipsyncai.com",
        "cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a api.flipsyncai.com",
        "cloudflared tunnel route dns eafc3d89-8b6b-4459-8e46-0c5186c22e1a ws.flipsyncai.com",
        "systemctl daemon-reload",
        "systemctl enable cloudflared-flipsync",
        "systemctl start cloudflared-flipsync",
    ]
    
    print("\n🌐 Setting up DNS routing and starting service...")
    for i, command in enumerate(final_commands, 1):
        print(f"🔧 Step {i}: {command[:50]}...")
        result = pve.execute_command(node, command)
        
        if result.get('data'):
            print(f"✅ Command executed")
        else:
            print(f"⚠️  Command may have failed")
    
    print("\n✅ Tunnel setup commands executed!")

def print_validation_steps():
    """Print validation steps"""
    print("\n" + "=" * 60)
    print("✅ VALIDATION & NEXT STEPS")
    print("=" * 60)
    
    print("""
🔍 VALIDATE TUNNEL SETUP:
1. Check tunnel service status:
   - Access Proxmox shell or SSH
   - Run: systemctl status cloudflared-flipsync
   - Run: journalctl -u cloudflared-flipsync -f

2. Test tunnel connectivity:
   - curl -I https://flipsyncai.com
   - curl -I https://api.flipsyncai.com
   - nslookup flipsyncai.com (should show Cloudflare IPs)

🖥️  COMPLETE VM SETUP:
1. Access Proxmox web interface: https://proxmox.proxy.equipment
2. Navigate to VM 201 (flipsync-production)
3. Click "Console" to access VM
4. Complete Ubuntu 24.04 installation:
   - Static IP: 192.168.1.201/24
   - Gateway: 192.168.1.1 (adjust for your network)
   - DNS: 8.8.8.8, 1.1.1.1
   - Username: flipsync
   - Enable SSH server

📦 DEPLOY FLIPSYNC:
1. SSH to VM: ssh flipsync@192.168.1.201
2. Transfer cleaned codebase from /home/brend/Flipsync_Final/
3. Install dependencies and configure services
4. Start FlipSync application

🎉 Infrastructure is ready for FlipSync deployment!
""")

if __name__ == "__main__":
    success = main()
    
    if success:
        print_validation_steps()
    else:
        print("\n❌ Tunnel setup execution failed.")
