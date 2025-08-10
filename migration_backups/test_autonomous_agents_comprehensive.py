#!/usr/bin/env python3
"""
Comprehensive Autonomous Agent Testing
=====================================
Test the 4+1 autonomous agent system for decision-making and learning capabilities.
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any

import requests

BASE_URL = "http://174.138.77.110:8000"

class AutonomousAgentTester:
    def __init__(self):
        self.token = None
        self.headers = {}
        
    def print_test_header(self, test_name: str):
        print(f"\n{'='*60}")
        print(f"🤖 {test_name}")
        print(f"{'='*60}")

    def print_result(self, test_name: str, success: bool, details: str = ""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")

    def authenticate(self) -> bool:
        """Authenticate and get access token."""
        self.print_test_header("Authentication Setup")
        
        login_data = {
            "email": "test@example.com",
            "password": "SecurePassword!"
        }
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                
                user_id = token_data.get("user", {}).get("id")
                self.print_result("Authentication", True, f"User ID: {user_id}")
                return True
            else:
                self.print_result("Authentication", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.print_result("Authentication", False, f"Error: {e}")
            return False

    def test_agent_endpoints(self) -> Dict[str, bool]:
        """Test 4+1 architecture agent endpoints."""
        self.print_test_header("4+1 Architecture Agent Endpoints")
        
        results = {}
        
        # Test agent status endpoint
        try:
            response = requests.get(f"{BASE_URL}/api/v1/agents/4plus1/agents/", headers=self.headers)
            if response.status_code == 200:
                agents = response.json()
                self.print_result("Agent status endpoint", True, f"Found {len(agents)} agents")
                results["agent_status"] = True
            else:
                self.print_result("Agent status endpoint", False, f"HTTP {response.status_code}")
                results["agent_status"] = False
        except Exception as e:
            self.print_result("Agent status endpoint", False, f"Error: {e}")
            results["agent_status"] = False
        
        # Test agent registration endpoint
        try:
            response = requests.get(f"{BASE_URL}/api/v1/agents/4plus1/registration/", headers=self.headers)
            if response.status_code == 200:
                registration = response.json()
                self.print_result("Agent registration", True, f"Status: {registration.get('status')}")
                results["agent_registration"] = True
            else:
                self.print_result("Agent registration", False, f"HTTP {response.status_code}")
                results["agent_registration"] = False
        except Exception as e:
            self.print_result("Agent registration", False, f"Error: {e}")
            results["agent_registration"] = False
            
        return results

    def test_decision_system(self) -> Dict[str, bool]:
        """Test autonomous decision-making system."""
        self.print_test_header("Autonomous Decision System")
        
        results = {}
        
        # Test decision pipeline endpoint
        try:
            response = requests.get(f"{BASE_URL}/api/v1/decisions/4plus1/pipeline/", headers=self.headers)
            if response.status_code == 200:
                pipeline = response.json()
                self.print_result("Decision pipeline", True, f"Status: {pipeline.get('status')}")
                results["decision_pipeline"] = True
            else:
                self.print_result("Decision pipeline", False, f"HTTP {response.status_code}")
                results["decision_pipeline"] = False
        except Exception as e:
            self.print_result("Decision pipeline", False, f"Error: {e}")
            results["decision_pipeline"] = False
        
        # Test decision history
        try:
            response = requests.get(f"{BASE_URL}/api/v1/decisions/4plus1/history/", headers=self.headers)
            if response.status_code == 200:
                history = response.json()
                decision_count = len(history) if isinstance(history, list) else history.get('total', 0)
                self.print_result("Decision history", True, f"Found {decision_count} decisions")
                results["decision_history"] = True
            else:
                self.print_result("Decision history", False, f"HTTP {response.status_code}")
                results["decision_history"] = False
        except Exception as e:
            self.print_result("Decision history", False, f"Error: {e}")
            results["decision_history"] = False
            
        return results

    def test_learning_system(self) -> Dict[str, bool]:
        """Test autonomous learning capabilities."""
        self.print_test_header("Autonomous Learning System")
        
        results = {}
        
        # Test learning data endpoint
        try:
            response = requests.get(f"{BASE_URL}/api/v1/decisions/4plus1/learning/", headers=self.headers)
            if response.status_code == 200:
                learning = response.json()
                learning_count = len(learning) if isinstance(learning, list) else learning.get('total', 0)
                self.print_result("Learning data", True, f"Found {learning_count} learning records")
                results["learning_data"] = True
            else:
                self.print_result("Learning data", False, f"HTTP {response.status_code}")
                results["learning_data"] = False
        except Exception as e:
            self.print_result("Learning data", False, f"Error: {e}")
            results["learning_data"] = False
        
        # Test learning metrics
        try:
            response = requests.get(f"{BASE_URL}/api/v1/decisions/4plus1/metrics/", headers=self.headers)
            if response.status_code == 200:
                metrics = response.json()
                self.print_result("Learning metrics", True, f"Metrics available: {list(metrics.keys())}")
                results["learning_metrics"] = True
            else:
                self.print_result("Learning metrics", False, f"HTTP {response.status_code}")
                results["learning_metrics"] = False
        except Exception as e:
            self.print_result("Learning metrics", False, f"Error: {e}")
            results["learning_metrics"] = False
            
        return results

    def test_agent_decision_making(self) -> Dict[str, bool]:
        """Test agent decision-making capabilities."""
        self.print_test_header("Agent Decision Making Test")
        
        results = {}
        
        # Test triggering a decision
        try:
            decision_request = {
                "agent_type": "market_agent",
                "context": {
                    "product_id": "test_product_123",
                    "action": "price_optimization",
                    "current_price": 29.99,
                    "competitor_prices": [25.99, 32.99, 28.50]
                },
                "priority": "high"
            }
            
            response = requests.post(
                f"{BASE_URL}/api/v1/decisions/4plus1/trigger/",
                json=decision_request,
                headers=self.headers
            )
            
            if response.status_code in [200, 201]:
                decision = response.json()
                decision_id = decision.get("decision_id")
                self.print_result("Trigger decision", True, f"Decision ID: {decision_id}")
                results["trigger_decision"] = True
                
                # Wait a moment for decision processing
                time.sleep(2)
                
                # Check decision status
                if decision_id:
                    status_response = requests.get(
                        f"{BASE_URL}/api/v1/decisions/4plus1/status/{decision_id}",
                        headers=self.headers
                    )
                    if status_response.status_code == 200:
                        status = status_response.json()
                        self.print_result("Decision status", True, f"Status: {status.get('status')}")
                        results["decision_status"] = True
                    else:
                        self.print_result("Decision status", False, f"HTTP {status_response.status_code}")
                        results["decision_status"] = False
                        
            else:
                self.print_result("Trigger decision", False, f"HTTP {response.status_code}")
                results["trigger_decision"] = False
                results["decision_status"] = False
                
        except Exception as e:
            self.print_result("Trigger decision", False, f"Error: {e}")
            results["trigger_decision"] = False
            results["decision_status"] = False
            
        return results

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive autonomous agent testing."""
        print("🚀 Starting Comprehensive Autonomous Agent Testing")
        print(f"📍 Backend URL: {BASE_URL}")
        
        # Authenticate first
        if not self.authenticate():
            return {"error": "Authentication failed"}
        
        # Run all tests
        all_results = {}
        
        all_results.update(self.test_agent_endpoints())
        all_results.update(self.test_decision_system())
        all_results.update(self.test_learning_system())
        all_results.update(self.test_agent_decision_making())
        
        return all_results

def main():
    """Main testing function."""
    tester = AutonomousAgentTester()
    results = tester.run_comprehensive_test()
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 AUTONOMOUS AGENT TESTING SUMMARY")
    print(f"{'='*60}")
    
    if "error" in results:
        print(f"❌ Testing failed: {results['error']}")
        return 1
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Results: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL AUTONOMOUS AGENT TESTS PASSED!")
        return 0
    else:
        print("⚠️ Some autonomous agent tests failed")
        return 1

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)
