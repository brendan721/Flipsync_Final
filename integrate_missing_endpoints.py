#!/usr/bin/env python3

"""
FlipSync Missing Endpoints Integration Script
============================================
Script to integrate missing API endpoints into the main FastAPI application
"""

import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def integrate_endpoints():
    """Integrate missing endpoints into main.py"""
    
    main_py_path = "/opt/flipsync/fs_agt_clean/app/main.py"
    
    # Read the current main.py file
    try:
        with open(main_py_path, 'r') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"Failed to read main.py: {e}")
        return False
    
    # Check if missing endpoints are already integrated
    if "missing_api_endpoints" in content:
        logger.info("Missing endpoints already integrated")
        return True
    
    # Find the import section and add our import
    import_line = "from fs_agt_clean.api.routes.missing_api_endpoints import ("
    import_block = """from fs_agt_clean.api.routes.missing_api_endpoints import (
    mobile_router as missing_mobile_router,
    ai_router as missing_ai_router,
    shipping_router as missing_shipping_router,
    advertising_router as missing_advertising_router
)"""
    
    # Find a good place to add the import (after other route imports)
    insert_position = content.find("from fs_agt_clean.api.routes.websocket_unified import")
    if insert_position == -1:
        logger.error("Could not find insertion point for imports")
        return False
    
    # Find the end of that import line
    end_position = content.find("\n", insert_position)
    
    # Insert our import
    new_content = (
        content[:end_position + 1] + 
        "\n# Missing API endpoints\n" + 
        import_block + "\n" + 
        content[end_position + 1:]
    )
    
    # Find where to add the router registrations
    # Look for the mobile router registration
    mobile_router_position = new_content.find('app.include_router(mobile_router, prefix="/api/v1/mobile"')
    
    if mobile_router_position == -1:
        # If mobile router doesn't exist, add after the main router registrations
        router_position = new_content.find('app.include_router(websocket_unified_router')
        if router_position == -1:
            logger.error("Could not find router registration section")
            return False
        
        # Find the end of that line
        end_router_position = new_content.find("\n", router_position)
        
        # Add our router registrations
        router_registrations = """
    # Missing API endpoints - Week 3 Implementation
    app.include_router(missing_mobile_router, prefix="/api/v1/mobile", tags=["mobile-missing"])
    app.include_router(missing_ai_router, prefix="/api/v1/ai", tags=["ai-missing"])
    app.include_router(missing_shipping_router, prefix="/api/v1/shipping", tags=["shipping-missing"])
    app.include_router(missing_advertising_router, prefix="/api/v1/advertising", tags=["advertising-missing"])
    logger.info("✅ Missing API endpoints registered successfully")
"""
        
        new_content = (
            new_content[:end_router_position + 1] + 
            router_registrations + 
            new_content[end_router_position + 1:]
        )
    else:
        logger.info("Mobile router already exists, skipping router registration")
    
    # Write the updated content back
    try:
        # Create backup
        backup_path = f"{main_py_path}.backup.missing_endpoints"
        with open(backup_path, 'w') as f:
            f.write(content)
        logger.info(f"Backup created: {backup_path}")
        
        # Write new content
        with open(main_py_path, 'w') as f:
            f.write(new_content)
        
        logger.info("Successfully integrated missing endpoints into main.py")
        return True
        
    except Exception as e:
        logger.error(f"Failed to write updated main.py: {e}")
        return False

def restart_backend():
    """Restart the backend service"""
    try:
        import subprocess
        
        # Find the uvicorn process
        result = subprocess.run(['pgrep', '-f', 'uvicorn.*fs_agt_clean'], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            pid = result.stdout.strip()
            logger.info(f"Found backend process PID: {pid}")
            
            # Kill the process gracefully
            subprocess.run(['kill', '-TERM', pid])
            logger.info("Backend process terminated")
            
            # Wait a moment
            import time
            time.sleep(2)
            
            # Start new process
            subprocess.Popen([
                '/opt/flipsync/venv/bin/uvicorn',
                'fs_agt_clean.app.main:app',
                '--host', '0.0.0.0',
                '--port', '8000',
                '--timeout-keep-alive', '300',
                '--access-log',
                '--log-level', 'info',
                '--no-server-header',
                '--date-header',
                '--forwarded-allow-ips=*'
            ], cwd='/opt/flipsync')
            
            logger.info("Backend service restarted")
            return True
            
        else:
            logger.warning("Backend process not found")
            return False
            
    except Exception as e:
        logger.error(f"Failed to restart backend: {e}")
        return False

def main():
    """Main integration function"""
    logger.info("Starting missing endpoints integration...")
    
    # Change to the correct directory
    os.chdir('/opt/flipsync')
    
    # Integrate endpoints
    if not integrate_endpoints():
        logger.error("Failed to integrate endpoints")
        return 1
    
    # Restart backend
    if not restart_backend():
        logger.error("Failed to restart backend")
        return 1
    
    logger.info("Missing endpoints integration completed successfully!")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
