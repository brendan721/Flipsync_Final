#!/usr/bin/env python3
"""
Test Redis connectivity from within the Docker container
"""

import asyncio
import json
import os
import redis.asyncio as redis
from datetime import datetime

async def test_redis_from_container():
    """Test Redis connectivity using the same configuration as the backend."""
    print("🔍 Testing Redis from Container Configuration")
    print("=" * 60)
    
    # Use the same Redis URL as the backend
    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
    print(f"📍 Redis URL: {redis_url}")
    
    try:
        # Create Redis client exactly like the backend does
        redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        
        # Test basic connectivity
        await redis_client.ping()
        print("✅ Redis ping successful")
        
        # Test state storage exactly like the OAuth flow
        test_state = "test_container_state_12345"
        state_data = {
            "user_id": "test_user",
            "scopes": ["https://api.ebay.com/oauth/api_scope"],
            "created_at": datetime.now().isoformat(),
            "authenticated": False
        }
        
        # Store state with the same key format
        state_key = f"oauth_state:{test_state}"
        await redis_client.setex(state_key, 3600, json.dumps(state_data))
        print(f"✅ State stored: {state_key}")
        
        # Retrieve state
        stored_data = await redis_client.get(state_key)
        if stored_data:
            retrieved_data = json.loads(stored_data)
            print(f"✅ State retrieved: {retrieved_data}")
        else:
            print("❌ State not found after storage")
            
        # List all oauth_state keys
        keys = await redis_client.keys("oauth_state:*")
        print(f"📝 All oauth_state keys: {keys}")
        
        # Clean up
        await redis_client.delete(state_key)
        await redis_client.aclose()
        
        return True
        
    except Exception as e:
        print(f"❌ Redis error: {e}")
        return False

async def test_oauth_authorize_endpoint():
    """Test the OAuth authorize endpoint to see if it stores state."""
    print("\n🔗 Testing OAuth Authorize Endpoint State Storage")
    print("=" * 60)
    
    import aiohttp
    
    try:
        oauth_data = {
            "scopes": [
                "https://api.ebay.com/oauth/api_scope",
                "https://api.ebay.com/oauth/api_scope/sell.inventory"
            ]
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/api/v1/marketplace/ebay/oauth/authorize",
                json=oauth_data
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    oauth_response = data.get("data", {})
                    state = oauth_response.get("state", "")
                    
                    print(f"✅ OAuth URL generated with state: {state}")
                    
                    # Now check if the state was actually stored in Redis
                    redis_url = os.getenv("REDIS_URL", "redis://redis:6379")
                    redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
                    
                    state_key = f"oauth_state:{state}"
                    stored_data = await redis_client.get(state_key)
                    
                    if stored_data:
                        state_data = json.loads(stored_data)
                        print(f"✅ State found in Redis: {state_data}")
                        await redis_client.aclose()
                        return True
                    else:
                        print(f"❌ State NOT found in Redis: {state_key}")
                        
                        # Check all keys
                        keys = await redis_client.keys("oauth_state:*")
                        print(f"📝 All oauth_state keys: {keys}")
                        
                        await redis_client.aclose()
                        return False
                else:
                    print(f"❌ OAuth authorize failed: {response.status}")
                    text = await response.text()
                    print(f"📝 Error: {text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

async def main():
    """Main test function."""
    print("🚀 Redis Container Test")
    print("=" * 60)
    
    # Test 1: Basic Redis connectivity
    redis_ok = await test_redis_from_container()
    
    if redis_ok:
        # Test 2: OAuth endpoint state storage
        oauth_ok = await test_oauth_authorize_endpoint()
        
        if oauth_ok:
            print("\n✅ All tests passed - OAuth state storage working")
        else:
            print("\n❌ OAuth endpoint not storing state in Redis")
    else:
        print("\n❌ Redis connectivity failed")

if __name__ == "__main__":
    asyncio.run(main())
