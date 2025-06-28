#!/usr/bin/env python3
"""
Test OAuth State Storage in Redis
This script tests the Redis-based OAuth state storage that's causing the token exchange to fail.
"""

import asyncio
import json
import redis.asyncio as redis
import requests
from datetime import datetime

class OAuthStateDebugger:
    def __init__(self):
        self.redis_url = "redis://localhost:6379"
        self.backend_url = "http://localhost:8001"
        
    async def test_oauth_state_flow(self):
        """Test the complete OAuth state flow."""
        print("🔍 Testing OAuth State Storage Flow")
        print("=" * 60)
        
        # Step 1: Test Redis connectivity
        if not await self.test_redis_connectivity():
            return False
            
        # Step 2: Test OAuth URL generation and state storage
        oauth_state = await self.test_oauth_url_generation()
        if not oauth_state:
            return False
            
        # Step 3: Test state retrieval
        if not await self.test_state_retrieval(oauth_state):
            return False
            
        # Step 4: Test OAuth callback with valid state
        if not await self.test_oauth_callback_with_state(oauth_state):
            return False
            
        return True
        
    async def test_redis_connectivity(self):
        """Test Redis connectivity."""
        print("🔗 Testing Redis Connectivity...")
        
        try:
            redis_client = redis.Redis.from_url(self.redis_url, decode_responses=True)
            
            # Test basic Redis operations
            await redis_client.set("test_key", "test_value", ex=10)
            value = await redis_client.get("test_key")
            
            if value == "test_value":
                print("  ✅ Redis connectivity: OK")
                print(f"  ✅ Redis URL: {self.redis_url}")
                
                # Clean up
                await redis_client.delete("test_key")
                await redis_client.aclose()
                return True
            else:
                print("  ❌ Redis connectivity: Failed to store/retrieve test data")
                await redis_client.aclose()
                return False
                
        except Exception as e:
            print(f"  ❌ Redis connectivity error: {e}")
            return False
            
    async def test_oauth_url_generation(self):
        """Test OAuth URL generation and extract state."""
        print("🔗 Testing OAuth URL Generation and State Storage...")
        
        try:
            oauth_data = {
                "scopes": [
                    "https://api.ebay.com/oauth/api_scope",
                    "https://api.ebay.com/oauth/api_scope/sell.inventory"
                ]
            }
            
            response = requests.post(
                f"{self.backend_url}/api/v1/marketplace/ebay/oauth/authorize",
                json=oauth_data
            )
            
            if response.status_code == 200:
                data = response.json()
                oauth_response = data.get("data", {})
                state = oauth_response.get("state", "")
                
                print(f"  ✅ OAuth URL generated successfully")
                print(f"  🔑 State: {state}")
                
                return state
            else:
                print(f"  ❌ OAuth URL generation failed: {response.status_code}")
                print(f"  📝 Error: {response.text}")
                return None
                
        except Exception as e:
            print(f"  ❌ Exception during OAuth URL generation: {e}")
            return None
            
    async def test_state_retrieval(self, state):
        """Test retrieving OAuth state from Redis."""
        print("🔍 Testing OAuth State Retrieval...")
        
        try:
            redis_client = redis.Redis.from_url(self.redis_url, decode_responses=True)
            
            # Try to retrieve the state
            state_key = f"oauth_state:{state}"
            stored_data = await redis_client.get(state_key)
            
            if stored_data:
                state_data = json.loads(stored_data)
                print(f"  ✅ State retrieved successfully")
                print(f"  📝 State data: {state_data}")
                
                # Check TTL
                ttl = await redis_client.ttl(state_key)
                print(f"  ⏰ State TTL: {ttl} seconds")
                
                await redis_client.aclose()
                return True
            else:
                print(f"  ❌ State not found in Redis")
                print(f"  🔍 Checking all oauth_state keys...")
                
                # List all oauth_state keys
                keys = await redis_client.keys("oauth_state:*")
                print(f"  📝 Found {len(keys)} oauth_state keys: {keys}")
                
                await redis_client.aclose()
                return False
                
        except Exception as e:
            print(f"  ❌ Exception during state retrieval: {e}")
            return False
            
    async def test_oauth_callback_with_state(self, state):
        """Test OAuth callback with valid state."""
        print("🔄 Testing OAuth Callback with Valid State...")
        
        try:
            callback_data = {
                "code": "test_authorization_code_12345",
                "state": state
            }
            
            response = requests.post(
                f"{self.backend_url}/api/v1/marketplace/ebay/oauth/callback",
                json=callback_data
            )
            
            print(f"  📝 Response Status: {response.status_code}")
            print(f"  📝 Response Headers: {dict(response.headers)}")
            
            if response.status_code == 302:
                # Check redirect location
                location = response.headers.get("location", "")
                print(f"  🔄 Redirect Location: {location}")
                
                if "Invalid or expired state parameter" in location:
                    print("  ❌ State validation still failing")
                    return False
                elif "Token exchange failed" in location:
                    print("  ✅ State validation passed, but token exchange failed (expected with mock code)")
                    return True
                else:
                    print("  ⚠️  Unexpected redirect")
                    return True
            else:
                print(f"  📝 Response Text: {response.text}")
                return response.status_code == 200
                
        except Exception as e:
            print(f"  ❌ Exception during OAuth callback test: {e}")
            return False
            
    async def test_manual_state_storage(self):
        """Test manual state storage and retrieval."""
        print("🧪 Testing Manual State Storage...")
        
        try:
            redis_client = redis.Redis.from_url(self.redis_url, decode_responses=True)
            
            # Create test state
            test_state = "test_state_12345"
            test_data = {
                "user_id": "test_user",
                "scopes": ["https://api.ebay.com/oauth/api_scope"],
                "created_at": datetime.now().isoformat(),
                "authenticated": False
            }
            
            # Store state
            state_key = f"oauth_state:{test_state}"
            await redis_client.setex(state_key, 3600, json.dumps(test_data))
            print(f"  ✅ Test state stored: {test_state}")
            
            # Retrieve state
            stored_data = await redis_client.get(state_key)
            if stored_data:
                retrieved_data = json.loads(stored_data)
                print(f"  ✅ Test state retrieved: {retrieved_data}")
                
                # Test OAuth callback with this state
                callback_data = {
                    "code": "test_code_67890",
                    "state": test_state
                }
                
                response = requests.post(
                    f"{self.backend_url}/api/v1/marketplace/ebay/oauth/callback",
                    json=callback_data
                )
                
                print(f"  📝 Callback Response: {response.status_code}")
                location = response.headers.get("location", "")
                print(f"  📝 Callback Location: {location}")
                
                # Clean up
                await redis_client.delete(state_key)
                await redis_client.aclose()
                
                return "Invalid or expired state parameter" not in location
            else:
                print(f"  ❌ Failed to retrieve test state")
                await redis_client.aclose()
                return False
                
        except Exception as e:
            print(f"  ❌ Exception during manual state test: {e}")
            return False

async def main():
    """Main debug function."""
    debugger = OAuthStateDebugger()
    
    print("🚀 Starting OAuth State Debug")
    print("=" * 60)
    
    # Test the complete flow
    success = await debugger.test_oauth_state_flow()
    
    if not success:
        print("\n🧪 Running additional manual tests...")
        manual_success = await debugger.test_manual_state_storage()
        
        if manual_success:
            print("\n✅ Manual state storage works - issue is in OAuth URL generation")
        else:
            print("\n❌ Manual state storage also fails - Redis or backend issue")
    
    if success:
        print("\n✅ OAuth state flow working correctly")
    else:
        print("\n❌ OAuth state flow has issues")
        print("🔧 Possible causes:")
        print("1. Redis connectivity issues")
        print("2. State expiring too quickly")
        print("3. State key mismatch")
        print("4. Redis configuration issues")

if __name__ == "__main__":
    asyncio.run(main())
