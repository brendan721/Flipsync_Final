#!/usr/bin/env python3
"""
Simple CORS fix based on web research.
The issue is likely that the browser sends different headers than curl.
"""

import os
import subprocess
import sys


def apply_simple_cors_fix():
    """Apply a simple CORS fix based on web research."""
    print("🔧 Applying Simple CORS Fix Based on Web Research")
    print("=" * 60)
    
    # Based on research, the issue is often:
    # 1. Missing allow_headers for browser-specific headers
    # 2. Incorrect allow_origins configuration
    # 3. Missing expose_headers
    
    cors_fix = '''
    # Enhanced CORS configuration for browser compatibility
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ],
        allow_credentials=True,
        allow_methods=["*"],  # Allow all methods
        allow_headers=["*"],  # Allow all headers (browser-friendly)
        expose_headers=["*"],  # Expose all headers
        max_age=600,
    )
    '''
    
    # Create a simple patch file
    patch_content = f'''
# Simple CORS fix - replace the existing CORS middleware with browser-friendly config
import re

def fix_cors_in_file(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find and replace the CORS middleware configuration
    cors_pattern = r'app\\.add_middleware\\(\\s*CORSMiddleware,.*?\\)'
    
    new_cors = """app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000", 
            "http://localhost:3001",
            "http://127.0.0.1:3001",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"], 
        expose_headers=["*"],
        max_age=600,
    )"""
    
    content = re.sub(cors_pattern, new_cors, content, flags=re.DOTALL)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    return True

# Apply the fix
fix_cors_in_file("fs_agt_clean/app/main.py")
print("✅ Applied simple CORS fix")
'''
    
    # Write and execute the patch
    with open('cors_patch.py', 'w') as f:
        f.write(patch_content)
    
    result = os.system('python3 cors_patch.py')
    
    if result == 0:
        print("✅ CORS configuration updated")
        return True
    else:
        print("❌ Failed to update CORS configuration")
        return False


def deploy_and_test():
    """Deploy the fix and test it."""
    print("\n🚀 Deploying Simple CORS Fix")
    print("=" * 60)
    
    # Copy to container
    cmd = "docker cp fs_agt_clean/app/main.py flipsync-production-api:/app/fs_agt_clean/app/main.py"
    result = os.system(cmd)
    
    if result != 0:
        print("❌ Failed to copy file to container")
        return False
    
    print("✅ Copied updated file to container")
    
    # Restart container
    print("🔄 Restarting container...")
    restart_result = os.system("docker restart flipsync-production-api")
    
    if restart_result != 0:
        print("❌ Failed to restart container")
        return False
    
    print("✅ Container restarted")
    print("⏳ Waiting for container to be ready...")
    os.system("sleep 30")
    
    # Test CORS
    print("\n🧪 Testing CORS Fix")
    print("=" * 60)
    
    # Test with the exact same headers a browser would send
    test_cmd = [
        "curl", "-v", "-s",
        "-H", "Origin: http://localhost:3000",
        "-H", "Access-Control-Request-Method: GET", 
        "-H", "Access-Control-Request-Headers: content-type,authorization",
        "-H", "User-Agent: Mozilla/5.0 (compatible; FlipSync-Test)",
        "-X", "OPTIONS",
        "http://localhost:8001/api/v1/marketplace/ebay/status/public"
    ]
    
    try:
        result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=15)
        
        if "200 OK" in result.stderr:
            print("✅ CORS preflight test: SUCCESS")
            
            # Test actual request
            get_cmd = [
                "curl", "-s", "-w", "%{http_code}",
                "-H", "Origin: http://localhost:3000",
                "http://localhost:8001/api/v1/marketplace/ebay/status/public"
            ]
            
            get_result = subprocess.run(get_cmd, capture_output=True, text=True, timeout=10)
            
            if "200" in get_result.stdout:
                print("✅ CORS GET request test: SUCCESS")
                return True
            else:
                print(f"❌ CORS GET request test: FAILED ({get_result.stdout})")
                return False
        else:
            print(f"❌ CORS preflight test: FAILED")
            print(f"Response: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ CORS test: TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ CORS test error: {e}")
        return False


def main():
    """Main function."""
    print("🎯 Simple CORS Fix for FlipSync")
    print("=" * 60)
    print("Based on web research, this applies a browser-friendly CORS config")
    print("Key changes:")
    print("- allow_methods=['*'] (instead of specific methods)")
    print("- allow_headers=['*'] (instead of specific headers)")
    print("- expose_headers=['*'] (for browser compatibility)")
    print("- Multiple localhost origins (3000 and 3001)")
    print()
    
    # Step 1: Apply the fix
    if not apply_simple_cors_fix():
        print("❌ Failed to apply CORS fix")
        return 1
    
    # Step 2: Deploy and test
    if deploy_and_test():
        print("\n🎉 SIMPLE CORS FIX SUCCESSFUL!")
        print("=" * 60)
        print("✅ Browser-friendly CORS configuration applied")
        print("✅ All methods and headers allowed")
        print("✅ Multiple localhost origins supported")
        print("✅ Container updated and tested")
        print()
        print("🚀 The Flutter app should now work without CORS errors!")
        print("   Try refreshing the browser and testing the listings page")
        return 0
    else:
        print("\n⚠️  CORS fix applied but test failed")
        print("Please check the container logs for more details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
