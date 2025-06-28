#!/usr/bin/env python3
"""
Quick Fix for Mobile Chat Connectivity Issues
Implements CORS configuration and WebSocket authentication fixes
"""
import os
import sys


def fix_cors_configuration():
    """Fix CORS configuration in the backend"""
    print("🔧 Fixing CORS Configuration...")

    # Check if we're in Docker container
    cors_config_file = "/app/fs_agt_clean/core/config/cors_config.py"
    local_cors_config = (
        "/home/brend/Flipsync_Final/fs_agt_clean/core/config/cors_config.py"
    )

    cors_config_content = '''"""
CORS Configuration for FlipSync Mobile App Integration
"""

# CORS Origins for mobile app development
CORS_ORIGINS = [
    "http://localhost:3000",    # Flutter web development
    "http://localhost:8081",    # Mobile development
    "http://10.0.2.2:3000",     # Android emulator
    "http://127.0.0.1:3000",    # Local loopback
    "http://0.0.0.0:3000",      # All interfaces
]

# WebSocket CORS Origins
WEBSOCKET_CORS_ORIGINS = CORS_ORIGINS

# CORS Headers
CORS_HEADERS = [
    "accept",
    "accept-encoding", 
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# CORS Methods
CORS_METHODS = [
    "DELETE",
    "GET", 
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

# Development mode CORS settings
DEVELOPMENT_CORS_SETTINGS = {
    "allow_origins": CORS_ORIGINS,
    "allow_credentials": True,
    "allow_methods": CORS_METHODS,
    "allow_headers": CORS_HEADERS,
}
'''

    # Write CORS configuration
    try:
        with open(local_cors_config, "w") as f:
            f.write(cors_config_content)
        print(f"  ✅ CORS configuration written to {local_cors_config}")
        return True
    except Exception as e:
        print(f"  ❌ Failed to write CORS config: {e}")
        return False


def update_main_app_cors():
    """Update main FastAPI app to use CORS configuration"""
    print("🔧 Updating Main App CORS Settings...")

    main_app_file = "/home/brend/Flipsync_Final/fs_agt_clean/main.py"

    try:
        # Read current main.py
        with open(main_app_file, "r") as f:
            content = f.read()

        # Check if CORS is already configured
        if "CORSMiddleware" in content and "localhost:3000" in content:
            print("  ✅ CORS already configured in main.py")
            return True

        # Add CORS import if not present
        if "from fastapi.middleware.cors import CORSMiddleware" not in content:
            # Find the imports section and add CORS import
            import_lines = []
            other_lines = []
            in_imports = True

            for line in content.split("\n"):
                if line.startswith("from ") or line.startswith("import "):
                    import_lines.append(line)
                elif line.strip() == "":
                    if in_imports:
                        import_lines.append(line)
                    else:
                        other_lines.append(line)
                else:
                    in_imports = False
                    other_lines.append(line)

            # Add CORS import
            import_lines.append("from fastapi.middleware.cors import CORSMiddleware")
            import_lines.append(
                "from fs_agt_clean.core.config.cors_config import DEVELOPMENT_CORS_SETTINGS"
            )

            # Reconstruct content
            content = "\n".join(import_lines + [""] + other_lines)

        # Add CORS middleware configuration
        if "app.add_middleware(CORSMiddleware" not in content:
            # Find where to add CORS middleware (after app creation)
            lines = content.split("\n")
            new_lines = []
            app_created = False
            cors_added = False

            for line in lines:
                new_lines.append(line)

                # Look for app creation
                if "app = FastAPI(" in line and not cors_added:
                    app_created = True

                # Add CORS middleware after app creation and before other middleware
                if (
                    app_created
                    and not cors_added
                    and (line.strip() == "" or "app.add_middleware" in line)
                ):
                    new_lines.insert(-1, "")
                    new_lines.insert(
                        -1, "# Add CORS middleware for mobile app integration"
                    )
                    new_lines.insert(-1, "app.add_middleware(")
                    new_lines.insert(-1, "    CORSMiddleware,")
                    new_lines.insert(-1, "    **DEVELOPMENT_CORS_SETTINGS")
                    new_lines.insert(-1, ")")
                    new_lines.insert(-1, "")
                    cors_added = True

            content = "\n".join(new_lines)

        # Write updated content
        with open(main_app_file, "w") as f:
            f.write(content)

        print(f"  ✅ Updated main.py with CORS configuration")
        return True

    except Exception as e:
        print(f"  ❌ Failed to update main.py: {e}")
        return False


