#!/usr/bin/env python3
"""
FlipSync Production Performance & Load Testing
Tests performance targets and concurrent user handling for the sophisticated 35+ agent system
"""

import asyncio
import aiohttp
import time
import statistics
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import threading

class ProductionPerformanceTest:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.results = {
            "response_times": [],
            "success_count": 0,
            "error_count": 0,
            "concurrent_users": 0
        }
        
    async def single_request(self, session, endpoint="/health"):
        """Make a single request and measure performance"""
        start_time = time.time()
        try:
            async with session.get(f"{self.base_url}{endpoint}") as response:
                await response.text()
                response_time = time.time() - start_time
                
                if response.status == 200:
                    self.results["success_count"] += 1
                    self.results["response_times"].append(response_time)
                    return {"status": "success", "response_time": response_time}
                else:
                    self.results["error_count"] += 1
                    return {"status": "error", "code": response.status}
                    
        except Exception as e:
            self.results["error_count"] += 1
            return {"status": "error", "error": str(e)}
    
    async def load_test(self, concurrent_users=50, requests_per_user=10):
        """Run load test with concurrent users"""
        print(f"🚀 Starting load test: {concurrent_users} concurrent users, {requests_per_user} requests each")
        
        self.results["concurrent_users"] = concurrent_users
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # Create tasks for concurrent users
            for user in range(concurrent_users):
                for request in range(requests_per_user):
                    # Mix different endpoints
                    endpoints = ["/health", "/api/v1/agents/", "/api/v1/chat/", "/api/v1/marketplace/products"]
                    endpoint = endpoints[request % len(endpoints)]
                    tasks.append(self.single_request(session, endpoint))
            
            # Execute all requests concurrently
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            return {
                "total_requests": len(tasks),
                "total_time": total_time,
                "requests_per_second": len(tasks) / total_time,
                "results": results
            }
    
    def analyze_performance(self, load_results):
        """Analyze performance metrics"""
        response_times = self.results["response_times"]
        
        if not response_times:
            return {"error": "No successful responses to analyze"}
        
        analysis = {
            "total_requests": load_results["total_requests"],
            "successful_requests": self.results["success_count"],
            "failed_requests": self.results["error_count"],
            "success_rate": (self.results["success_count"] / load_results["total_requests"]) * 100,
            "concurrent_users": self.results["concurrent_users"],
            "requests_per_second": load_results["requests_per_second"],
            "response_times": {
                "min": min(response_times),
                "max": max(response_times),
                "avg": statistics.mean(response_times),
                "median": statistics.median(response_times),
                "p95": sorted(response_times)[int(len(response_times) * 0.95)] if len(response_times) > 20 else max(response_times),
                "p99": sorted(response_times)[int(len(response_times) * 0.99)] if len(response_times) > 100 else max(response_times)
            }
        }
        
        return analysis
    
    def evaluate_production_readiness(self, analysis):
        """Evaluate against production targets"""
        targets = {
            "success_rate": 95.0,  # >95% success rate
            "avg_response_time": 1.0,  # <1s average response time
            "p95_response_time": 2.0,  # <2s 95th percentile
            "requests_per_second": 100,  # >100 requests/second
            "concurrent_users": 50  # Handle 50+ concurrent users
        }
        
        evaluation = {}
        score = 0
        max_score = len(targets)
        
        # Success Rate
        if analysis["success_rate"] >= targets["success_rate"]:
            evaluation["success_rate"] = "PASS"
            score += 1
        else:
            evaluation["success_rate"] = "FAIL"
        
        # Average Response Time
        if analysis["response_times"]["avg"] <= targets["avg_response_time"]:
            evaluation["avg_response_time"] = "PASS"
            score += 1
        else:
            evaluation["avg_response_time"] = "FAIL"
        
        # 95th Percentile Response Time
        if analysis["response_times"]["p95"] <= targets["p95_response_time"]:
            evaluation["p95_response_time"] = "PASS"
            score += 1
        else:
            evaluation["p95_response_time"] = "FAIL"
        
        # Requests Per Second
        if analysis["requests_per_second"] >= targets["requests_per_second"]:
            evaluation["requests_per_second"] = "PASS"
            score += 1
        else:
            evaluation["requests_per_second"] = "FAIL"
        
        # Concurrent Users
        if analysis["concurrent_users"] >= targets["concurrent_users"]:
            evaluation["concurrent_users"] = "PASS"
            score += 1
        else:
            evaluation["concurrent_users"] = "FAIL"
        
        evaluation["score"] = score
        evaluation["max_score"] = max_score
        evaluation["percentage"] = (score / max_score) * 100
        evaluation["targets"] = targets
        
        return evaluation
    
    async def run_performance_test(self):
        """Run complete performance test suite"""
        print("⚡ FLIPSYNC PRODUCTION PERFORMANCE TEST")
        print("=" * 50)
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Base URL: {self.base_url}")
        print()
        
        # Run load test
        load_results = await self.load_test(concurrent_users=50, requests_per_user=10)
        
        # Analyze results
        analysis = self.analyze_performance(load_results)
        
        # Evaluate against production targets
        evaluation = self.evaluate_production_readiness(analysis)
        
        # Display results
        print("📊 PERFORMANCE RESULTS")
        print("=" * 30)
        print(f"📈 Total Requests: {analysis['total_requests']}")
        print(f"✅ Successful: {analysis['successful_requests']}")
        print(f"❌ Failed: {analysis['failed_requests']}")
        print(f"📊 Success Rate: {analysis['success_rate']:.1f}%")
        print(f"👥 Concurrent Users: {analysis['concurrent_users']}")
        print(f"⚡ Requests/Second: {analysis['requests_per_second']:.1f}")
        print()
        
        print("⏱️  RESPONSE TIME ANALYSIS")
        print("=" * 30)
        print(f"🚀 Average: {analysis['response_times']['avg']:.3f}s")
        print(f"📊 Median: {analysis['response_times']['median']:.3f}s")
        print(f"⚡ Min: {analysis['response_times']['min']:.3f}s")
        print(f"🔥 Max: {analysis['response_times']['max']:.3f}s")
        print(f"📈 95th Percentile: {analysis['response_times']['p95']:.3f}s")
        print(f"🎯 99th Percentile: {analysis['response_times']['p99']:.3f}s")
        print()
        
        print("🎯 PRODUCTION READINESS EVALUATION")
        print("=" * 40)
        targets = evaluation["targets"]
        
        print(f"✅ Success Rate: {evaluation['success_rate']} (Target: ≥{targets['success_rate']}%, Actual: {analysis['success_rate']:.1f}%)")
        print(f"⚡ Avg Response Time: {evaluation['avg_response_time']} (Target: ≤{targets['avg_response_time']}s, Actual: {analysis['response_times']['avg']:.3f}s)")
        print(f"📊 95th Percentile: {evaluation['p95_response_time']} (Target: ≤{targets['p95_response_time']}s, Actual: {analysis['response_times']['p95']:.3f}s)")
        print(f"🚀 Requests/Second: {evaluation['requests_per_second']} (Target: ≥{targets['requests_per_second']}, Actual: {analysis['requests_per_second']:.1f})")
        print(f"👥 Concurrent Users: {evaluation['concurrent_users']} (Target: ≥{targets['concurrent_users']}, Actual: {analysis['concurrent_users']})")
        print()
        
        print("🏆 FINAL SCORE")
        print("=" * 20)
        print(f"📊 Score: {evaluation['score']}/{evaluation['max_score']}")
        print(f"📈 Percentage: {evaluation['percentage']:.1f}%")
        
        if evaluation["percentage"] >= 100:
            print("🎉 EXCELLENT - EXCEEDS ALL PRODUCTION TARGETS!")
        elif evaluation["percentage"] >= 80:
            print("✅ GOOD - MEETS PRODUCTION REQUIREMENTS")
        elif evaluation["percentage"] >= 60:
            print("⚠️  ACCEPTABLE - MINOR OPTIMIZATIONS NEEDED")
        else:
            print("❌ NEEDS IMPROVEMENT - SIGNIFICANT OPTIMIZATIONS REQUIRED")
        
        return evaluation

async def main():
    tester = ProductionPerformanceTest()
    await tester.run_performance_test()

if __name__ == "__main__":
    asyncio.run(main())
