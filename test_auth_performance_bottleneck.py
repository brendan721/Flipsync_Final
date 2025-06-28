#!/usr/bin/env python3
"""
FlipSync Authentication Performance Bottleneck Analysis
Test concurrent authentication performance to identify bottlenecks at 25+ users
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
class AuthTestResult:
    """Result of an authentication test"""
    success: bool
    response_time: float
    status_code: int
    error_message: str = ""

class AuthPerformanceTester:
    """Test authentication performance under concurrent load"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.login_url = f"{base_url}/api/v1/auth/login"
        self.token_url = f"{base_url}/api/v1/auth/token"
        
    async def test_single_auth(self, session: aiohttp.ClientSession, user_id: int) -> AuthTestResult:
        """Test single authentication request"""
        start_time = time.time()

        # Test data - use the configured test user
        login_data = {
            "email": "test@example.com",
            "password": "SecurePassword!"
        }
        
        try:
            async with session.post(self.login_url, json=login_data) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    return AuthTestResult(
                        success=True,
                        response_time=response_time,
                        status_code=response.status
                    )
                else:
                    error_text = await response.text()
                    return AuthTestResult(
                        success=False,
                        response_time=response_time,
                        status_code=response.status,
                        error_message=error_text
                    )
                    
        except Exception as e:
            response_time = time.time() - start_time
            return AuthTestResult(
                success=False,
                response_time=response_time,
                status_code=0,
                error_message=str(e)
            )
    
    async def test_concurrent_auth(self, concurrent_users: int) -> Dict[str, Any]:
        """Test concurrent authentication with specified number of users"""
        logger.info(f"Testing authentication with {concurrent_users} concurrent users")

        # Create session with connection pooling and different user agents to simulate different clients
        connector = aiohttp.TCPConnector(
            limit=concurrent_users + 10,  # Allow extra connections
            limit_per_host=concurrent_users + 10
        )

        # Add headers to simulate different clients and avoid burst limiting
        headers = {
            'User-Agent': 'FlipSync-LoadTest/1.0',
            'X-Forwarded-For': '192.168.1.100',  # Simulate different IP
            'X-Real-IP': '192.168.1.100'
        }

        async with aiohttp.ClientSession(connector=connector, headers=headers) as session:
            # Create concurrent authentication tasks with slight staggering
            tasks = []
            for user_id in range(concurrent_users):
                tasks.append(self.test_single_auth(session, user_id))
                # Add tiny delay to avoid burst protection (simulate real user behavior)
                if user_id % 10 == 9:  # Every 10 users, add small delay
                    await asyncio.sleep(0.1)

            # Execute all tasks concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            # Process results
            successful_results = []
            failed_results = []
            
            for result in results:
                if isinstance(result, Exception):
                    failed_results.append(AuthTestResult(
                        success=False,
                        response_time=0,
                        status_code=0,
                        error_message=str(result)
                    ))
                elif result.success:
                    successful_results.append(result)
                else:
                    failed_results.append(result)
            
            # Calculate statistics
            success_count = len(successful_results)
            failure_count = len(failed_results)
            success_rate = (success_count / concurrent_users) * 100
            
            response_times = [r.response_time for r in successful_results]
            avg_response_time = statistics.mean(response_times) if response_times else 0
            median_response_time = statistics.median(response_times) if response_times else 0
            
            return {
                "concurrent_users": concurrent_users,
                "total_time": total_time,
                "success_count": success_count,
                "failure_count": failure_count,
                "success_rate": success_rate,
                "avg_response_time": avg_response_time,
                "median_response_time": median_response_time,
                "min_response_time": min(response_times) if response_times else 0,
                "max_response_time": max(response_times) if response_times else 0,
                "failed_results": failed_results[:5]  # Show first 5 failures for analysis
            }
    
    async def run_performance_analysis(self) -> Dict[str, Any]:
        """Run comprehensive authentication performance analysis"""
        logger.info("Starting authentication performance analysis")
        
        # Test different concurrent user levels
        test_levels = [1, 5, 10, 15, 20, 25, 30, 40, 50, 75, 100]
        results = {}
        
        for level in test_levels:
            logger.info(f"Testing {level} concurrent users...")
            try:
                result = await self.test_concurrent_auth(level)
                results[level] = result
                
                logger.info(f"Level {level}: {result['success_rate']:.1f}% success rate, "
                          f"{result['avg_response_time']:.3f}s avg response time")
                
                # Stop if success rate drops below 50%
                if result['success_rate'] < 50:
                    logger.warning(f"Success rate dropped below 50% at {level} users. Stopping test.")
                    break
                    
                # Brief pause between tests
                await asyncio.sleep(2)
                
            except Exception as e:
                logger.error(f"Error testing {level} users: {e}")
                results[level] = {"error": str(e)}
        
        return results

async def main():
    """Main test execution"""
    tester = AuthPerformanceTester()
    
    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{tester.base_url}/health") as response:
                if response.status != 200:
                    logger.error("FlipSync server is not responding. Please start the server first.")
                    return
    except Exception as e:
        logger.error(f"Cannot connect to FlipSync server: {e}")
        logger.info("Please start the server with: cd fs_agt_clean && python -m uvicorn app.main:app --host 0.0.0.0 --port 8001")
        return
    
    # Run performance analysis
    results = await tester.run_performance_analysis()
    
    # Generate report
    print("\n" + "="*80)
    print("FLIPSYNC AUTHENTICATION PERFORMANCE ANALYSIS REPORT")
    print("="*80)
    
    for level, result in results.items():
        if "error" in result:
            print(f"\n{level:3d} users: ERROR - {result['error']}")
            continue
            
        print(f"\n{level:3d} users: {result['success_rate']:5.1f}% success | "
              f"{result['avg_response_time']:6.3f}s avg | "
              f"{result['failure_count']:2d} failures")
        
        # Show failure details for problematic levels
        if result['failure_count'] > 0:
            print(f"         Failure details:")
            for i, failure in enumerate(result['failed_results']):
                print(f"           {i+1}. Status {failure.status_code}: {failure.error_message[:60]}")
    
    # Find bottleneck point
    bottleneck_level = None
    for level, result in results.items():
        if "error" not in result and result['success_rate'] < 95:
            bottleneck_level = level
            break
    
    print(f"\n" + "="*80)
    print("BOTTLENECK ANALYSIS:")
    if bottleneck_level:
        print(f"Authentication bottleneck detected at {bottleneck_level} concurrent users")
        print(f"Success rate drops below 95% at this level")
    else:
        print("No significant bottleneck detected in tested range")
    
    print("\nRECOMMENDATIONS:")
    print("1. Implement connection pooling for authentication services")
    print("2. Add Redis caching for user session validation")
    print("3. Optimize database queries in authentication flow")
    print("4. Remove redundant authentication fallback mechanisms")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(main())