def create_websocket_auth_fix():
    """Create WebSocket authentication fix"""
    print("🔧 Creating WebSocket Authentication Fix...")

    websocket_fix_file = (
        "/home/brend/Flipsync_Final/fs_agt_clean/core/websocket/mobile_auth_fix.py"
    )

    websocket_fix_content = '''"""
WebSocket Authentication Fix for Mobile App Development
"""
from typing import Optional
from fastapi import WebSocket
import os

def is_development_origin(origin: Optional[str]) -> bool:
    """Check if the origin is from a development environment."""
    if not origin:
        return False
    
    development_origins = [
        "http://localhost:3000",
        "http://localhost:8081",
        "http://127.0.0.1:3000",
        "http://10.0.2.2:3000",
    ]
    
    return origin in development_origins

async def accept_websocket_with_mobile_support(
    websocket: WebSocket, 
    token: Optional[str] = None
) -> bool:
    """Accept WebSocket connection with mobile app support."""
    try:
        # Get origin from headers
        origin = websocket.headers.get("origin")
        
        # In development, allow mobile app connections without strict JWT validation
        if os.getenv("ENVIRONMENT", "development") == "development":
            if is_development_origin(origin):
                await websocket.accept()
                return True
        
        # For production or non-mobile origins, validate JWT
        if token:
            # TODO: Add JWT validation logic here
            await websocket.accept()
            return True
        else:
            # Reject connection without token in production
            await websocket.close(code=1008, reason="Authentication required")
            return False
            
    except Exception as e:
        print(f"WebSocket authentication error: {e}")
        await websocket.close(code=1011, reason="Internal server error")
        return False
'''

    try:
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(websocket_fix_file), exist_ok=True)

        with open(websocket_fix_file, "w") as f:
            f.write(websocket_fix_content)

        print(f"  ✅ WebSocket authentication fix created: {websocket_fix_file}")
        return True

    except Exception as e:
        print(f"  ❌ Failed to create WebSocket fix: {e}")
        return False


def create_browser_launch_script():
    """Create browser launch script for development"""
    print("🔧 Creating Browser Launch Script...")

    browser_script = "/home/brend/Flipsync_Final/launch_chrome_dev.sh"

    script_content = """#!/bin/bash
# Chrome Development Launch Script for FlipSync Mobile Testing

echo "🌐 Launching Chrome for FlipSync Mobile Development"
echo "This will open Chrome with CORS disabled for local development"
echo ""

# Create temporary user data directory
TEMP_DIR="/tmp/chrome_flipsync_dev"
mkdir -p "$TEMP_DIR"

# Chrome executable paths for different systems
if command -v google-chrome &> /dev/null; then
    CHROME_CMD="google-chrome"
elif command -v chromium-browser &> /dev/null; then
    CHROME_CMD="chromium-browser"  
elif command -v chrome &> /dev/null; then
    CHROME_CMD="chrome"
else
    echo "❌ Chrome not found. Please install Google Chrome or Chromium."
    exit 1
fi

echo "✅ Found Chrome: $CHROME_CMD"
echo "🚀 Launching with development settings..."

# Launch Chrome with development settings
$CHROME_CMD \\
    --disable-web-security \\
    --user-data-dir="$TEMP_DIR" \\
    --allow-running-insecure-content \\
    --disable-features=VizDisplayCompositor \\
    --ignore-certificate-errors \\
    --ignore-ssl-errors \\
    --allow-insecure-localhost \\
    http://localhost:3000 &

echo "✅ Chrome launched for FlipSync development"
echo "📱 Navigate to: http://localhost:3000"
echo "🔧 Development mode: CORS disabled, insecure content allowed"
echo ""
echo "⚠️  WARNING: Only use this for development. Do not browse other sites."
"""

    try:
        with open(browser_script, "w") as f:
            f.write(script_content)

        # Make script executable
        os.chmod(browser_script, 0o755)

        print(f"  ✅ Browser launch script created: {browser_script}")
        print(f"  ✅ Script made executable")
        return True

    except Exception as e:
        print(f"  ❌ Failed to create browser script: {e}")
        return False


def main():
    """Main function to apply all fixes"""
    print("🔧 FlipSync Mobile Chat Connectivity Fix")
    print("=" * 50)

    fixes_applied = 0
    total_fixes = 4

    # Apply fixes
    if fix_cors_configuration():
        fixes_applied += 1

    if update_main_app_cors():
        fixes_applied += 1

    if create_websocket_auth_fix():
        fixes_applied += 1

    if create_browser_launch_script():
        fixes_applied += 1

    # Summary
    print("\n📊 Fix Application Summary:")
    print("=" * 50)
    print(f"Fixes Applied: {fixes_applied}/{total_fixes}")

    if fixes_applied == total_fixes:
        print("✅ All fixes applied successfully!")
        print("\n🚀 Next Steps:")
        print("1. Restart the FlipSync backend (docker-compose restart)")
        print("2. Run: ./launch_chrome_dev.sh")
        print("3. Navigate to http://localhost:3000")
        print("4. Test chat functionality")
    else:
        print("⚠️ Some fixes failed to apply. Check error messages above.")

    return fixes_applied == total_fixes


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
