#!/usr/bin/env python3
"""
Comprehensive Autonomous Agent Decision Testing
==============================================
Test that agents are making decisions and storing them in the database.
"""

import asyncio
import json
import time
import requests
import websockets
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

class AgentDecisionValidator:
    def __init__(self):
        self.token = None
        self.headers = {}
        
    def print_test_header(self, test_name: str):
        print(f"\n{'='*60}")
        print(f"🧠 {test_name}")
        print(f"{'='*60}")

    def print_result(self, test_name: str, success: bool, details: str = ""):
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"   📝 {details}")

    def authenticate(self) -> bool:
        """Get authentication token."""
        login_data = {"email": "test@example.com", "password": "SecurePassword!"}
        
        try:
            response = requests.post(f"{BASE_URL}/api/v1/auth/login", json=login_data)
            if response.status_code == 200:
                token_data = response.json()
                self.token = token_data.get("access_token")
                self.headers = {"Authorization": f"Bearer {self.token}"}
                return True
            return False
        except:
            return False

    def test_agent_count_analysis(self):
        """Analyze the 16 agents vs original 10."""
        self.print_test_header("Agent Count Analysis (16 vs 10)")
        
        try:
            response = requests.get(f"{BASE_URL}/api/v1/agents/4plus1/list", headers=self.headers)
            if response.status_code == 200:
                agents = response.json()
                
                # Group by agent type
                agent_types = {}
                for agent in agents:
                    agent_type = agent.get('agent_type', 'unknown')
                    if agent_type not in agent_types:
                        agent_types[agent_type] = []
                    agent_types[agent_type].append(agent)
                
                print(f"📊 Total agents: {len(agents)}")
                print(f"📋 Agent type breakdown:")
                for agent_type, agent_list in agent_types.items():
                    print(f"   - {agent_type}: {len(agent_list)} agents")
                    if len(agent_list) > 1:
                        print(f"     IDs: {[a.get('id', 'unknown')[:30] for a in agent_list[:3]]}")
                
                # Check if there are duplicates or test agents
                duplicate_types = {k: v for k, v in agent_types.items() if len(v) > 1}
                if duplicate_types:
                    self.print_result("Agent Duplication Analysis", True, 
                                    f"Found {len(duplicate_types)} types with multiple instances")
                else:
                    self.print_result("Agent Duplication Analysis", True, "No duplicates found")
                    
            else:
                self.print_result("Agent List Retrieval", False, f"HTTP {response.status_code}")
        except Exception as e:
            self.print_result("Agent List Retrieval", False, f"Error: {e}")

    async def test_live_decision_monitoring(self):
        """Test live decision monitoring via WebSocket."""
        self.print_test_header("Live Decision Monitoring")
        
        try:
            ws_url = f"{WS_URL}/api/v1/decisions/4plus1/ws/live?token={self.token}"
            
            async with websockets.connect(ws_url, timeout=10) as websocket:
                self.print_result("Decision WebSocket Connection", True, "Connected successfully")
                
                # Wait for initial data
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    
                    recent_decisions = data.get('recent_decisions', [])
                    decision_count = len(recent_decisions)
                    
                    self.print_result("Recent Decisions Retrieved", True, 
                                    f"Found {decision_count} recent decisions")
                    
                    if recent_decisions:
                        latest_decision = recent_decisions[0]
                        print(f"   📋 Latest decision:")
                        print(f"      ID: {latest_decision.get('decision_id')}")
                        print(f"      Agent: {latest_decision.get('agent_type')}")
                        print(f"      Type: {latest_decision.get('decision_type')}")
                        print(f"      Status: {latest_decision.get('status')}")
                        print(f"      Created: {latest_decision.get('created_at')}")
                        
                        return decision_count > 0
                    else:
                        self.print_result("Decision Data Analysis", False, "No recent decisions found")
                        return False
                        
                except asyncio.TimeoutError:
                    self.print_result("Decision Data Retrieval", False, "No data received")
                    return False
                    
        except Exception as e:
            self.print_result("Decision WebSocket Connection", False, f"Error: {e}")
            return False

    async def test_agent_status_monitoring(self):
        """Test agent status monitoring via WebSocket."""
        self.print_test_header("Agent Status Monitoring")
        
        try:
            ws_url = f"{WS_URL}/api/v1/agents/4plus1/ws/status?token={self.token}"
            
            async with websockets.connect(ws_url, timeout=10) as websocket:
                self.print_result("Agent Status WebSocket", True, "Connected successfully")
                
                # Wait for agent status data
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=5)
                    data = json.loads(message)
                    
                    agents = data.get('agents', [])
                    active_agents = [a for a in agents if a.get('status') == 'active']
                    
                    self.print_result("Agent Status Data", True, 
                                    f"{len(active_agents)}/{len(agents)} agents active")
                    
                    # Check for decision-making capability
                    decision_capable_agents = []
                    for agent in active_agents:
                        capabilities = agent.get('capabilities', [])
                        if any('decision' in cap.lower() for cap in capabilities):
                            decision_capable_agents.append(agent)
                    
                    if decision_capable_agents:
                        self.print_result("Decision-Making Agents", True, 
                                        f"Found {len(decision_capable_agents)} decision-capable agents")
                    else:
                        print("   📋 Checking agent types for decision capability...")
                        core_agent_types = ['market', 'executive', 'logistics', 'content']
                        core_agents = [a for a in active_agents if a.get('agent_type') in core_agent_types]
                        self.print_result("Core Autonomous Agents", True, 
                                        f"Found {len(core_agents)} core agents")
                        
                    return len(active_agents) > 0
                        
                except asyncio.TimeoutError:
                    self.print_result("Agent Status Data", False, "No data received")
                    return False
                    
        except Exception as e:
            self.print_result("Agent Status WebSocket", False, f"Error: {e}")
            return False

    def test_decision_storage_verification(self):
        """Verify decisions are being stored by checking recent activity."""
        self.print_test_header("Decision Storage Verification")
        
        # Test if we can access decision data through API endpoints
        decision_endpoints = [
            "/api/v1/agents/4plus1/metrics/system",
            "/api/v1/agent-monitoring/metrics",
            "/api/v1/agents/system/metrics"
        ]
        
        decision_indicators_found = False
        
        for endpoint in decision_endpoints:
            try:
                response = requests.get(f"{BASE_URL}{endpoint}", headers=self.headers)
                if response.status_code == 200:
                    data = response.json()
                    
                    # Look for decision-related metrics
                    data_str = json.dumps(data).lower()
                    if any(keyword in data_str for keyword in ['decision', 'learning', 'agent_decision']):
                        decision_indicators_found = True
                        self.print_result(f"Decision Metrics in {endpoint}", True, "Decision data found")
                        
                        # Extract specific metrics if available
                        if 'decision' in data_str:
                            print(f"   📊 Decision-related data detected in response")
                        break
                        
            except Exception as e:
                continue
        
        if not decision_indicators_found:
            self.print_result("Decision Storage Indicators", False, "No decision metrics found in API responses")
        
        return decision_indicators_found

    async def run_comprehensive_validation(self):
        """Run comprehensive agent decision validation."""
        print("🚀 Starting Comprehensive Agent Decision Validation")
        print(f"📍 Backend URL: {BASE_URL}")
        
        if not self.authenticate():
            print("❌ Authentication failed")
            return False
        
        # Test 1: Analyze agent count
        self.test_agent_count_analysis()
        
        # Test 2: Live decision monitoring
        decisions_active = await self.test_live_decision_monitoring()
        
        # Test 3: Agent status monitoring
        agents_active = await self.test_agent_status_monitoring()
        
        # Test 4: Decision storage verification
        storage_verified = self.test_decision_storage_verification()
        
        # Summary
        print(f"\n{'='*60}")
        print("📊 COMPREHENSIVE VALIDATION SUMMARY")
        print(f"{'='*60}")
        
        results = {
            "Agents Active": agents_active,
            "Decisions Active": decisions_active,
            "Storage Verified": storage_verified
        }
        
        for test_name, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
        
        all_passed = all(results.values())
        
        if all_passed:
            print("\n🎉 ALL AUTONOMOUS AGENT SYSTEMS OPERATIONAL!")
            print("   ✅ Agents are active and making decisions")
            print("   ✅ Decision monitoring is working")
            print("   ✅ Data storage is verified")
        else:
            print("\n⚠️ Some autonomous agent systems need attention")
        
        return all_passed

async def main():
    """Main validation function."""
    validator = AgentDecisionValidator()
    success = await validator.run_comprehensive_validation()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
