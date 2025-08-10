#!/usr/bin/env python3
"""
Fix VM 201 Boot Issue - Attach ISO and Fix Boot Order
The VM is stuck in boot loop because ISO isn't properly attached
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
                
                print("✅ Proxmox authentication successful")
                return True
            return False
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            return False
    
    def get_vm_config(self, node: str, vmid: int):
        """Get VM configuration"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/nodes/{node}/qemu/{vmid}/config")
            response.raise_for_status()
            result = response.json()
            return result.get('data', {})
        except Exception as e:
            print(f"❌ Failed to get VM config: {e}")
            return {}
    
    def stop_vm(self, node: str, vmid: int) -> bool:
        """Stop VM"""
        try:
            response = self.session.post(f"https://{self.host}/api2/json/nodes/{node}/qemu/{vmid}/status/stop")
            if response.status_code in [200, 500]:  # 500 might mean already stopped
                print(f"✅ VM {vmid} stop command sent")
                return True
            return False
        except Exception as e:
            print(f"❌ Failed to stop VM: {e}")
            return False
    
    def update_vm_config(self, node: str, vmid: int, config: dict) -> bool:
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
            print(f"❌ Failed to start VM: {e}")
            return False
    
    def get_storage_content(self, node: str, storage: str):
        """Get storage content to find ISO"""
        try:
            response = self.session.get(f"https://{self.host}/api2/json/nodes/{node}/storage/{storage}/content")
            response.raise_for_status()
            result = response.json()
            return result.get('data', [])
        except Exception as e:
            print(f"❌ Failed to get storage content: {e}")
            return []

def fix_vm_boot_issue():
    """Fix VM 201 boot issue by properly attaching ISO and fixing boot order"""
    print("🔧 FIXING VM 201 BOOT ISSUE")
    print("=" * 50)
    
    # Connection details
    PROXMOX_HOST = "proxmox.proxy.equipment"
    USERNAME = "root@pam"
    PASSWORD = "admin123"
    TARGET_NODE = "pve"
    VMID = 201
    
    # Initialize API
    pve = ProxmoxAPI(PROXMOX_HOST, USERNAME, PASSWORD)
    
    if not pve.authenticate():
        print("❌ Failed to authenticate")
        return False
    
    # Step 1: Stop the VM
    print(f"\n🛑 Step 1: Stopping VM {VMID}...")
    pve.stop_vm(TARGET_NODE, VMID)
    time.sleep(10)  # Wait for VM to stop
    
    # Step 2: Get current VM configuration
    print(f"\n📋 Step 2: Checking current VM configuration...")
    vm_config = pve.get_vm_config(TARGET_NODE, VMID)
    
    if vm_config:
        print("Current configuration:")
        for key, value in vm_config.items():
            if key in ['boot', 'ide2', 'scsi0', 'net0']:
                print(f"   {key}: {value}")
    
    # Step 3: Find Ubuntu ISO
    print(f"\n💿 Step 3: Finding Ubuntu ISO...")
    iso_found = None
    
    # Check different storage locations
    storage_locations = ['local', 'local-lvm', 'vm-storage']
    
    for storage in storage_locations:
        print(f"   Checking storage: {storage}")
        content = pve.get_storage_content(TARGET_NODE, storage)
        
        for item in content:
            volid = item.get('volid', '')
            if 'ubuntu' in volid.lower() and ('24.04' in volid or '2404' in volid):
                iso_found = volid
                print(f"✅ Found Ubuntu ISO: {iso_found}")
                break
        
        if iso_found:
            break
    
    if not iso_found:
        print("❌ Ubuntu ISO not found. Let's download it...")
        # Try to download Ubuntu ISO
        download_success = download_ubuntu_iso(pve, TARGET_NODE)
        if not download_success:
            return False
        
        # Check again for the ISO
        content = pve.get_storage_content(TARGET_NODE, 'local')
        for item in content:
            volid = item.get('volid', '')
            if 'ubuntu' in volid.lower() and '24.04' in volid:
                iso_found = volid
                break
    
    # Step 4: Update VM configuration with proper ISO and boot order
    print(f"\n🔧 Step 4: Updating VM configuration...")
    
    if iso_found:
        # Configuration to fix boot issue
        new_config = {
            'ide2': f'{iso_found},media=cdrom',
            'boot': 'order=ide2;scsi0',  # Boot from CD first, then disk
        }
        
        print(f"   Attaching ISO: {iso_found}")
        print(f"   Setting boot order: CD first, then disk")
        
        if pve.update_vm_config(TARGET_NODE, VMID, new_config):
            print("✅ VM configuration updated successfully")
        else:
            print("❌ Failed to update VM configuration")
            return False
    else:
        print("❌ No Ubuntu ISO found, cannot fix boot issue")
        return False
    
    # Step 5: Start VM
    print(f"\n🚀 Step 5: Starting VM {VMID}...")
    if pve.start_vm(TARGET_NODE, VMID):
        print("✅ VM started successfully")
        print("\n📋 VM should now boot from Ubuntu ISO")
        print("   Access console: https://proxmox.proxy.equipment")
        print("   Navigate to VM 201 > Console")
        return True
    else:
        print("❌ Failed to start VM")
        return False

def download_ubuntu_iso(pve, node):
    """Download Ubuntu 24.04 ISO if not found"""
    print("📥 Downloading Ubuntu 24.04 ISO...")
    
    ubuntu_url = "https://releases.ubuntu.com/24.04.1/ubuntu-24.04.1-live-server-amd64.iso"
    iso_name = "ubuntu-24.04.1-live-server-amd64.iso"
    
    try:
        data = {
            'content': 'iso',
            'filename': iso_name,
            'url': ubuntu_url
        }
        
        response = pve.session.post(f"https://{pve.host}/api2/json/nodes/{node}/storage/local/download-url", data=data)
        response.raise_for_status()
        
        result = response.json()
        if result.get('data'):
            print(f"✅ Ubuntu ISO download started: {result['data']}")
            print("⏳ Download may take several minutes...")
            time.sleep(60)  # Wait for download to progress
            return True
        else:
            print("❌ Failed to start ISO download")
            return False
            
    except Exception as e:
        print(f"❌ Failed to download ISO: {e}")
        return False

def main():
    """Main function"""
    print("🚀 FIXING FLIPSYNC VM BOOT ISSUE")
    print("=" * 50)
    print("Issue: VM is stuck in boot loop - 'Boot failed: not a bootable disk'")
    print("Solution: Properly attach Ubuntu ISO and fix boot order")
    print("")
    
    success = fix_vm_boot_issue()
    
    if success:
        print("\n🎉 VM BOOT ISSUE FIXED!")
        print("\n📋 NEXT STEPS:")
        print("1. Access VM console: https://proxmox.proxy.equipment")
        print("2. Navigate to VM 201 (flipsync-production)")
        print("3. Click 'Console' - VM should now boot from Ubuntu ISO")
        print("4. Install Ubuntu 24.04 with static IP: 192.168.1.201")
        print("5. Complete the FlipSync deployment")
        
        print("\n✅ The VM should now boot properly from the Ubuntu ISO!")
    else:
        print("\n❌ Failed to fix VM boot issue")
        print("Manual steps required:")
        print("1. Access Proxmox web interface")
        print("2. Stop VM 201")
        print("3. Edit VM > Hardware > Add CD/DVD Drive")
        print("4. Select Ubuntu 24.04 ISO")
        print("5. Edit VM > Options > Boot Order")
        print("6. Set CD/DVD as first boot device")
        print("7. Start VM")

if __name__ == "__main__":
    main()
