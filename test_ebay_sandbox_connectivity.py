#!/usr/bin/env python3
"""
eBay Sandbox Connectivity Test
Validates the refresh token and tests real API connectivity
"""

import asyncio
import os
import sys
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fs_agt_clean.agents.utils.oauth_token_manager import refresh_oauth_token
from fs_agt_clean.agents.market.ebay_client import eBayClient
from fs_agt_clean.agents.market.ebay_agent import EbayMarketAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class eBaySandboxTester:
    """Comprehensive eBay sandbox connectivity tester."""
    
    def __init__(self):
        """Initialize the tester with sandbox credentials."""
        self.client_id = os.getenv("SB_EBAY_APP_ID")
        self.client_secret = os.getenv("SB_EBAY_CERT_ID") 
        self.refresh_token = os.getenv("SB_EBAY_REFRESH_TOKEN")
        self.sandbox_base_url = "https://api.sandbox.ebay.com"
        self.token_endpoint = "https://api.sandbox.ebay.com/identity/v1/oauth2/token"
        
        # Test results storage
        self.test_results = {}
        
    def validate_credentials(self) -> bool:
        """Validate that all required credentials are present."""
        logger.info("🔍 Validating eBay sandbox credentials...")
        
        missing_creds = []
        if not self.client_id:
            missing_creds.append("SB_EBAY_APP_ID")
        if not self.client_secret:
            missing_creds.append("SB_EBAY_CERT_ID")
        if not self.refresh_token:
            missing_creds.append("SB_EBAY_REFRESH_TOKEN")
            
        if missing_creds:
            logger.error(f"❌ Missing credentials: {', '.join(missing_creds)}")
            return False
            
        logger.info("✅ All sandbox credentials present")
        logger.info(f"   Client ID: {self.client_id[:20]}...")
        logger.info(f"   Refresh Token: {self.refresh_token[:50]}...")
        return True
        
    async def test_token_refresh(self) -> bool:
        """Test OAuth token refresh functionality."""
        logger.info("🔄 Testing OAuth token refresh...")
        
        try:
            # Test token refresh for sell scope
            token_data = await refresh_oauth_token(
                token_endpoint=self.token_endpoint,
                refresh_token=self.refresh_token,
                client_id=self.client_id,
                client_secret=self.client_secret,
                scope="https://api.ebay.com/oauth/api_scope/sell.inventory",
                use_basic_auth=True,
                marketplace="ebay_sandbox"
            )
            
            # Validate token response
            required_fields = ["access_token", "expires_in", "token_type"]
            for field in required_fields:
                if field not in token_data:
                    logger.error(f"❌ Missing field in token response: {field}")
                    return False
                    
            logger.info("✅ Token refresh successful")
            logger.info(f"   Token Type: {token_data['token_type']}")
            logger.info(f"   Expires In: {token_data['expires_in']} seconds")
            logger.info(f"   Access Token: {token_data['access_token'][:30]}...")
            
            self.test_results["token_refresh"] = {
                "status": "success",
                "access_token": token_data["access_token"],
                "expires_in": token_data["expires_in"]
            }
            return True
            
        except Exception as e:
            logger.error(f"❌ Token refresh failed: {e}")
            self.test_results["token_refresh"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
            
    async def test_ebay_client(self) -> bool:
        """Test eBay client with real API calls."""
        logger.info("🛒 Testing eBay client functionality...")
        
        try:
            # Create eBay client for sandbox
            ebay_client = eBayClient(
                client_id=self.client_id,
                client_secret=self.client_secret,
                environment="sandbox"
            )
            
            async with ebay_client:
                # Test credential validation
                is_valid = await ebay_client.validate_credentials()
                if not is_valid:
                    logger.error("❌ eBay client credential validation failed")
                    return False
                    
                logger.info("✅ eBay client credentials validated")
                
                # Test product search (should work with public scope)
                try:
                    listings = await ebay_client.search_products("iPhone", limit=3)
                    logger.info(f"✅ Product search returned {len(listings)} listings")
                    
                    if listings:
                        sample_listing = listings[0]
                        logger.info(f"   Sample listing: {sample_listing.title}")
                        logger.info(f"   Price: ${sample_listing.current_price.amount}")
                        
                except Exception as search_error:
                    logger.warning(f"⚠️ Product search failed (may be expected): {search_error}")
                
                self.test_results["ebay_client"] = {
                    "status": "success",
                    "credential_validation": True,
                    "search_results": len(listings) if 'listings' in locals() else 0
                }
                return True
                
        except Exception as e:
            logger.error(f"❌ eBay client test failed: {e}")
            self.test_results["ebay_client"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
            
    async def test_ebay_agent(self) -> bool:
        """Test eBay agent integration."""
        logger.info("🤖 Testing eBay agent integration...")
        
        try:
            # Create agent configuration
            agent_config = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "sandbox": True
            }
            
            # Initialize eBay agent
            ebay_agent = EbayMarketAgent(
                agent_id="test_ebay_agent",
                config=agent_config
            )
            
            # Test agent initialization
            logger.info("✅ eBay agent initialized successfully")
            
            # Test token acquisition
            try:
                # This will test the agent's token management
                access_token = await ebay_agent._get_access_token("sell")
                if access_token:
                    logger.info("✅ Agent token acquisition successful")
                    logger.info(f"   Access Token: {access_token[:30]}...")
                else:
                    logger.error("❌ Agent token acquisition failed")
                    return False
                    
            except Exception as token_error:
                logger.error(f"❌ Agent token acquisition failed: {token_error}")
                return False
                
            self.test_results["ebay_agent"] = {
                "status": "success",
                "token_acquisition": True
            }
            return True
            
        except Exception as e:
            logger.error(f"❌ eBay agent test failed: {e}")
            self.test_results["ebay_agent"] = {
                "status": "failed",
                "error": str(e)
            }
            return False
            
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run all tests and return comprehensive results."""
        logger.info("🚀 Starting eBay Sandbox Connectivity Test Suite")
        logger.info("=" * 60)
        
        start_time = datetime.now(timezone.utc)
        
        # Test 1: Credential validation
        creds_valid = self.validate_credentials()
        if not creds_valid:
            return {"status": "failed", "reason": "Invalid credentials"}
            
        # Test 2: Token refresh
        token_success = await self.test_token_refresh()
        
        # Test 3: eBay client
        client_success = await self.test_ebay_client()
        
        # Test 4: eBay agent
        agent_success = await self.test_ebay_agent()
        
        # Calculate results
        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()
        
        total_tests = 4
        passed_tests = sum([creds_valid, token_success, client_success, agent_success])
        
        # Generate summary
        summary = {
            "status": "success" if passed_tests == total_tests else "partial",
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "duration_seconds": duration,
            "timestamp": end_time.isoformat(),
            "detailed_results": self.test_results
        }
        
        # Print summary
        logger.info("=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info(f"   Status: {'✅ SUCCESS' if summary['status'] == 'success' else '⚠️ PARTIAL SUCCESS'}")
        logger.info(f"   Tests Passed: {passed_tests}/{total_tests}")
        logger.info(f"   Duration: {duration:.2f} seconds")
        
        if summary['status'] == 'success':
            logger.info("🎉 All tests passed! eBay sandbox integration is ready.")
        else:
            logger.warning("⚠️ Some tests failed. Review the logs above for details.")
            
        return summary

async def main():
    """Main test execution function."""
    tester = eBaySandboxTester()
    results = await tester.run_comprehensive_test()
    
    # Exit with appropriate code
    if results["status"] == "success":
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
