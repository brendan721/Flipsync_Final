#!/usr/bin/env python3
"""
FlipSync Inventory API Performance Analysis
Test inventory API performance to identify bottlenecks causing 6.754s response times
Target: <1s response time for 100 items
"""

import asyncio
import aiohttp
import time
import json
import statistics
from typing import List, Dict, Any
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class InventoryTestResult:
    """Result of an inventory API test"""
    success: bool
    response_time: float
    status_code: int
    item_count: int = 0
    error_message: str = ""

class InventoryPerformanceTester:
    """Test inventory API performance under various conditions"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.inventory_url = f"{base_url}/api/v1/inventory/items"
        self.auth_url = f"{base_url}/api/v1/auth/login"
        self.auth_token = None
        
    async def authenticate(self, session: aiohttp.ClientSession) -> bool:
        """Authenticate and get access token"""
        try:
            login_data = {
                "email": "test@example.com",
                "password": "SecurePassword!"
            }
            
            async with session.post(self.auth_url, json=login_data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    return True
                else:
                    logger.error(f"Authentication failed: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    async def test_inventory_api(self, session: aiohttp.ClientSession, limit: int = 100, offset: int = 0) -> InventoryTestResult:
        """Test inventory API with specified parameters"""
        start_time = time.time()
        
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        params = {"limit": limit, "offset": offset}
        
        try:
            async with session.get(self.inventory_url, headers=headers, params=params) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    item_count = len(data.get("items", []))
                    
                    return InventoryTestResult(
                        success=True,
                        response_time=response_time,
                        status_code=response.status,
                        item_count=item_count
                    )
                else:
                    error_text = await response.text()
                    return InventoryTestResult(
                        success=False,
                        response_time=response_time,
                        status_code=response.status,
                        error_message=error_text
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            return InventoryTestResult(
                success=False,
                response_time=response_time,
                status_code=0,
                error_message=str(e)
            )
    
    async def test_various_limits(self) -> Dict[str, Any]:
        """Test inventory API with various item limits"""
        logger.info("Testing inventory API with various item limits")
        
        async with aiohttp.ClientSession() as session:
            # Authenticate first
            if not await self.authenticate(session):
                return {"error": "Authentication failed"}
            
            test_limits = [10, 25, 50, 100, 200, 500, 1000]
            results = {}
            
            for limit in test_limits:
                logger.info(f"Testing with limit={limit}")
                
                # Run test 3 times and take average
                test_results = []
                for i in range(3):
                    result = await self.test_inventory_api(session, limit=limit)
                    test_results.append(result)
                    await asyncio.sleep(0.5)  # Brief pause between tests
                
                # Calculate statistics
                successful_results = [r for r in test_results if r.success]
                if successful_results:
                    response_times = [r.response_time for r in successful_results]
                    avg_response_time = statistics.mean(response_times)
                    min_response_time = min(response_times)
                    max_response_time = max(response_times)
                    item_count = successful_results[0].item_count
                    
                    results[limit] = {
                        "success_rate": len(successful_results) / len(test_results) * 100,
                        "avg_response_time": avg_response_time,
                        "min_response_time": min_response_time,
                        "max_response_time": max_response_time,
                        "item_count": item_count,
                        "items_per_second": item_count / avg_response_time if avg_response_time > 0 else 0
                    }
                else:
                    results[limit] = {
                        "success_rate": 0,
                        "error": test_results[0].error_message if test_results else "Unknown error"
                    }
                
                # Stop if response time exceeds 10 seconds
                if successful_results and successful_results[0].response_time > 10:
                    logger.warning(f"Response time exceeded 10s at limit={limit}. Stopping test.")
                    break
        
        return results
    
    async def test_concurrent_requests(self, concurrent_count: int = 5, limit: int = 100) -> Dict[str, Any]:
        """Test concurrent inventory API requests"""
        logger.info(f"Testing {concurrent_count} concurrent inventory requests")
        
        async with aiohttp.ClientSession() as session:
            # Authenticate first
            if not await self.authenticate(session):
                return {"error": "Authentication failed"}
            
            # Create concurrent tasks
            tasks = [
                self.test_inventory_api(session, limit=limit)
                for _ in range(concurrent_count)
            ]
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Process results
            successful_results = []
            failed_results = []
            
            for result in results:
                if isinstance(result, Exception):
                    failed_results.append(str(result))
                elif result.success:
                    successful_results.append(result)
                else:
                    failed_results.append(result.error_message)
            
            if successful_results:
                response_times = [r.response_time for r in successful_results]
                return {
                    "concurrent_requests": concurrent_count,
                    "total_time": total_time,
                    "success_count": len(successful_results),
                    "failure_count": len(failed_results),
                    "success_rate": len(successful_results) / concurrent_count * 100,
                    "avg_response_time": statistics.mean(response_times),
                    "min_response_time": min(response_times),
                    "max_response_time": max(response_times),
                    "throughput_requests_per_second": len(successful_results) / total_time
                }
            else:
                return {
                    "concurrent_requests": concurrent_count,
                    "success_rate": 0,
                    "errors": failed_results[:5]  # Show first 5 errors
                }

async def main():
    """Main test execution"""
    tester = InventoryPerformanceTester()
    
    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{tester.base_url}/health") as response:
                if response.status != 200:
                    logger.error("FlipSync server is not responding. Please start the server first.")
                    return
    except Exception as e:
        logger.error(f"Cannot connect to FlipSync server: {e}")
        return
    
    print("\n" + "="*80)
    print("FLIPSYNC INVENTORY API PERFORMANCE ANALYSIS")
    print("="*80)
    print("Target: <1s response time for 100 items")
    print("Current baseline: 6.754s (needs 6.7x improvement)")
    
    # Test 1: Various item limits
    print("\n📊 Test 1: Response Time vs Item Count")
    results = await tester.test_various_limits()
    
    for limit, result in results.items():
        if "error" in result:
            print(f"  {limit:4d} items: ERROR - {result['error']}")
        else:
            print(f"  {limit:4d} items: {result['avg_response_time']:6.3f}s avg | "
                  f"{result['item_count']:3d} returned | "
                  f"{result['items_per_second']:6.1f} items/s")
    
    # Test 2: Concurrent requests
    print("\n🔄 Test 2: Concurrent Request Performance")
    concurrent_result = await tester.test_concurrent_requests(concurrent_count=5, limit=100)
    
    if "error" in concurrent_result:
        print(f"  ERROR: {concurrent_result['error']}")
    else:
        print(f"  5 concurrent requests: {concurrent_result['success_rate']:5.1f}% success | "
              f"{concurrent_result['avg_response_time']:6.3f}s avg | "
              f"{concurrent_result['throughput_requests_per_second']:5.2f} req/s")
    
    # Analysis and recommendations
    print(f"\n" + "="*80)
    print("PERFORMANCE ANALYSIS:")
    
    # Find the 100-item result
    if 100 in results and "avg_response_time" in results[100]:
        current_time = results[100]["avg_response_time"]
        target_time = 1.0
        improvement_needed = current_time / target_time
        
        print(f"Current 100-item response time: {current_time:.3f}s")
        print(f"Target response time: {target_time:.3f}s")
        print(f"Improvement needed: {improvement_needed:.1f}x faster")
        
        if current_time > target_time:
            print("\n🔴 PERFORMANCE ISSUE CONFIRMED")
            print("RECOMMENDATIONS:")
            print("1. Add database indexing for inventory queries")
            print("2. Implement response caching with Redis")
            print("3. Optimize database query patterns")
            print("4. Add pagination optimization")
        else:
            print("\n✅ PERFORMANCE TARGET MET")
    
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
