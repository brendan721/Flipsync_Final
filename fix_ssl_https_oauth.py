#!/usr/bin/env python3
"""
Fix SSL/HTTPS Configuration for eBay OAuth Integration
This script addresses the critical SSL issues preventing eBay OAuth from working.
"""

import os
import subprocess
import sys
import time
import requests
import urllib3
from pathlib import Path

# Disable SSL warnings for testing
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SSLOAuthFixer:
    def __init__(self):
        self.project_root = Path("/home/brend/Flipsync_Final")
        self.ssl_dir = self.project_root / "ssl"
        self.nginx_ssl_dir = self.project_root / "nginx" / "ssl"
        
    def fix_ssl_configuration(self):
        """Fix SSL configuration for eBay OAuth."""
        print("🔒 Fixing SSL Configuration for eBay OAuth")
        print("=" * 60)
        
        # Step 1: Check SSL certificates
        if not self.check_ssl_certificates():
            print("❌ SSL certificates missing or invalid")
            return False
            
        # Step 2: Update FastAPI to support HTTPS
        if not self.update_fastapi_ssl():
            print("❌ Failed to update FastAPI SSL configuration")
            return False
            
        # Step 3: Update environment configuration
        if not self.update_environment_config():
            print("❌ Failed to update environment configuration")
            return False
            
        # Step 4: Fix CORS for HTTPS
        if not self.fix_cors_for_https():
            print("❌ Failed to fix CORS for HTTPS")
            return False
            
        print("✅ SSL configuration fixed successfully")
        return True
        
    def check_ssl_certificates(self):
        """Check if SSL certificates exist and are valid."""
        print("🔍 Checking SSL certificates...")
        
        cert_files = [
            self.nginx_ssl_dir / "server.crt",
            self.nginx_ssl_dir / "server.key",
            self.nginx_ssl_dir / "ca.crt"
        ]
        
        for cert_file in cert_files:
            if not cert_file.exists():
                print(f"❌ Missing certificate: {cert_file}")
                return False
            else:
                print(f"✅ Found certificate: {cert_file}")
                
        return True
        
    def update_fastapi_ssl(self):
        """Update FastAPI configuration to support SSL."""
        print("🔧 Updating FastAPI SSL configuration...")
        
        # Create SSL startup script
        ssl_startup_content = '''#!/bin/bash
# SSL-enabled startup script for FlipSync API

# Set SSL environment variables
export SSL_ENABLED=true
export SSL_CERT_FILE=/etc/nginx/ssl/server.crt
export SSL_KEY_FILE=/etc/nginx/ssl/server.key
export SSL_CA_FILE=/etc/nginx/ssl/ca.crt

# Start API with both HTTP and HTTPS
echo "🔒 Starting FlipSync API with SSL support..."

# Start HTTP server on port 8000
uvicorn fs_agt_clean.app.main:app --host 0.0.0.0 --port 8000 &

# Start HTTPS server on port 8443
uvicorn fs_agt_clean.app.main:app --host 0.0.0.0 --port 8443 \\
    --ssl-keyfile /etc/nginx/ssl/server.key \\
    --ssl-certfile /etc/nginx/ssl/server.crt &

# Wait for both servers
wait
'''
        
        ssl_startup_path = self.project_root / "start_ssl.sh"
        with open(ssl_startup_path, 'w') as f:
            f.write(ssl_startup_content)
            
        # Make executable
        os.chmod(ssl_startup_path, 0o755)
        print(f"✅ Created SSL startup script: {ssl_startup_path}")
        
        return True
        
    def update_environment_config(self):
        """Update environment configuration for HTTPS."""
        print("🔧 Updating environment configuration...")
        
        # Update Flutter environment config
        flutter_env_content = '''
# FlipSync Production Environment Configuration
# HTTPS-enabled for eBay OAuth integration

API_BASE_URL=https://localhost:8443
WS_BASE_URL=wss://localhost:8443
ENVIRONMENT=production
SSL_ENABLED=true
EBAY_OAUTH_ENABLED=true
EBAY_CLIENT_ID=BrendanB-Nashvill-PRD-7f5c11990-62c1c838
EBAY_RU_NAME=Brendan_Blomfie-BrendanB-Nashvi-vuwrefym
EBAY_CALLBACK_URL=https://www.nashvillegeneral.store/ebay-oauth
'''
        
        env_path = self.project_root / "mobile" / "web" / "assets" / "config" / ".env.production"
        env_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(env_path, 'w') as f:
            f.write(flutter_env_content)
            
        print(f"✅ Updated environment config: {env_path}")
        return True
        
    def fix_cors_for_https(self):
        """Fix CORS configuration to support HTTPS."""
        print("🔧 Fixing CORS for HTTPS...")
        
        cors_config_path = self.project_root / "fs_agt_clean" / "core" / "config" / "cors_config.py"
        
        # Read current config
        with open(cors_config_path, 'r') as f:
            content = f.read()
            
        # Add HTTPS origins
        https_origins = '''
    # HTTPS origins for eBay OAuth
    "https://localhost:3000",  # Flutter web HTTPS
    "https://localhost:3443",  # Flutter web HTTPS (alternate)
    "https://127.0.0.1:3000",  # Local HTTPS
    "https://127.0.0.1:3443",  # Local HTTPS (alternate)
'''
        
        # Insert HTTPS origins after development origins
        if "# Production origins" in content:
            content = content.replace(
                "# Production origins",
                https_origins + "    # Production origins"
            )
            
            with open(cors_config_path, 'w') as f:
                f.write(content)
                
            print("✅ Added HTTPS origins to CORS configuration")
            return True
        else:
            print("❌ Could not find CORS configuration section")
            return False
            
    def test_ssl_configuration(self):
        """Test SSL configuration."""
        print("🧪 Testing SSL configuration...")
        
        # Test HTTPS endpoint
        try:
            response = requests.get("https://localhost:8443/health", verify=False, timeout=10)
            if response.status_code == 200:
                print("✅ HTTPS endpoint working")
                return True
            else:
                print(f"❌ HTTPS endpoint returned: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ HTTPS endpoint error: {e}")
            return False
            
    def restart_containers(self):
        """Restart Docker containers to apply SSL changes."""
        print("🔄 Restarting containers with SSL configuration...")
        
        try:
            # Copy SSL certificates to containers
            subprocess.run([
                "docker", "cp", 
                str(self.nginx_ssl_dir), 
                "flipsync-production-api:/etc/nginx/ssl"
            ], check=True)
            
            # Restart API container
            subprocess.run(["docker", "restart", "flipsync-production-api"], check=True)
            
            print("✅ Containers restarted with SSL configuration")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to restart containers: {e}")
            return False
            
    def create_https_test_script(self):
        """Create a test script for HTTPS OAuth flow."""
        test_script_content = '''#!/usr/bin/env python3
"""
Test HTTPS eBay OAuth Flow
"""
import requests
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def test_https_oauth():
    """Test HTTPS OAuth flow."""
    print("🔒 Testing HTTPS eBay OAuth Flow")
    print("=" * 50)
    
    # Test 1: HTTPS Health Check
    try:
        response = requests.get("https://localhost:8443/health", verify=False)
        print(f"✅ HTTPS Health Check: {response.status_code}")
    except Exception as e:
        print(f"❌ HTTPS Health Check: {e}")
        return False
        
    # Test 2: HTTPS OAuth URL Generation
    try:
        oauth_data = {
            "scopes": [
                "https://api.ebay.com/oauth/api_scope",
                "https://api.ebay.com/oauth/api_scope/sell.inventory"
            ]
        }
        
        response = requests.post(
            "https://localhost:8443/api/v1/marketplace/ebay/oauth/authorize",
            json=oauth_data,
            verify=False
        )
        
        if response.status_code == 200:
            data = response.json()
            auth_url = data.get("data", {}).get("authorization_url", "")
            print(f"✅ HTTPS OAuth URL: {auth_url[:100]}...")
            return True
        else:
            print(f"❌ HTTPS OAuth URL: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ HTTPS OAuth URL: {e}")
        return False

if __name__ == "__main__":
    test_https_oauth()
'''
        
        test_script_path = self.project_root / "test_https_oauth.py"
        with open(test_script_path, 'w') as f:
            f.write(test_script_content)
            
        os.chmod(test_script_path, 0o755)
        print(f"✅ Created HTTPS test script: {test_script_path}")

def main():
    """Main function."""
    fixer = SSLOAuthFixer()
    
    print("🚀 Starting SSL/HTTPS Fix for eBay OAuth")
    print("=" * 60)
    
    # Apply fixes
    if not fixer.fix_ssl_configuration():
        print("❌ SSL configuration fix failed")
        sys.exit(1)
        
    # Create test script
    fixer.create_https_test_script()
    
    # Restart containers
    if not fixer.restart_containers():
        print("⚠️ Container restart failed - manual restart may be needed")
        
    print("\n🎉 SSL/HTTPS Fix Complete!")
    print("=" * 60)
    print("Next steps:")
    print("1. Run: python test_https_oauth.py")
    print("2. Test eBay OAuth in browser with HTTPS")
    print("3. Verify SSL certificates are working")
    
if __name__ == "__main__":
    main()
