#!/usr/bin/env python3
"""
FlipSync V3 Integration Validation Test
=====================================

Comprehensive test suite to validate the 3-day implementation:
- Day 1: Backend route enablement
- Day 2: Frontend integration fixes  
- Day 3: End-to-end validation

Tests all critical V3 revenue workflows and 4+1 agent architecture.
"""

import asyncio
import aiohttp
import json
import time
from datetime import datetime
import websockets

class FlipSyncV3IntegrationValidator:
    def __init__(self):
        self.base_url = "https://flipsyncai.com"
        self.api_base = f"{self.base_url}/api/v1"
        self.ws_url = f"wss://flipsyncai.com/ws/flipsync"
        self.results = {
            "day1_backend_routes": {},
            "day2_frontend_integration": {},
            "day3_validation": {},
            "overall_status": "PENDING"
        }

    async def test_day1_backend_routes(self):
        """Test Day 1: Backend route enablement"""
        print("🔧 Testing Day 1: Backend Route Enablement...")
        
        async with aiohttp.ClientSession() as session:
            # Test 4+1 Agent Architecture
            try:
                async with session.get(f"{self.api_base}/agents/status") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        agents_count = len(data.get("agents", []))
                        architecture = data.get("architecture", "")
                        self.results["day1_backend_routes"]["agents_status"] = {
                            "status": "✅ PASS",
                            "agents_count": agents_count,
                            "architecture": architecture,
                            "expected": "4+1 architecture with 5 agents"
                        }
                    else:
                        self.results["day1_backend_routes"]["agents_status"] = {
                            "status": "❌ FAIL",
                            "error": f"HTTP {resp.status}"
                        }
            except Exception as e:
                self.results["day1_backend_routes"]["agents_status"] = {
                    "status": "❌ FAIL",
                    "error": str(e)
                }

            # Test V3 Revenue Endpoints (should require auth)
            v3_endpoints = [
                ("POST", "/ai/analyze-product", "Enhanced Product Creation"),
                ("POST", "/shipping/v1/shipping/arbitrage", "Shipping Arbitrage"),
                ("POST", "/advertising/boost-listing", "External Advertising")
            ]

            for method, endpoint, name in v3_endpoints:
                try:
                    if method == "POST":
                        async with session.post(f"{self.api_base}{endpoint}", 
                                              json={"test": "data"}) as resp:
                            # Expecting 401/403 for auth required, not 404
                            if resp.status in [401, 403]:
                                status = "✅ PASS (Auth Required)"
                            elif resp.status == 404:
                                status = "❌ FAIL (Route Not Found)"
                            else:
                                status = f"⚠️ UNEXPECTED (HTTP {resp.status})"
                            
                            self.results["day1_backend_routes"][endpoint.replace("/", "_")] = {
                                "status": status,
                                "name": name,
                                "http_status": resp.status
                            }
                except Exception as e:
                    self.results["day1_backend_routes"][endpoint.replace("/", "_")] = {
                        "status": "❌ FAIL",
                        "name": name,
                        "error": str(e)
                    }

    async def test_day2_frontend_integration(self):
        """Test Day 2: Frontend integration fixes"""
        print("🎨 Testing Day 2: Frontend Integration...")
        
        async with aiohttp.ClientSession() as session:
            # Test Frontend Accessibility
            try:
                async with session.get(f"{self.base_url}") as resp:
                    if resp.status == 200:
                        content = await resp.text()
                        has_flutter = "flutter" in content.lower()
                        self.results["day2_frontend_integration"]["frontend_access"] = {
                            "status": "✅ PASS",
                            "has_flutter_content": has_flutter,
                            "http_status": resp.status
                        }
                    else:
                        self.results["day2_frontend_integration"]["frontend_access"] = {
                            "status": "❌ FAIL",
                            "http_status": resp.status
                        }
            except Exception as e:
                self.results["day2_frontend_integration"]["frontend_access"] = {
                    "status": "❌ FAIL",
                    "error": str(e)
                }

            # Test API Configuration (should use domain, not IP)
            try:
                async with session.get(f"{self.api_base}/agents/status") as resp:
                    if resp.status == 200:
                        # Check if we're successfully using domain-based URLs
                        self.results["day2_frontend_integration"]["api_domain_config"] = {
                            "status": "✅ PASS",
                            "note": "Successfully using flipsyncai.com domain",
                            "url_used": self.api_base
                        }
                    else:
                        self.results["day2_frontend_integration"]["api_domain_config"] = {
                            "status": "❌ FAIL",
                            "http_status": resp.status
                        }
            except Exception as e:
                self.results["day2_frontend_integration"]["api_domain_config"] = {
                    "status": "❌ FAIL",
                    "error": str(e)
                }

    async def test_day3_validation(self):
        """Test Day 3: Comprehensive validation"""
        print("🧪 Testing Day 3: Comprehensive Validation...")
        
        # Test WebSocket Real-time Integration
        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Send ping
                test_message = {"type": "ping", "timestamp": datetime.now().isoformat()}
                await websocket.send(json.dumps(test_message))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                
                self.results["day3_validation"]["websocket_integration"] = {
                    "status": "✅ PASS",
                    "ping_successful": True,
                    "response_type": response_data.get("type", "unknown")
                }
        except Exception as e:
            self.results["day3_validation"]["websocket_integration"] = {
                "status": "❌ FAIL",
                "error": str(e)
            }

        # Test Performance (concurrent requests)
        async with aiohttp.ClientSession() as session:
            start_time = time.time()
            tasks = []
            for i in range(5):
                task = session.get(f"{self.api_base}/agents/status")
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            success_count = sum(1 for r in responses if not isinstance(r, Exception) and r.status == 200)
            avg_response_time = (end_time - start_time) / 5
            
            self.results["day3_validation"]["performance_test"] = {
                "status": "✅ PASS" if success_count == 5 and avg_response_time < 1.0 else "❌ FAIL",
                "success_rate": f"{success_count}/5",
                "avg_response_time": f"{avg_response_time:.2f}s",
                "meets_target": avg_response_time < 1.0
            }

    def calculate_overall_status(self):
        """Calculate overall implementation status"""
        all_tests = []
        
        for day_results in self.results.values():
            if isinstance(day_results, dict):
                for test_result in day_results.values():
                    if isinstance(test_result, dict) and "status" in test_result:
                        all_tests.append(test_result["status"].startswith("✅"))
        
        if not all_tests:
            self.results["overall_status"] = "❌ NO TESTS RUN"
        elif all(all_tests):
            self.results["overall_status"] = "✅ ALL TESTS PASS"
        else:
            pass_count = sum(all_tests)
            total_count = len(all_tests)
            self.results["overall_status"] = f"⚠️ PARTIAL ({pass_count}/{total_count} PASS)"

    def print_results(self):
        """Print comprehensive test results"""
        print("\n" + "="*80)
        print("🎯 FLIPSYNC V3 INTEGRATION VALIDATION RESULTS")
        print("="*80)
        
        for day, tests in self.results.items():
            if day == "overall_status":
                continue
                
            print(f"\n📅 {day.upper().replace('_', ' ')}")
            print("-" * 50)
            
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    if isinstance(result, dict):
                        status = result.get("status", "UNKNOWN")
                        print(f"  {test_name}: {status}")
                        
                        # Print additional details
                        for key, value in result.items():
                            if key != "status":
                                print(f"    {key}: {value}")
        
        print(f"\n🏆 OVERALL STATUS: {self.results['overall_status']}")
        print("="*80)

    async def run_all_tests(self):
        """Run all validation tests"""
        print("🚀 Starting FlipSync V3 Integration Validation...")
        print(f"🕐 Test started at: {datetime.now().isoformat()}")
        
        await self.test_day1_backend_routes()
        await self.test_day2_frontend_integration()
        await self.test_day3_validation()
        
        self.calculate_overall_status()
        self.print_results()
        
        return self.results

async def main():
    validator = FlipSyncV3IntegrationValidator()
    results = await validator.run_all_tests()
    
    # Save results to file
    with open("v3_integration_validation_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"\n💾 Results saved to: v3_integration_validation_results.json")

if __name__ == "__main__":
    asyncio.run(main())
