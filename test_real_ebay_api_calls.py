#!/usr/bin/env python3
"""
REAL eBay API Integration Test
Tests actual eBay sandbox API calls with evidence of real integration
"""

import asyncio
import aiohttp
import json
import logging
import sys
import time
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealEbayAPITester:
    """Test actual eBay API calls through FlipSync backend."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_direct_ebay_client_in_container(self) -> Dict[str, Any]:
        """Test eBay client directly in the Docker container."""
        logger.info("🔍 Testing Direct eBay Client in Container")
        
        test_script = '''
import asyncio
import sys
import os
sys.path.append("/app")

from fs_agt_clean.agents.market.ebay_client import EbayClient

async def test_ebay_client():
    print("=== REAL eBay API Test ===")
    
    # Initialize eBay client with sandbox credentials
    client = EbayClient()
    
    print(f"Client ID configured: {bool(client.client_id)}")
    print(f"Client Secret configured: {bool(client.client_secret)}")
    print(f"Refresh Token configured: {bool(client.refresh_token)}")
    
    if not client.client_id:
        print("❌ No eBay credentials - would use mocks")
        return {"error": "No credentials"}
    
    print("✅ eBay credentials found - making REAL API calls")
    
    try:
        # Test 1: Validate credentials
        print("\\n🔐 Testing credential validation...")
        is_valid = await client.validate_credentials()
        print(f"Credentials valid: {is_valid}")
        
        # Test 2: Search for products
        print("\\n🔍 Testing product search...")
        search_results = await client.search_products("iPhone", limit=3)
        print(f"Search results count: {len(search_results)}")
        
        if search_results:
            print("✅ REAL eBay search results:")
            for i, result in enumerate(search_results[:2]):
                print(f"  {i+1}. {result.title}")
                print(f"     Price: ${result.current_price.amount}")
                print(f"     Item ID: {result.identifier.ebay_item_id}")
                print(f"     URL: {result.listing_url}")
        
        # Test 3: Get competitive prices
        print("\\n💰 Testing competitive pricing...")
        prices = await client.get_competitive_prices("iPhone 14")
        print(f"Competitive prices found: {len(prices)}")
        
        if prices:
            print("✅ REAL competitive pricing data:")
            for i, price in enumerate(prices[:3]):
                print(f"  {i+1}. ${price.amount}")
        
        return {
            "success": True,
            "credentials_valid": is_valid,
            "search_results_count": len(search_results),
            "competitive_prices_count": len(prices),
            "evidence": "Real eBay API calls made successfully"
        }
        
    except Exception as e:
        print(f"❌ Error during eBay API testing: {e}")
        return {"error": str(e)}
    
    finally:
        await client.close()

# Run the test
result = asyncio.run(test_ebay_client())
print(f"\\n=== TEST RESULT ===")
print(result)
'''
        
        try:
            # Execute the test script in the Docker container
            import subprocess
            result = subprocess.run([
                'docker', 'exec', 'flipsync-api', 'python', '-c', test_script
            ], capture_output=True, text=True, timeout=60)
            
            logger.info("📋 eBay Client Test Output:")
            logger.info(result.stdout)
            
            if result.stderr:
                logger.error("❌ eBay Client Test Errors:")
                logger.error(result.stderr)
            
            # Parse the result
            if "Real eBay API calls made successfully" in result.stdout:
                return {
                    "test_name": "Direct eBay Client Test",
                    "success": True,
                    "evidence": "Real eBay API calls confirmed",
                    "output": result.stdout,
                    "return_code": result.returncode
                }
            else:
                return {
                    "test_name": "Direct eBay Client Test",
                    "success": False,
                    "error": "No evidence of real API calls",
                    "output": result.stdout,
                    "stderr": result.stderr,
                    "return_code": result.returncode
                }
                
        except Exception as e:
            logger.error(f"❌ Container test execution error: {e}")
            return {
                "test_name": "Direct eBay Client Test",
                "success": False,
                "error": str(e)
            }
    
    async def test_ebay_marketplace_endpoint(self) -> Dict[str, Any]:
        """Test the eBay marketplace endpoint for real API integration."""
        logger.info("🛒 Testing eBay Marketplace Endpoint")
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/v1/marketplace/ebay",
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for evidence of real eBay integration
                    evidence_indicators = [
                        "credentials_valid",
                        "api_connection",
                        "sandbox",
                        "ebay_client",
                        "authentication"
                    ]
                    
                    response_text = str(data).lower()
                    evidence_found = any(indicator in response_text for indicator in evidence_indicators)
                    
                    return {
                        "test_name": "eBay Marketplace Endpoint",
                        "success": True,
                        "status_code": response.status,
                        "response_data": data,
                        "evidence_of_real_integration": evidence_found
                    }
                else:
                    error_text = await response.text()
                    return {
                        "test_name": "eBay Marketplace Endpoint",
                        "success": False,
                        "status_code": response.status,
                        "error": error_text
                    }
                    
        except Exception as e:
            return {
                "test_name": "eBay Marketplace Endpoint",
                "success": False,
                "error": str(e)
            }
    
    async def test_agent_with_real_ebay_data(self) -> Dict[str, Any]:
        """Test agents using real eBay data through chat interface."""
        logger.info("🤖 Testing Agents with Real eBay Data")
        
        try:
            # Create conversation
            payload = {
                "title": "Real eBay API Test",
                "description": "Testing agents with actual eBay API calls"
            }
            
            async with self.session.post(
                f"{self.base_url}/api/v1/chat/conversations",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status not in [200, 201]:
                    return {"success": False, "error": "Failed to create conversation"}
                
                data = await response.json()
                conversation_id = data.get('conversation_id') or data.get('id')
                
                if not conversation_id:
                    return {"success": False, "error": "No conversation ID"}
            
            # Send message requesting real eBay data
            message_payload = {
                "text": "I need you to search eBay for 'iPhone 14' and give me REAL current market data with actual prices and item IDs. Please use the actual eBay API, not mock data.",
                "sender_type": "user"
            }
            
            start_time = time.time()
            async with self.session.post(
                f"{self.base_url}/api/v1/chat/conversations/{conversation_id}/messages",
                json=message_payload,
                timeout=aiohttp.ClientTimeout(total=90)
            ) as response:
                
                response_time = time.time() - start_time
                
                if response.status in [200, 201]:
                    data = await response.json()
                    response_text = str(data).lower()
                    
                    # Look for evidence of real eBay data
                    real_data_indicators = [
                        "ebay item id",
                        "ebay.com/itm",
                        "actual price",
                        "real market data",
                        "current listing",
                        "sandbox api",
                        "api call"
                    ]
                    
                    real_data_found = any(indicator in response_text for indicator in real_data_indicators)
                    
                    # Look for mock data indicators (bad signs)
                    mock_indicators = [
                        "mock",
                        "sample",
                        "ebay listing 1",
                        "ebay listing 2",
                        "ebay001",
                        "ebay002"
                    ]
                    
                    mock_data_found = any(indicator in response_text for indicator in mock_indicators)
                    
                    return {
                        "test_name": "Agents with Real eBay Data",
                        "success": True,
                        "response_time": response_time,
                        "real_data_indicators_found": real_data_found,
                        "mock_data_indicators_found": mock_data_found,
                        "evidence_of_real_api": real_data_found and not mock_data_found,
                        "response_preview": str(data)[:500] + "..." if len(str(data)) > 500 else str(data)
                    }
                else:
                    error_text = await response.text()
                    return {
                        "test_name": "Agents with Real eBay Data",
                        "success": False,
                        "status_code": response.status,
                        "error": error_text
                    }
                    
        except Exception as e:
            return {
                "test_name": "Agents with Real eBay Data",
                "success": False,
                "error": str(e)
            }

    async def run_real_ebay_tests(self) -> Dict[str, Any]:
        """Run comprehensive real eBay API integration tests."""
        logger.info("🚀 Starting REAL eBay API Integration Tests")
        logger.info("=" * 70)
        logger.info("🎯 Testing actual eBay sandbox API calls with evidence")
        logger.info("")
        
        test_results = {}
        
        # Test 1: Direct eBay Client in Container
        logger.info("🧪 TEST 1: Direct eBay Client in Container")
        test_results["direct_ebay_client"] = await self.test_direct_ebay_client_in_container()
        
        # Test 2: eBay Marketplace Endpoint
        logger.info("🧪 TEST 2: eBay Marketplace Endpoint")
        test_results["ebay_marketplace_endpoint"] = await self.test_ebay_marketplace_endpoint()
        
        # Test 3: Agents with Real eBay Data
        logger.info("🧪 TEST 3: Agents with Real eBay Data")
        test_results["agents_real_ebay_data"] = await self.test_agent_with_real_ebay_data()
        
        return test_results

async def main():
    """Main test execution."""
    logger.info("🏢 REAL eBay API Integration Testing")
    logger.info("=" * 70)
    logger.info("🔍 Verifying actual eBay sandbox API calls with evidence")
    logger.info("🧪 Environment: eBay Sandbox with Real Credentials")
    logger.info("")
    
    async with RealEbayAPITester() as tester:
        results = await tester.run_real_ebay_tests()
        
        # Analyze results for evidence of real API calls
        logger.info("")
        logger.info("📊 REAL eBay API INTEGRATION RESULTS")
        logger.info("=" * 50)
        
        total_tests = len(results)
        tests_with_real_api_evidence = 0
        tests_successful = 0
        
        for test_name, result in results.items():
            if result.get("success", False):
                tests_successful += 1
                
                # Check for evidence of real API calls
                evidence_found = False
                if "evidence" in result and "Real eBay API calls" in result["evidence"]:
                    evidence_found = True
                elif result.get("evidence_of_real_api", False):
                    evidence_found = True
                elif result.get("evidence_of_real_integration", False):
                    evidence_found = True
                
                if evidence_found:
                    tests_with_real_api_evidence += 1
                
                status = "✅ REAL API" if evidence_found else "⚠️ NO EVIDENCE"
                logger.info(f"   {test_name}: {status}")
                
                if "output" in result:
                    logger.info(f"      Evidence: {result.get('evidence', 'See output')}")
                
            else:
                logger.info(f"   {test_name}: ❌ FAILED")
                logger.info(f"      Error: {result.get('error', 'Unknown error')}")
        
        # Final assessment
        logger.info("")
        logger.info("🎯 REAL API INTEGRATION ASSESSMENT")
        logger.info("=" * 40)
        logger.info(f"Tests Successful: {tests_successful}/{total_tests}")
        logger.info(f"Real API Evidence Found: {tests_with_real_api_evidence}/{total_tests}")
        
        if tests_with_real_api_evidence >= 2:
            logger.info("🎉 SUCCESS: Real eBay API integration confirmed!")
            logger.info("   ✅ Actual eBay sandbox API calls are being made")
            logger.info("   ✅ FlipSync is using real marketplace data")
            return 0
        elif tests_with_real_api_evidence >= 1:
            logger.info("⚠️ PARTIAL: Some real API integration detected")
            logger.info("   ⚠️ Need to verify all components are using real APIs")
            return 0
        else:
            logger.error("❌ NO REAL API INTEGRATION FOUND")
            logger.info("   ❌ FlipSync appears to be using mock data only")
            logger.info("   🔧 Check eBay credentials and API configuration")
            return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
