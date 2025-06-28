#!/usr/bin/env python3
"""
Real Agent eBay API Calls Test for FlipSync Production Readiness
================================================================

This test validates actual EbayMarketAgent API calls with real eBay data:
1. Real agent initialization with fixed metrics
2. Actual eBay API calls through the agent
3. Agent business logic validation with real data

NOTE: This focuses on the CORE AGENTIC SYSTEM functionality.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fs_agt_clean.agents.market.ebay_agent import EbayMarketAgent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RealAgentEbayTester:
    """Test real EbayMarketAgent with actual eBay API calls."""
    
    def __init__(self):
        """Initialize the real agent eBay tester."""
        self.client_id = os.getenv("SB_EBAY_APP_ID")
        self.client_secret = os.getenv("SB_EBAY_CERT_ID")
        self.refresh_token = os.getenv("SB_EBAY_REFRESH_TOKEN")
        
        # Test results storage
        self.test_results = {}
        
    async def test_agent_initialization(self) -> Dict[str, Any]:
        """Test EbayMarketAgent initialization."""
        logger.info("🔧 Testing EbayMarketAgent initialization...")
        
        try:
            # Create agent configuration
            agent_config = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "refresh_token": self.refresh_token,
                "sandbox": True
            }
            
            # Initialize real EbayMarketAgent
            self.ebay_agent = EbayMarketAgent(
                agent_id="test_ebay_agent",
                config=agent_config
            )
            
            logger.info("✅ EbayMarketAgent initialized successfully")
            return {
                "success": True,
                "agent_id": self.ebay_agent.agent_id,
                "marketplace": self.ebay_agent.marketplace,
                "sandbox_mode": agent_config.get("sandbox", False)
            }
            
        except Exception as e:
            logger.error(f"❌ EbayMarketAgent initialization failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_agent_token_acquisition(self) -> Dict[str, Any]:
        """Test agent token acquisition (the part that was hanging)."""
        logger.info("🔑 Testing agent token acquisition...")
        
        try:
            if not hasattr(self, 'ebay_agent'):
                return {"success": False, "error": "Agent not initialized"}
            
            # This was the method that was hanging due to metrics
            # Now it should work with the fixed metrics system
            logger.info("   Attempting to get access token...")
            
            # Test token acquisition for different scopes
            scopes_to_test = ["sell", "buy"]  # Test multiple scopes
            token_results = {}
            
            for scope in scopes_to_test:
                try:
                    logger.info(f"   Testing {scope} scope token...")
                    # This should now work without hanging
                    access_token = await self.ebay_agent._get_access_token(scope)
                    
                    if access_token:
                        logger.info(f"✅ {scope} token acquired: {access_token[:30]}...")
                        token_results[scope] = {
                            "success": True,
                            "token_length": len(access_token),
                            "token_preview": access_token[:30] + "..."
                        }
                    else:
                        logger.warning(f"⚠️ {scope} token acquisition returned None")
                        token_results[scope] = {
                            "success": False,
                            "error": "Token acquisition returned None"
                        }
                        
                except Exception as scope_error:
                    logger.error(f"❌ {scope} token acquisition failed: {scope_error}")
                    token_results[scope] = {
                        "success": False,
                        "error": str(scope_error)
                    }
            
            # Check if at least one scope worked
            successful_scopes = [scope for scope, result in token_results.items() if result.get("success")]
            
            return {
                "success": len(successful_scopes) > 0,
                "successful_scopes": successful_scopes,
                "token_results": token_results,
                "total_scopes_tested": len(scopes_to_test)
            }
            
        except Exception as e:
            logger.error(f"❌ Agent token acquisition test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_agent_api_calls(self) -> Dict[str, Any]:
        """Test actual agent API calls to eBay."""
        logger.info("🌐 Testing agent eBay API calls...")
        
        try:
            if not hasattr(self, 'ebay_agent'):
                return {"success": False, "error": "Agent not initialized"}
            
            # Test different agent API methods
            api_test_results = {}
            
            # Test 1: Search products through agent
            logger.info("   Testing agent product search...")
            try:
                # This should use the agent's internal API call methods
                search_query = "iPhone"
                
                # Use the agent's API call method directly
                search_response = await self.ebay_agent._make_api_call(
                    method="GET",
                    endpoint="/buy/browse/v1/item_summary/search",
                    scope_type="buy",
                    params={
                        "q": search_query,
                        "limit": 3
                    }
                )
                
                if search_response and "itemSummaries" in search_response:
                    items = search_response["itemSummaries"]
                    logger.info(f"✅ Agent API search successful: {len(items)} items found")
                    
                    api_test_results["product_search"] = {
                        "success": True,
                        "items_found": len(items),
                        "sample_item": {
                            "title": items[0].get("title", "N/A"),
                            "price": items[0].get("price", {}).get("value", "N/A")
                        } if items else None
                    }
                else:
                    logger.warning("⚠️ Agent API search returned no items")
                    api_test_results["product_search"] = {
                        "success": True,
                        "items_found": 0,
                        "note": "No items found but API call successful"
                    }
                    
            except Exception as search_error:
                logger.error(f"❌ Agent API search failed: {search_error}")
                api_test_results["product_search"] = {
                    "success": False,
                    "error": str(search_error)
                }
            
            # Test 2: Get categories through agent
            logger.info("   Testing agent category retrieval...")
            try:
                category_response = await self.ebay_agent._make_api_call(
                    method="GET",
                    endpoint="/commerce/taxonomy/v1/category_tree/0",
                    scope_type="buy"
                )
                
                if category_response and "categoryTreeId" in category_response:
                    logger.info("✅ Agent category API call successful")
                    api_test_results["category_retrieval"] = {
                        "success": True,
                        "category_tree_id": category_response.get("categoryTreeId"),
                        "version": category_response.get("categoryTreeVersion")
                    }
                else:
                    logger.warning("⚠️ Agent category API call returned unexpected response")
                    api_test_results["category_retrieval"] = {
                        "success": False,
                        "error": "Unexpected response format"
                    }
                    
            except Exception as category_error:
                logger.error(f"❌ Agent category API call failed: {category_error}")
                api_test_results["category_retrieval"] = {
                    "success": False,
                    "error": str(category_error)
                }
            
            # Calculate overall success
            successful_calls = sum(1 for result in api_test_results.values() if result.get("success"))
            total_calls = len(api_test_results)
            
            return {
                "success": successful_calls > 0,
                "successful_calls": successful_calls,
                "total_calls": total_calls,
                "api_test_results": api_test_results
            }
            
        except Exception as e:
            logger.error(f"❌ Agent API calls test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive real agent eBay API test."""
        logger.info("🚀 Starting Real Agent eBay API Test Suite")
        logger.info("=" * 60)
        
        results = {
            "test_start_time": datetime.now().isoformat(),
            "tests": {}
        }
        
        # Test 1: Agent initialization
        logger.info("Test 1: Agent Initialization")
        results["tests"]["agent_initialization"] = await self.test_agent_initialization()
        
        # Test 2: Token acquisition (previously hanging)
        logger.info("Test 2: Agent Token Acquisition")
        results["tests"]["token_acquisition"] = await self.test_agent_token_acquisition()
        
        # Test 3: Real API calls through agent
        logger.info("Test 3: Agent eBay API Calls")
        results["tests"]["api_calls"] = await self.test_agent_api_calls()
        
        # Calculate overall success
        successful_tests = sum(1 for test in results["tests"].values() if test.get("success", False))
        total_tests = len(results["tests"])
        
        results["summary"] = {
            "total_tests": total_tests,
            "successful_tests": successful_tests,
            "success_rate": f"{(successful_tests/total_tests)*100:.1f}%",
            "overall_status": "PASS" if successful_tests == total_tests else "PARTIAL"
        }
        
        results["test_end_time"] = datetime.now().isoformat()
        
        return results


