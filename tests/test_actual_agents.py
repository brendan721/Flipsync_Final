#!/usr/bin/env python3
"""
Test Actual FlipSync Autonomous Agents
=====================================
Test the real agent endpoints that exist in the system.
"""

import json
import time
from datetime import datetime, timezone

import requests

BASE_URL = "http://localhost:8000"

class FlipSyncAgentTester:
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

    def test_agent_system(self):
        """Test the actual agent system endpoints."""
        self.print_test_header("FlipSync Agent System")
        
        # Test 4+1 architecture status
        try:
            response = requests.get(f"{BASE_URL}/api/v1/agents/4plus1/", headers=self.headers)
            if response.status_code == 200:
                data = response.json()
                self.print_result("4+1 Architecture Status", True, f"Response: {json.dumps(data, indent=2)}")
            else:
                self.print_result("4+1 Architecture Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_result("4+1 Architecture Status", False, f"Error: {e}")
        
        # Test 4+1 health
        try:
            response = requests.get(f"{BASE_URL}/api/v1/agents/4plus1/health", headers=self.headers)
            if response.status_code == 200:
                health = response.json()
                self.print_result("4+1 Health Check", True, f"Status: {health.get('status')}")
            else:
                self.print_result("4+1 Health Check", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_result("4+1 Health Check", False, f"Error: {e}")
        
        # Test agent list
        try:
            response = requests.get(f"{BASE_URL}/api/v1/agents/4plus1/list", headers=self.headers)
            if response.status_code == 200:
                agents = response.json()
                agent_count = len(agents) if isinstance(agents, list) else agents.get('count', 0)
                self.print_result("Agent List", True, f"Found {agent_count} agents")
                if isinstance(agents, list) and agents:
                    print(f"   📋 Agents: {[agent.get('name', agent.get('id', 'unknown')) for agent in agents[:3]]}")
            else:
                self.print_result("Agent List", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_result("Agent List", False, f"Error: {e}")
        
        # Test system metrics
        try:
            response = requests.get(f"{BASE_URL}/api/v1/agents/4plus1/metrics/system", headers=self.headers)
            if response.status_code == 200:
                metrics = response.json()
                self.print_result("System Metrics", True, f"Metrics: {list(metrics.keys())}")
            else:
                self.print_result("System Metrics", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_result("System Metrics", False, f"Error: {e}")

    def test_agent_monitoring(self):
        """Test agent monitoring system."""
        self.print_test_header("Agent Monitoring System")
        
        # Test monitoring status
        try:
            response = requests.get(f"{BASE_URL}/api/v1/agent-monitoring/status", headers=self.headers)
            if response.status_code == 200:
                status = response.json()
                self.print_result("Monitoring Status", True, f"Status: {status.get('status')}")
            else:
                self.print_result("Monitoring Status", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_result("Monitoring Status", False, f"Error: {e}")
        
        # Test monitoring metrics
        try:
            response = requests.get(f"{BASE_URL}/api/v1/agent-monitoring/metrics", headers=self.headers)
            if response.status_code == 200:
                metrics = response.json()
                self.print_result("Monitoring Metrics", True, f"Metrics available: {list(metrics.keys())}")
            else:
                self.print_result("Monitoring Metrics", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_result("Monitoring Metrics", False, f"Error: {e}")
        
        # Test dashboard
        try:
            response = requests.get(f"{BASE_URL}/api/v1/agent-monitoring/dashboard", headers=self.headers)
            if response.status_code == 200:
                dashboard = response.json()
                self.print_result("Monitoring Dashboard", True, f"Dashboard data available")
            else:
                self.print_result("Monitoring Dashboard", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_result("Monitoring Dashboard", False, f"Error: {e}")

    def test_decision_system(self):
        """Test decision-making capabilities."""
        self.print_test_header("Decision System Testing")
        
        # Check for decision endpoints
        decision_endpoints = [
            "/api/v1/decisions/",
            "/api/v1/decisions/history",
            "/api/v1/decisions/metrics",
            "/api/v1/decisions/pipeline"
        ]
        
        for endpoint in decision_endpoints:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    self.print_result(f"Decision endpoint {endpoint}", True, f"Data available")
                elif response.status_code == 404:
                    self.print_result(f"Decision endpoint {endpoint}", False, "Not implemented")
                else:
                    self.print_result(f"Decision endpoint {endpoint}", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.print_result(f"Decision endpoint {endpoint}", False, f"Error: {e}")

    def test_database_connectivity(self):
        """Test database connectivity and data."""
        self.print_test_header("Database Connectivity")
        
        # Test if we can access any data endpoints
        data_endpoints = [
            "/api/v1/agents/",
            "/api/v1/agents/list",
            "/api/v1/agents/status"
        ]
        
        for endpoint in data_endpoints:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    self.print_result(f"Data endpoint {endpoint}", True, f"Response received")
                else:
                    self.print_result(f"Data endpoint {endpoint}", False, f"HTTP {response.status_code}")
            except Exception as e:
                self.print_result(f"Data endpoint {endpoint}", False, f"Error: {e}")

    def run_comprehensive_test(self):
        """Run comprehensive testing."""
        print("🚀 Starting FlipSync Autonomous Agent Testing")
        print(f"📍 Backend URL: {BASE_URL}")
        
        # Authenticate first
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with agent testing")
            return
        
        # Run all tests
        self.test_agent_system()
        self.test_agent_monitoring()
        self.test_decision_system()
        self.test_database_connectivity()
        
        print(f"\n{'='*60}")
        print("🎯 TESTING COMPLETE")
        print(f"{'='*60}")

def main():
    """Main testing function."""
    tester = FlipSyncAgentTester()
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()
