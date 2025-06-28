#!/usr/bin/env python3
"""
Debug eBay Token Exchange Issues
This script helps identify why the token exchange is failing.
"""

import asyncio
import aiohttp
import base64
import json
import sys
import urllib.parse
from datetime import datetime

class TokenExchangeDebugger:
    def __init__(self):
        self.client_id = "BrendanB-Nashvill-PRD-7f5c11990-62c1c838"
        self.client_secret = None  # We'll need to get this from environment
        self.ru_name = "Brendan_Blomfie-BrendanB-Nashvi-vuwrefym"
        self.token_url = "https://api.ebay.com/identity/v1/oauth2/token"
        
    async def debug_token_exchange_flow(self):
        """Debug the complete token exchange flow."""
        print("🔍 Debugging eBay Token Exchange Flow")
        print("=" * 60)
        
        # Step 1: Test OAuth URL generation
        if not await self.test_oauth_url_generation():
            return False
            
        # Step 2: Test token exchange with mock data
        if not await self.test_token_exchange_mock():
            return False
            
        # Step 3: Test eBay API connectivity
        if not await self.test_ebay_api_connectivity():
            return False
            
        return True
        
    async def test_oauth_url_generation(self):
        """Test OAuth URL generation to get a valid state."""
        print("🔗 Testing OAuth URL Generation...")
        
        try:
            oauth_data = {
                "scopes": [
                    "https://api.ebay.com/oauth/api_scope",
                    "https://api.ebay.com/oauth/api_scope/sell.inventory"
                ]
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8001/api/v1/marketplace/ebay/oauth/authorize",
                    json=oauth_data
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        oauth_response = data.get("data", {})
                        
                        auth_url = oauth_response.get("authorization_url", "")
                        state = oauth_response.get("state", "")
                        
                        print(f"  ✅ OAuth URL generated successfully")
                        print(f"  🔑 State: {state}")
                        print(f"  🌐 Auth URL components:")
                        
                        # Parse URL components
                        parsed_url = urllib.parse.urlparse(auth_url)
                        query_params = urllib.parse.parse_qs(parsed_url.query)
                        
                        for key, value in query_params.items():
                            print(f"    {key}: {value[0] if value else 'None'}")
                            
                        # Verify redirect_uri is RuName
                        redirect_uri = query_params.get("redirect_uri", [""])[0]
                        if redirect_uri == self.ru_name:
                            print(f"  ✅ Redirect URI correctly set to RuName: {redirect_uri}")
                        else:
                            print(f"  ❌ Redirect URI incorrect: {redirect_uri} (should be {self.ru_name})")
                            return False
                            
                        return True
                    else:
                        error_text = await response.text()
                        print(f"  ❌ OAuth URL generation failed: {response.status}")
                        print(f"  📝 Error: {error_text}")
                        return False
                        
        except Exception as e:
            print(f"  ❌ Exception during OAuth URL test: {e}")
            return False
            
    async def test_token_exchange_mock(self):
        """Test token exchange with mock authorization code."""
        print("🔄 Testing Token Exchange with Mock Data...")
        
        # Create a mock authorization code (this won't work but will show the request format)
        mock_code = "v^1.1#i^1#f^0#p^3#I^3#r^1#t^Ul41XzMockCodeForTesting"
        
        try:
            callback_data = {
                "code": mock_code,
                "state": "mock_state_for_testing"
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8001/api/v1/marketplace/ebay/oauth/callback",
                    json=callback_data
                ) as response:
                    
                    response_text = await response.text()
                    print(f"  📝 Response Status: {response.status}")
                    print(f"  📝 Response Text: {response_text[:500]}...")
                    
                    if response.status == 400:
                        # Expected for mock data - check if it's a token exchange error
                        if "Token exchange failed" in response_text:
                            print("  ✅ Token exchange endpoint is working (expected failure with mock data)")
                            
                            # Try to extract the actual eBay error
                            try:
                                response_json = json.loads(response_text)
                                detail = response_json.get("detail", "")
                                if "Token exchange failed:" in detail:
                                    ebay_error = detail.split("Token exchange failed:")[1].strip()
                                    print(f"  🔍 eBay API Error: {ebay_error}")
                                    
                                    # Parse eBay error
                                    if "invalid_grant" in ebay_error:
                                        print("  ℹ️  Error Analysis: Invalid authorization code (expected with mock data)")
                                    elif "invalid_client" in ebay_error:
                                        print("  ❌ Error Analysis: Invalid client credentials")
                                        return False
                                    elif "invalid_request" in ebay_error:
                                        print("  ❌ Error Analysis: Invalid request format")
                                        return False
                                        
                            except json.JSONDecodeError:
                                print("  ⚠️  Could not parse error response")
                                
                            return True
                        else:
                            print("  ❌ Unexpected error type")
                            return False
                    else:
                        print("  ⚠️  Unexpected response status")
                        return True
                        
        except Exception as e:
            print(f"  ❌ Exception during token exchange test: {e}")
            return False
            
    async def test_ebay_api_connectivity(self):
        """Test direct connectivity to eBay API."""
        print("🌐 Testing eBay API Connectivity...")
        
        try:
            # Test eBay token endpoint connectivity
            async with aiohttp.ClientSession() as session:
                # Just test connectivity, not actual token exchange
                headers = {
                    "User-Agent": "FlipSync/1.0",
                    "Accept": "application/json"
                }
                
                async with session.get(
                    "https://api.ebay.com/identity/v1/oauth2/token",
                    headers=headers
                ) as response:
                    
                    print(f"  📝 eBay API Response Status: {response.status}")
                    
                    if response.status == 405:  # Method Not Allowed (expected for GET)
                        print("  ✅ eBay API is reachable (405 expected for GET request)")
                        return True
                    elif response.status == 400:  # Bad Request (also acceptable)
                        print("  ✅ eBay API is reachable (400 expected without proper request)")
                        return True
                    else:
                        response_text = await response.text()
                        print(f"  📝 eBay API Response: {response_text[:200]}...")
                        return True
                        
        except Exception as e:
            print(f"  ❌ eBay API connectivity error: {e}")
            return False
            
    async def test_direct_token_exchange(self, auth_code: str, state: str):
        """Test direct token exchange with real authorization code."""
        print("🔄 Testing Direct Token Exchange...")
        
        if not self.client_secret:
            print("  ❌ Client secret not available for direct test")
            return False
            
        try:
            # Prepare credentials for Basic Auth
            credentials = f"{self.client_id}:{self.client_secret}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()
            
            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
            }
            
            data = {
                "grant_type": "authorization_code",
                "code": auth_code,
                "redirect_uri": self.ru_name,  # Must match authorization request
            }
            
            print(f"  🔍 Token Exchange Request:")
            print(f"    URL: {self.token_url}")
            print(f"    Headers: {headers}")
            print(f"    Data: {data}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.token_url,
                    headers=headers,
                    data=data
                ) as response:
                    
                    response_text = await response.text()
                    print(f"  📝 Response Status: {response.status}")
                    print(f"  📝 Response Text: {response_text}")
                    
                    if response.status == 200:
                        print("  ✅ Token exchange successful!")
                        return True
                    else:
                        print(f"  ❌ Token exchange failed: {response_text}")
                        return False
                        
        except Exception as e:
            print(f"  ❌ Direct token exchange error: {e}")
            return False

async def main():
    """Main debug function."""
    debugger = TokenExchangeDebugger()
    
    print("🚀 Starting eBay Token Exchange Debug")
    print("=" * 60)
    
    success = await debugger.debug_token_exchange_flow()
    
    if success:
        print("\n✅ Debug completed successfully")
        print("💡 Recommendations:")
        print("1. Check if client_secret is properly configured")
        print("2. Verify redirect_uri matches exactly between authorize and token requests")
        print("3. Ensure authorization codes are used immediately (they expire quickly)")
        print("4. Check eBay API credentials and permissions")
    else:
        print("\n❌ Debug found issues")
        print("🔧 Check the errors above and fix the identified problems")

if __name__ == "__main__":
    asyncio.run(main())
