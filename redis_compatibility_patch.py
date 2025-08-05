#!/usr/bin/env python3
"""
Redis Compatibility Patch for FlipSync Production Deployment
============================================================

This script patches the FlipSync codebase to use the standard redis library
instead of aioredis for Python 3.12 compatibility.
"""

import os
import re
import shutil
from pathlib import Path

def patch_redis_imports():
    """Patch all files that import aioredis to use redis instead."""
    
    # Files that need patching
    files_to_patch = [
        "/opt/flipsync/fs_agt_clean/core/cache/ai_cache.py",
        "/opt/flipsync/fs_agt_clean/core/cache/redis_manager.py"
    ]
    
    for file_path in files_to_patch:
        if not os.path.exists(file_path):
            print(f"⚠️  File not found: {file_path}")
            continue
            
        print(f"🔧 Patching {file_path}")
        
        # Read the file
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Create backup
        backup_path = f"{file_path}.backup"
        shutil.copy2(file_path, backup_path)
        print(f"📦 Backup created: {backup_path}")
        
        # Apply patches
        if "ai_cache.py" in file_path:
            content = patch_ai_cache(content)
        elif "redis_manager.py" in file_path:
            content = patch_redis_manager(content)
        
        # Write patched content
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Patched {file_path}")

def patch_ai_cache(content):
    """Patch ai_cache.py to use redis instead of aioredis."""
    
    # Replace aioredis imports
    content = re.sub(
        r'try:\s*import aioredis\s*from aioredis import Redis\s*REDIS_AVAILABLE = True\s*except ImportError:\s*aioredis = None\s*Redis = None\s*REDIS_AVAILABLE = False',
        '''try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    Redis = None
    REDIS_AVAILABLE = False''',
        content,
        flags=re.DOTALL
    )
    
    # Replace aioredis.from_url calls
    content = re.sub(
        r'await aioredis\.from_url\(',
        'await redis.from_url(',
        content
    )
    
    return content

def patch_redis_manager(content):
    """Patch redis_manager.py to use redis instead of aioredis."""
    
    # Replace aioredis imports
    content = re.sub(
        r'try:\s*import aioredis\s*from aioredis import Redis\s*REDIS_AVAILABLE = True\s*except ImportError:\s*aioredis = None\s*Redis = None\s*REDIS_AVAILABLE = False',
        '''try:
    import redis.asyncio as redis
    from redis.asyncio import Redis
    REDIS_AVAILABLE = True
except ImportError:
    redis = None
    Redis = None
    REDIS_AVAILABLE = False''',
        content,
        flags=re.DOTALL
    )
    
    # Replace aioredis.from_url calls
    content = re.sub(
        r'self\._client = await aioredis\.from_url\(',
        'self._client = await redis.from_url(',
        content
    )
    
    return content

def main():
    """Main execution function."""
    print("🚀 Starting Redis compatibility patch for FlipSync...")
    
    try:
        patch_redis_imports()
        print("\n✅ Redis compatibility patch completed successfully!")
        print("🔄 FlipSync is now compatible with Python 3.12 and redis library")
        
    except Exception as e:
        print(f"\n❌ Patch failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
