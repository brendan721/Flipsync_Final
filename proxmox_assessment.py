#!/usr/bin/env python3
"""
Proxmox Assessment Script - Check current state and connectivity
"""

import requests
import json
import urllib3
from typing import Dict, Any, Optional

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class ProxmoxAssessment:
    def __init__(self):
        self.primary_host = "proxmox.proxy.equipment"
        self.backup_host = "192.168.110.14:8006"
        self.username = "root@pam"
        self.password = "admin123"
        self.api_token_id = "root@pam!llm"
        self.api_token_secret = "40702b1d-8c02-4a8b-b650-561ca2794aa7"
        self.session = requests.Session()
        self.session.verify = False
        self.authenticated_host = None
        self.ticket = None
        self.csrf_token = None

    def test_connectivity(self, host: str) -> bool:
        """Test basic connectivity to Proxmox host"""
        try:
            print(f"🔍 Testing connectivity to {host}...")
            response = self.session.get(f"https://{host}/api2/json/version", timeout=10)
            if response.status_code == 200:
                print(f"✅ Successfully connected to {host}")
                return True
            elif response.status_code == 401:
                print(f"✅ Host {host} is reachable (authentication required)")
                return True
            else:
                print(f"❌ Connection failed to {host}: HTTP {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Connection failed to {host}: {e}")
            return False

    def authenticate_password(self, host: str) -> bool:
        """Authenticate using username/password"""
        try:
            print(f"🔐 Attempting password authentication to {host}...")
            auth_url = f"https://{host}/api2/json/access/ticket"
            auth_data = {"username": self.username, "password": self.password}

            response = self.session.post(auth_url, data=auth_data, timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("data"):
                self.ticket = result["data"]["ticket"]
                self.csrf_token = result["data"]["CSRFPreventionToken"]

                # Set authentication headers
                self.session.headers.update(
                    {
                        "Cookie": f"PVEAuthCookie={self.ticket}",
                        "CSRFPreventionToken": self.csrf_token,
                    }
                )

                print(f"✅ Password authentication successful to {host}")
                self.authenticated_host = host
                return True
            else:
                print(
                    f"❌ Password authentication failed to {host}: No data in response"
                )
                return False

        except Exception as e:
            print(f"❌ Password authentication failed to {host}: {e}")
            return False

    def authenticate_token(self, host: str) -> bool:
        """Authenticate using API token"""
        try:
            print(f"🔑 Attempting token authentication to {host}...")

            # Set token authentication headers
            self.session.headers.update(
                {
                    "Authorization": f"PVEAPIToken={self.api_token_id}={self.api_token_secret}"
                }
            )

            # Test with a simple API call
            response = self.session.get(f"https://{host}/api2/json/version", timeout=10)
            response.raise_for_status()

            result = response.json()
            if result.get("data"):
                print(f"✅ Token authentication successful to {host}")
                self.authenticated_host = host
                return True
            else:
                print(f"❌ Token authentication failed to {host}")
                return False

        except Exception as e:
            print(f"❌ Token authentication failed to {host}: {e}")
            return False

    def get_cluster_info(self) -> Optional[Dict[str, Any]]:
        """Get cluster information"""
        if not self.authenticated_host:
            return None

        try:
            response = self.session.get(
                f"https://{self.authenticated_host}/api2/json/cluster/status"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to get cluster info: {e}")
            return None

    def get_nodes(self) -> Optional[Dict[str, Any]]:
        """Get list of nodes"""
        if not self.authenticated_host:
            return None

        try:
            response = self.session.get(
                f"https://{self.authenticated_host}/api2/json/nodes"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to get nodes: {e}")
            return None

    def get_vms(self, node: str) -> Optional[Dict[str, Any]]:
        """Get list of VMs on a node"""
        if not self.authenticated_host:
            return None

        try:
            response = self.session.get(
                f"https://{self.authenticated_host}/api2/json/nodes/{node}/qemu"
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Failed to get VMs for node {node}: {e}")
            return None

    def check_vm_201(self, node: str) -> Optional[Dict[str, Any]]:
        """Check if VM 201 exists"""
        if not self.authenticated_host:
            return None

        try:
            response = self.session.get(
                f"https://{self.authenticated_host}/api2/json/nodes/{node}/qemu/201/status/current"
            )
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 500:
                # VM doesn't exist
                return None
            else:
                response.raise_for_status()
        except Exception as e:
            print(f"ℹ️  VM 201 does not exist on node {node}")
            return None

    def assess_environment(self):
        """Complete environment assessment"""
        print("🚀 FlipSync Proxmox Environment Assessment")
        print("=" * 60)

        # Test connectivity to both hosts
        primary_connected = self.test_connectivity(self.primary_host)
        backup_connected = self.test_connectivity(self.backup_host)

        if not primary_connected and not backup_connected:
            print("❌ Cannot connect to either Proxmox host")
            return False

        # Try authentication with primary host first
        authenticated = False
        if primary_connected:
            if self.authenticate_password(self.primary_host):
                authenticated = True
            elif self.authenticate_token(self.primary_host):
                authenticated = True

        # Try backup host if primary failed
        if not authenticated and backup_connected:
            if self.authenticate_password(self.backup_host):
                authenticated = True
            elif self.authenticate_token(self.backup_host):
                authenticated = True

        if not authenticated:
            print("❌ Failed to authenticate with any method")
            return False

        print(f"\n📊 Successfully authenticated to: {self.authenticated_host}")

        # Get cluster information
        print("\n🔍 Gathering cluster information...")
        cluster_info = self.get_cluster_info()
        if cluster_info:
            print(f"✅ Cluster status retrieved")

        # Get nodes
        nodes_info = self.get_nodes()
        if not nodes_info or not nodes_info.get("data"):
            print("❌ Failed to get node information")
            return False

        nodes = nodes_info["data"]
        print(f"✅ Found {len(nodes)} node(s):")
        for node in nodes:
            print(f"   - {node['node']} (status: {node.get('status', 'unknown')})")

        # Check VMs on each node
        print("\n🖥️  Checking existing VMs...")
        for node in nodes:
            node_name = node["node"]
            print(f"\n📋 VMs on node '{node_name}':")

            vms_info = self.get_vms(node_name)
            if vms_info and vms_info.get("data"):
                vms = vms_info["data"]
                print(f"   Found {len(vms)} VM(s):")
                for vm in vms:
                    vmid = vm.get("vmid", "unknown")
                    name = vm.get("name", "unnamed")
                    status = vm.get("status", "unknown")
                    print(f"   - VM {vmid}: {name} (status: {status})")
            else:
                print("   No VMs found")

            # Specifically check for VM 201
            vm_201_status = self.check_vm_201(node_name)
            if vm_201_status:
                print(f"⚠️  VM 201 exists on node {node_name}")
                vm_data = vm_201_status.get("data", {})
                print(f"   Status: {vm_data.get('status', 'unknown')}")
                print(f"   Memory: {vm_data.get('mem', 0)} bytes")
                print(f"   CPU: {vm_data.get('cpu', 0)}")
            else:
                print(
                    f"✅ VM 201 does not exist on node {node_name} - ready for creation"
                )

        return True


def main():
    assessor = ProxmoxAssessment()
    success = assessor.assess_environment()

    if success:
        print("\n🎉 Environment assessment completed successfully!")
        print("\n📋 NEXT STEPS:")
        print("1. VM 201 creation is ready to proceed")
        print("2. Ubuntu 24.04 ISO download and attachment")
        print("3. VM configuration with proper specifications")
        print("4. Network setup and Cloudflare tunnel configuration")
    else:
        print("\n❌ Environment assessment failed")
        print("Please check connectivity and credentials")


if __name__ == "__main__":
    main()
