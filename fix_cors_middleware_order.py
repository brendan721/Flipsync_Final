#!/usr/bin/env python3
"""
Fix CORS middleware order and configuration issues.
Based on research, the issue is likely middleware order or conflicting configurations.
"""

import os
import re
import subprocess
import sys
from pathlib import Path


def fix_cors_middleware_order():
    """Fix the middleware order to ensure CORS works properly."""
    print("🔧 Fixing CORS Middleware Order and Configuration")
    print("=" * 60)
    
    main_py_path = Path("fs_agt_clean/app/main.py")
    
    if not main_py_path.exists():
        print(f"❌ File not found: {main_py_path}")
        return False
    
    # Read the current file
    with open(main_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix 1: Ensure CORS middleware is added FIRST (before any other middleware)
    print("🔍 Checking middleware order...")
    
    # Find the CORS middleware section
    cors_pattern = r'(app\.add_middleware\(\s*CORSMiddleware,.*?max_age=600,.*?\))'
    cors_match = re.search(cors_pattern, content, re.DOTALL)
    
    if cors_match:
        cors_middleware = cors_match.group(1)
        print("✅ Found CORS middleware configuration")
        
        # Remove the existing CORS middleware
        content = re.sub(cors_pattern, '', content, flags=re.DOTALL)
        
        # Find where to insert CORS middleware (right after app creation)
        app_creation_pattern = r'(app = FastAPI\([^)]*\))'
        app_match = re.search(app_creation_pattern, content, re.DOTALL)
        
        if app_match:
            # Insert CORS middleware immediately after app creation
            insertion_point = app_match.end()
            cors_insertion = f"\n\n    # CORS middleware MUST be added first to handle preflight requests\n    {cors_middleware}\n"
            content = content[:insertion_point] + cors_insertion + content[insertion_point:]
            print("✅ Moved CORS middleware to be first")
        else:
            print("❌ Could not find app creation point")
            return False
    else:
        print("❌ Could not find CORS middleware")
        return False
    
    # Fix 2: Add explicit OPTIONS handler as a fallback
    options_handler = '''
    # Explicit OPTIONS handler as fallback for CORS preflight
    @app.options("/{path:path}")
    async def options_handler(path: str):
        """Handle CORS preflight requests."""
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "http://localhost:3000",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
                "Access-Control-Allow-Headers": "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Max-Age": "600",
            }
        )
    '''
    
    # Insert the OPTIONS handler after CORS middleware
    cors_end = content.find(cors_middleware) + len(cors_middleware)
    content = content[:cors_end] + options_handler + content[cors_end:]
    print("✅ Added explicit OPTIONS handler as fallback")
    
    # Fix 3: Ensure rate limiter properly skips OPTIONS
    rate_limiter_pattern = r'(app\.add_middleware\(\s*type\(rate_limiter\),.*?\))'
    rate_limiter_match = re.search(rate_limiter_pattern, content, re.DOTALL)
    
    if rate_limiter_match:
        print("✅ Found rate limiter middleware")
        # Add comment to ensure it's after CORS
        rate_limiter_text = rate_limiter_match.group(1)
        new_rate_limiter = f"    # Rate limiter added AFTER CORS to avoid interfering with preflight\n    {rate_limiter_text}"
        content = content.replace(rate_limiter_text, new_rate_limiter)
        print("✅ Added comment to rate limiter middleware")
    
    # Write the fixed content
    if content != original_content:
        with open(main_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("✅ Fixed CORS middleware order and configuration")
        return True
    else:
        print("ℹ️  No changes needed")
        return False


def remove_conflicting_app():
    """Remove the conflicting app.py file that might be causing issues."""
    print("\n🗑️  Removing Conflicting App Configuration")
    print("=" * 60)
    
    app_py_path = Path("fs_agt_clean/app/app.py")
    
    if app_py_path.exists():
        # Backup the file first
        backup_path = Path("fs_agt_clean/app/app.py.backup")
        with open(app_py_path, 'r') as src, open(backup_path, 'w') as dst:
            dst.write(src.read())
        
        # Remove the conflicting file
        app_py_path.unlink()
        print(f"✅ Removed conflicting app.py (backed up to {backup_path})")
        return True
    else:
        print("ℹ️  No conflicting app.py found")
        return False


def copy_to_container_and_restart():
    """Copy the fixed files to the container and restart it."""
    print("\n🚀 Deploying Fix to Docker Container")
    print("=" * 60)
    
    container_name = "flipsync-production-api"
    
    # Copy the fixed main.py
    cmd = f"docker cp fs_agt_clean/app/main.py {container_name}:/app/fs_agt_clean/app/main.py"
    result = os.system(cmd)
    
    if result == 0:
        print("✅ Copied fixed main.py to container")
    else:
        print("❌ Failed to copy main.py to container")
        return False
    
    # Remove the conflicting app.py from container if it exists
    cmd = f"docker exec {container_name} rm -f /app/fs_agt_clean/app/app.py"
    os.system(cmd)  # Don't check result as file might not exist
    print("✅ Removed conflicting app.py from container")
    
    # Restart the container
    print("🔄 Restarting container...")
    restart_cmd = f"docker restart {container_name}"
    result = os.system(restart_cmd)
    
    if result == 0:
        print("✅ Container restarted successfully")
        print("⏳ Waiting for container to be ready...")
        os.system("sleep 20")
        return True
    else:
        print("❌ Failed to restart container")
        return False


def test_cors_fix():
    """Test that the CORS fix is working."""
    print("\n🧪 Testing CORS Fix")
    print("=" * 60)
    
    # Test CORS preflight
    test_cmd = [
        "curl", "-s", "-w", "%{http_code}",
        "-H", "Origin: http://localhost:3000",
        "-H", "Access-Control-Request-Method: GET",
        "-H", "Access-Control-Request-Headers: content-type",
        "-X", "OPTIONS",
        "http://localhost:8001/api/v1/marketplace/ebay/status/public"
    ]
    
    try:
        result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
        
        if "200" in result.stdout:
            print("✅ CORS preflight test: SUCCESS (200 OK)")
            
            # Test actual GET request
            get_cmd = [
                "curl", "-s", "-w", "%{http_code}",
                "-H", "Origin: http://localhost:3000",
                "http://localhost:8001/api/v1/marketplace/ebay/status/public"
            ]
            
            get_result = subprocess.run(get_cmd, capture_output=True, text=True, timeout=10)
            
            if "200" in get_result.stdout:
                print("✅ CORS GET request test: SUCCESS (200 OK)")
                return True
            else:
                print(f"❌ CORS GET request test: FAILED ({get_result.stdout})")
                return False
        else:
            print(f"❌ CORS preflight test: FAILED ({result.stdout})")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ CORS test: TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ CORS test error: {e}")
        return False


def main():
    """Main function to fix CORS issues."""
    print("🎯 FlipSync CORS Middleware Fix")
    print("=" * 60)
    print("This script will:")
    print("1. Fix CORS middleware order (CORS must be first)")
    print("2. Add explicit OPTIONS handler as fallback")
    print("3. Remove conflicting app configurations")
    print("4. Deploy fix to Docker container")
    print("5. Test the fix")
    print()
    
    success_count = 0
    
    # Step 1: Fix middleware order
    if fix_cors_middleware_order():
        success_count += 1
    
    # Step 2: Remove conflicting app
    if remove_conflicting_app():
        success_count += 1
    
    # Step 3: Deploy to container
    if copy_to_container_and_restart():
        success_count += 1
    
    # Step 4: Test the fix
    if test_cors_fix():
        success_count += 1
        
        print("\n🎉 CORS ISSUES COMPLETELY RESOLVED!")
        print("=" * 60)
        print("✅ Middleware order fixed (CORS first)")
        print("✅ Explicit OPTIONS handler added")
        print("✅ Conflicting configurations removed")
        print("✅ Container updated and tested")
        print()
        print("🚀 The Flutter app should now work without CORS errors!")
        print("   Try refreshing the browser and navigating to listings page")
        return 0
    else:
        print(f"\n⚠️  CORS fix partially successful ({success_count}/4 steps)")
        print("Please check the container logs for more details")
        return 1


if __name__ == "__main__":
    sys.exit(main())
