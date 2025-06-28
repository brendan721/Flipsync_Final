#!/usr/bin/env python3
"""
Fix CORS issues by removing conflicting manual OPTIONS handlers
and ensuring CORS middleware handles all preflight requests properly.
"""

import os
import re
import sys
from pathlib import Path


def fix_cors_issues():
    """Fix CORS issues in the FlipSync backend."""
    print("🔧 Fixing CORS Issues in FlipSync Backend")
    print("=" * 60)
    
    # Files that need CORS fixes
    files_to_fix = [
        "fs_agt_clean/app/main.py",
        "fs_agt_clean/api/routes/auth.py", 
        "fs_agt_clean/api/routes/agents.py",
        "fs_agt_clean/api/routes/chat.py",
    ]
    
    fixes_applied = 0
    
    for file_path in files_to_fix:
        full_path = Path(file_path)
        if not full_path.exists():
            print(f"⚠️  File not found: {file_path}")
            continue
            
        print(f"\n🔍 Processing: {file_path}")
        
        # Read the file
        with open(full_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Fix 1: Remove manual OPTIONS handlers in route files
        if "routes/" in file_path:
            # Remove @router.options() handlers
            content = re.sub(
                r'@router\.options\([^)]*\)\s*\n\s*async def [^:]+:\s*\n\s*"""[^"]*"""\s*\n\s*return \{"message": "OK"\}',
                '',
                content,
                flags=re.MULTILINE | re.DOTALL
            )
            
            # Remove standalone options functions
            content = re.sub(
                r'\n\n@router\.options\([^)]*\)\s*\nasync def options_[^:]+:\s*\n\s*"""[^"]*"""\s*\n\s*return \{"message": "OK"\}',
                '',
                content,
                flags=re.MULTILINE | re.DOTALL
            )
        
        # Fix 2: Remove manual OPTIONS handlers in main.py
        if "main.py" in file_path:
            # Remove the manual @app.options() handlers that conflict with CORS middleware
            content = re.sub(
                r'@app\.options\([^)]*\)\s*\n\s*async def [^:]+:\s*\n\s*"""[^"]*"""\s*\n[^@]*?return Response\([^)]*\)',
                '',
                content,
                flags=re.MULTILINE | re.DOTALL
            )
        
        # Check if changes were made
        if content != original_content:
            # Write the fixed content back
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed CORS issues in: {file_path}")
            fixes_applied += 1
        else:
            print(f"ℹ️  No CORS fixes needed in: {file_path}")
    
    # Fix 3: Ensure CORS middleware configuration is optimal
    main_py_path = Path("fs_agt_clean/app/main.py")
    if main_py_path.exists():
        print(f"\n🔧 Optimizing CORS middleware configuration...")
        
        with open(main_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check if we need to add max_age to CORS middleware
        if "access-control-max-age" not in content.lower():
            # Find the CORS middleware configuration and add max_age
            cors_pattern = r'(app\.add_middleware\(\s*CORSMiddleware,\s*[^)]*allow_headers=\[[^\]]*\],)'
            
            def add_max_age(match):
                return match.group(1) + '\n        max_age=600,  # Cache preflight requests for 10 minutes'
            
            new_content = re.sub(cors_pattern, add_max_age, content, flags=re.MULTILINE | re.DOTALL)
            
            if new_content != content:
                with open(main_py_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"✅ Added max_age to CORS middleware")
                fixes_applied += 1
    
    print(f"\n📊 CORS Fix Summary")
    print("=" * 60)
    print(f"✅ Files processed: {len(files_to_fix)}")
    print(f"✅ Fixes applied: {fixes_applied}")
    
    if fixes_applied > 0:
        print("\n🔄 Next Steps:")
        print("1. Copy updated files to Docker container")
        print("2. Restart the container to apply changes")
        print("3. Test CORS functionality")
        return True
    else:
        print("\n✅ No CORS fixes were needed")
        return False


def copy_files_to_container():
    """Copy the fixed files to the Docker container."""
    print("\n🚀 Copying Fixed Files to Docker Container")
    print("=" * 60)
    
    files_to_copy = [
        "fs_agt_clean/app/main.py",
        "fs_agt_clean/api/routes/auth.py", 
        "fs_agt_clean/api/routes/agents.py",
        "fs_agt_clean/api/routes/chat.py",
    ]
    
    container_name = "flipsync-production-api"
    
    for file_path in files_to_copy:
        if Path(file_path).exists():
            # Copy file to container
            cmd = f"docker cp {file_path} {container_name}:/app/{file_path}"
            print(f"📁 Copying: {file_path}")
            
            result = os.system(cmd)
            if result == 0:
                print(f"✅ Successfully copied: {file_path}")
            else:
                print(f"❌ Failed to copy: {file_path}")
        else:
            print(f"⚠️  File not found: {file_path}")
    
    print("\n🔄 Restarting container to apply changes...")
    restart_result = os.system(f"docker restart {container_name}")
    
    if restart_result == 0:
        print("✅ Container restarted successfully")
        print("\n⏳ Waiting for container to be ready...")
        os.system("sleep 15")
        return True
    else:
        print("❌ Failed to restart container")
        return False


def test_cors_fix():
    """Test that CORS is working after the fix."""
    print("\n🧪 Testing CORS Fix")
    print("=" * 60)
    
    import subprocess
    
    # Test CORS preflight request
    test_cmd = [
        "curl", "-v", 
        "-H", "Origin: http://localhost:3000",
        "-H", "Access-Control-Request-Method: GET",
        "-H", "Access-Control-Request-Headers: content-type",
        "-X", "OPTIONS",
        "http://localhost:8001/api/v1/marketplace/ebay/status/public"
    ]
    
    try:
        result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
        
        if "200 OK" in result.stderr:
            print("✅ CORS preflight request: SUCCESS (200 OK)")
            
            if "access-control-allow-origin: http://localhost:3000" in result.stderr.lower():
                print("✅ CORS headers: Correct origin allowed")
            else:
                print("⚠️  CORS headers: Origin header missing or incorrect")
                
            return True
        else:
            print(f"❌ CORS preflight request: FAILED")
            print(f"Response: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ CORS test: TIMEOUT")
        return False
    except Exception as e:
        print(f"❌ CORS test error: {e}")
        return False


def main():
    """Main function to fix CORS issues."""
    print("🎯 FlipSync CORS Issue Fix")
    print("=" * 60)
    print("This script will:")
    print("1. Remove conflicting manual OPTIONS handlers")
    print("2. Optimize CORS middleware configuration") 
    print("3. Copy fixed files to Docker container")
    print("4. Restart container and test CORS")
    print()
    
    # Step 1: Fix CORS issues in source files
    fixes_needed = fix_cors_issues()
    
    if fixes_needed:
        # Step 2: Copy files to container
        copy_success = copy_files_to_container()
        
        if copy_success:
            # Step 3: Test the fix
            test_success = test_cors_fix()
            
            if test_success:
                print("\n🎉 CORS ISSUES FIXED SUCCESSFULLY!")
                print("✅ The Flutter app should now be able to make API calls")
                print("✅ eBay inventory integration should work correctly")
                return 0
            else:
                print("\n⚠️  CORS fix applied but test failed")
                print("Please check the container logs for more details")
                return 1
        else:
            print("\n❌ Failed to copy files to container")
            return 1
    else:
        print("\n✅ No CORS fixes were needed")
        print("The issue might be elsewhere - check container logs")
        return 0


if __name__ == "__main__":
    sys.exit(main())
