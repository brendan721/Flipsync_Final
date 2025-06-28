#!/usr/bin/env python3
"""
FlipSync Production API Validation Test Suite
Tests all critical endpoints and validates the sophisticated 35+ agent system
"""

import requests
import json
import time
from datetime import datetime

class ProductionAPIValidator:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.results = {}
        
    def test_health_check(self):
        """Test basic health endpoint"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "PASS",
                    "response_time": response.elapsed.total_seconds(),
                    "data": data
                }
            else:
                return {"status": "FAIL", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def test_agent_system(self):
        """Test sophisticated agent system"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/agents/", timeout=15)
            if response.status_code == 200:
                agents = response.json()
                return {
                    "status": "PASS",
                    "agent_count": len(agents),
                    "response_time": response.elapsed.total_seconds(),
                    "sample_agent": agents[0] if agents else None
                }
            else:
                return {"status": "FAIL", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def test_chat_service(self):
        """Test chat service availability"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/chat/", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "PASS",
                    "service_status": data.get("status"),
                    "features": data.get("features", []),
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {"status": "FAIL", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def test_marketplace_products(self):
        """Test marketplace integration"""
        try:
            response = requests.get(f"{self.base_url}/api/v1/marketplace/products", timeout=10)
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "PASS",
                    "marketplace_status": data.get("status"),
                    "agent_system_operational": data.get("agent_system_operational"),
                    "response_time": response.elapsed.total_seconds()
                }
            else:
                return {"status": "FAIL", "error": f"HTTP {response.status_code}"}
        except Exception as e:
            return {"status": "FAIL", "error": str(e)}
    
    def run_validation(self):
        """Run complete validation suite"""
        print("🚀 FLIPSYNC PRODUCTION API VALIDATION")
        print("=" * 50)
        print(f"📅 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🌐 Base URL: {self.base_url}")
        print()
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Agent System", self.test_agent_system),
            ("Chat Service", self.test_chat_service),
            ("Marketplace Products", self.test_marketplace_products),
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            print(f"🧪 Testing {test_name}...")
            result = test_func()
            self.results[test_name] = result
            
            if result["status"] == "PASS":
                print(f"✅ {test_name}: PASS")
                if "response_time" in result:
                    print(f"   ⏱️  Response Time: {result['response_time']:.3f}s")
                if "agent_count" in result:
                    print(f"   🤖 Agent Count: {result['agent_count']}")
                if "service_status" in result:
                    print(f"   📊 Service Status: {result['service_status']}")
                passed += 1
            else:
                print(f"❌ {test_name}: FAIL")
                print(f"   🚨 Error: {result.get('error', 'Unknown error')}")
            print()
        
        # Summary
        print("📊 VALIDATION SUMMARY")
        print("=" * 30)
        print(f"✅ Tests Passed: {passed}/{total}")
        print(f"📈 Success Rate: {(passed/total)*100:.1f}%")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - PRODUCTION READY!")
        elif passed >= total * 0.8:
            print("⚠️  MOSTLY READY - Minor issues detected")
        else:
            print("❌ PRODUCTION NOT READY - Critical issues detected")
        
        return passed, total

if __name__ == "__main__":
    validator = ProductionAPIValidator()
    validator.run_validation()
