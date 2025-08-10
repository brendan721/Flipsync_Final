#!/usr/bin/env python3

"""
eBay OAuth Flow Investigation Script
===================================

This script investigates the eBay OAuth implementation issues and tests
the complete OAuth flow including Redis token storage.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime
from typing import Dict, Any, Optional

import aiohttp
import redis.asyncio as redis

# Production backend configuration
PRODUCTION_API_BASE = 'http://174.138.77.110:8000'

# eBay Production Credentials
EBAY_CREDENTIALS = {
    'app_id': 'BrendanB-Nashvill-PRD-7f5c11990-62c1c838',
    'dev_id': 'e83908d0-476b-4534-a947-3a88227709e4',
    'cert_id': 'PRD-f5c119904e18-fb68-4e53-9b35-49ef'
}

# Redis instances
REDIS_LOCAL = 'redis://127.0.0.1:6379'
REDIS_EXTERNAL = 'redis://174.138.77.110:6379'

class EbayOAuthInvestigator:
    def __init__(self):
        self.session = None
        self.redis_local = None
        self.redis_external = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        try:
            self.redis_local = redis.from_url(REDIS_LOCAL)
            await self.redis_local.ping()
            print("✅ Local Redis (127.0.0.1:6379): Connected")
        except Exception as e:
            print(f"❌ Local Redis (127.0.0.1:6379): {e}")
            
        try:
            self.redis_external = redis.from_url(REDIS_EXTERNAL)
            await self.redis_external.ping()
            print("✅ External Redis (174.138.77.110:6379): Connected")
        except Exception as e:
            print(f"❌ External Redis (174.138.77.110:6379): {e}")
            
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
        if self.redis_local:
            await self.redis_local.close()
        if self.redis_external:
            await self.redis_external.close()

    async def check_redis_tokens(self):
        """Check both Redis instances for existing eBay tokens."""
        print("\n🔍 Checking Redis instances for eBay tokens...")
        
        for redis_name, redis_client in [
            ("Local Redis", self.redis_local),
            ("External Redis", self.redis_external)
        ]:
            if not redis_client:
                print(f"⚠️  {redis_name}: Not available")
                continue
                
            try:
                # Check for eBay-related keys
                keys = await redis_client.keys("*ebay*")
                keys.extend(await redis_client.keys("*oauth*"))
                keys.extend(await redis_client.keys("*token*"))
                
                print(f"\n📊 {redis_name} - Found {len(keys)} relevant keys:")
                for key in keys[:10]:  # Show first 10 keys
                    key_str = key.decode() if isinstance(key, bytes) else str(key)
                    try:
                        value = await redis_client.get(key)
                        if value:
                            value_str = value.decode() if isinstance(value, bytes) else str(value)
                            print(f"   🔑 {key_str}: {value_str[:100]}...")
                        else:
                            print(f"   🔑 {key_str}: <empty>")
                    except Exception as e:
                        print(f"   🔑 {key_str}: <error reading: {e}>")
                        
            except Exception as e:
                print(f"❌ {redis_name}: Error checking keys - {e}")

    async def test_oauth_authorization_url(self):
        """Test generating eBay OAuth authorization URL."""
        print("\n🧪 Testing eBay OAuth Authorization URL Generation...")
        
        try:
            # Test without authentication first
            url = f"{PRODUCTION_API_BASE}/api/v1/marketplace/ebay/oauth/authorize"
            payload = {
                "scopes": [
                    "https://api.ebay.com/oauth/api_scope/sell.inventory",
                    "https://api.ebay.com/oauth/api_scope/sell.account",
                    "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
                ]
            }
            
            async with self.session.post(url, json=payload) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = await response.json()
                    print("✅ OAuth Authorization URL Generation: SUCCESS")
                    print(f"   Authorization URL: {data.get('data', {}).get('authorization_url', 'N/A')}")
                    print(f"   State Parameter: {data.get('data', {}).get('state', 'N/A')}")
                    return data
                elif response.status == 401:
                    print("⚠️  OAuth Authorization: Requires authentication")
                    print(f"   Response: {response_text}")
                    
                    # Try with a mock user_id or session
                    return await self.test_oauth_with_session()
                else:
                    print(f"❌ OAuth Authorization: Failed with status {response.status}")
                    print(f"   Response: {response_text}")
                    
        except Exception as e:
            print(f"❌ OAuth Authorization URL Generation: Exception - {e}")
            
        return None

    async def test_oauth_with_session(self):
        """Test OAuth with session or user context."""
        print("\n🧪 Testing OAuth with session context...")
        
        try:
            # Try to create a session or use existing endpoint
            url = f"{PRODUCTION_API_BASE}/api/v1/marketplace/ebay/oauth/authorize"
            
            # Try with different headers
            headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'FlipSync-OAuth-Test/1.0'
            }
            
            payload = {
                "scopes": [
                    "https://api.ebay.com/oauth/api_scope/sell.inventory",
                    "https://api.ebay.com/oauth/api_scope/sell.account"
                ],
                "user_id": "test_user_oauth",
                "environment": "production"
            }
            
            async with self.session.post(url, json=payload, headers=headers) as response:
                response_text = await response.text()
                
                if response.status == 200:
                    data = await response.json()
                    print("✅ OAuth with Session: SUCCESS")
                    print(f"   Authorization URL: {data.get('data', {}).get('authorization_url', 'N/A')}")
                    return data
                else:
                    print(f"⚠️  OAuth with Session: Status {response.status}")
                    print(f"   Response: {response_text}")
                    
        except Exception as e:
            print(f"❌ OAuth with Session: Exception - {e}")
            
        return None

    async def test_ebay_system_status(self):
        """Test eBay system status endpoint."""
        print("\n🧪 Testing eBay System Status...")
        
        try:
            url = f"{PRODUCTION_API_BASE}/api/v1/ebay/status"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    print("✅ eBay System Status: SUCCESS")
                    print(f"   Environment: {data.get('environment', 'N/A')}")
                    print(f"   Initialized: {data.get('is_initialized', False)}")
                    print(f"   OAuth Token Valid: {data.get('oauth_token_valid', False)}")
                    return data
                else:
                    response_text = await response.text()
                    print(f"❌ eBay System Status: Status {response.status}")
                    print(f"   Response: {response_text}")
                    
        except Exception as e:
            print(f"❌ eBay System Status: Exception - {e}")
            
        return None

    async def test_direct_oauth_flow(self):
        """Test direct OAuth flow using production credentials."""
        print("\n🧪 Testing Direct OAuth Flow...")
        
        try:
            # Generate OAuth URL directly using eBay's OAuth endpoint
            import urllib.parse
            import secrets
            
            # Generate state parameter
            state = secrets.token_urlsafe(32)
            
            # eBay OAuth parameters
            auth_params = {
                'client_id': EBAY_CREDENTIALS['app_id'],
                'response_type': 'code',
                'redirect_uri': 'Brendan_Blomfie-BrendanB-Nashvi-vuwrefym',  # RuName
                'scope': 'https://api.ebay.com/oauth/api_scope/sell.inventory https://api.ebay.com/oauth/api_scope/sell.account',
                'state': state
            }
            
            # Build authorization URL
            base_url = 'https://auth.ebay.com/oauth2/authorize'
            auth_url = f"{base_url}?{urllib.parse.urlencode(auth_params)}"
            
            print("✅ Direct OAuth URL Generated:")
            print(f"   URL: {auth_url}")
            print(f"   State: {state}")
            print(f"   Client ID: {EBAY_CREDENTIALS['app_id']}")
            print(f"   RuName: Brendan_Blomfie-BrendanB-Nashvi-vuwrefym")
            
            return {
                'authorization_url': auth_url,
                'state': state,
                'client_id': EBAY_CREDENTIALS['app_id']
            }
            
        except Exception as e:
            print(f"❌ Direct OAuth Flow: Exception - {e}")
            
        return None

    async def test_trading_api_access(self):
        """Test Trading API access (requires valid token)."""
        print("\n🧪 Testing Trading API Access...")
        
        # This would require a valid access token
        print("⚠️  Trading API test requires valid OAuth token")
        print("   This test will be performed after OAuth flow completion")
        
        return None

    async def generate_oauth_report(self):
        """Generate comprehensive OAuth investigation report."""
        print("\n📊 Generating OAuth Investigation Report...")
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'redis_status': {},
            'oauth_tests': {},
            'recommendations': []
        }
        
        # Redis status
        report['redis_status']['local'] = self.redis_local is not None
        report['redis_status']['external'] = self.redis_external is not None
        
        # OAuth test results
        oauth_result = await self.test_oauth_authorization_url()
        report['oauth_tests']['authorization_url'] = oauth_result is not None
        
        system_status = await self.test_ebay_system_status()
        report['oauth_tests']['system_status'] = system_status is not None
        
        direct_oauth = await self.test_direct_oauth_flow()
        report['oauth_tests']['direct_oauth'] = direct_oauth is not None
        
        # Recommendations
        if not report['oauth_tests']['authorization_url']:
            report['recommendations'].append("OAuth endpoint requires authentication - implement user session")
        
        if not report['redis_status']['local'] and not report['redis_status']['external']:
            report['recommendations'].append("No Redis instances available for token storage")
        
        if direct_oauth:
            report['recommendations'].append("Use direct OAuth URL for user authentication")
            report['oauth_url'] = direct_oauth['authorization_url']
        
        return report

async def main():
    print("🚀 eBay OAuth Flow Investigation")
    print("=" * 60)
    
    async with EbayOAuthInvestigator() as investigator:
        # Check Redis instances
        await investigator.check_redis_tokens()
        
        # Test OAuth endpoints
        await investigator.test_ebay_system_status()
        await investigator.test_oauth_authorization_url()
        await investigator.test_direct_oauth_flow()
        
        # Generate report
        report = await investigator.generate_oauth_report()
        
        # Save report
        with open('ebay-oauth-investigation-report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Investigation report saved to: ebay-oauth-investigation-report.json")
        
        # Print summary
        print("\n🎯 INVESTIGATION SUMMARY")
        print("=" * 60)
        print(f"📊 Redis Local: {'✅ Connected' if report['redis_status']['local'] else '❌ Not available'}")
        print(f"📊 Redis External: {'✅ Connected' if report['redis_status']['external'] else '❌ Not available'}")
        print(f"📊 OAuth Authorization: {'✅ Working' if report['oauth_tests']['authorization_url'] else '⚠️  Requires auth'}")
        print(f"📊 System Status: {'✅ Working' if report['oauth_tests']['system_status'] else '❌ Failed'}")
        print(f"📊 Direct OAuth: {'✅ Generated' if report['oauth_tests']['direct_oauth'] else '❌ Failed'}")
        
        if 'oauth_url' in report:
            print(f"\n🔗 OAuth Authorization URL:")
            print(f"   {report['oauth_url']}")
        
        print(f"\n📋 Recommendations: {len(report['recommendations'])}")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠️  Investigation interrupted by user")
    except Exception as e:
        print(f"\n❌ Investigation failed: {e}")
        sys.exit(1)