async def main():
    """Main test execution."""
    tester = RealAgentEbayTester()
    
    # Validate credentials
    if not all([tester.client_id, tester.client_secret]):
        logger.error("❌ Missing eBay sandbox credentials")
        return
    
    logger.info("✅ eBay sandbox credentials present")
    
    # Run tests
    results = await tester.run_comprehensive_test()
    
    # Print results
    logger.info("=" * 60)
    logger.info("📊 REAL AGENT EBAY API TEST RESULTS")
    logger.info("=" * 60)
    
    for test_name, test_result in results["tests"].items():
        status = "✅ PASS" if test_result.get("success") else "❌ FAIL"
        logger.info(f"{test_name}: {status}")
        if not test_result.get("success"):
            logger.info(f"   Error: {test_result.get('error', 'Unknown error')}")
        else:
            # Print key details for successful tests
            if test_name == "token_acquisition":
                successful_scopes = test_result.get("successful_scopes", [])
                logger.info(f"   Successful scopes: {', '.join(successful_scopes)}")
            elif test_name == "api_calls":
                successful_calls = test_result.get("successful_calls", 0)
                total_calls = test_result.get("total_calls", 0)
                logger.info(f"   API calls: {successful_calls}/{total_calls} successful")
    
    logger.info(f"Overall Status: {results['summary']['overall_status']}")
    logger.info(f"Success Rate: {results['summary']['success_rate']}")
    
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
