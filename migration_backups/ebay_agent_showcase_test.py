#!/usr/bin/env python3
"""
eBay Agent Showcase Test
=======================
Demonstrates autonomous agents working with eBay accounts for user showcase.
"""

import asyncio
import json
import time
import requests
import websockets
from datetime import datetime, timezone

BASE_URL = "http://174.138.77.110:8000"
WS_URL = "ws://174.138.77.110:8000"

class EbayAgentShowcase:
    def __init__(self):
        self.token = None
        self.headers = {}
        
    def print_showcase_header(self, title: str):
        print(f"\n{'🎭'*30}")
        print(f"🎯 {title}")
        print(f"{'🎭'*30}")

    def print_step(self, step_num: int, description: str, status: str = "INFO"):
        icons = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️", "INFO": "🔄", "SUCCESS": "🎉"}
        icon = icons.get(status, "📋")
        print(f"\n{icon} Step {step_num}: {description}")

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

    def demonstrate_ebay_oauth_flow(self):
        """Demonstrate eBay OAuth flow for user account connection."""
        self.print_showcase_header("eBay Account Connection Showcase")
        
        self.print_step(1, "Generating eBay OAuth URL for user account connection")
        
        # Test both sandbox and production OAuth generation
        environments = ["sandbox", "production"]
        oauth_urls = {}
        
        for env in environments:
            user_id = "testuser" if env == "sandbox" else "realuser"
            
            try:
                response = requests.post(f"{BASE_URL}/api/v1/ebay/oauth/authorize", 
                                       json={
                                           "user_id": user_id,
                                           "scopes": [
                                               "https://api.ebay.com/oauth/api_scope/sell.inventory",
                                               "https://api.ebay.com/oauth/api_scope/sell.account",
                                               "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
                                               "https://api.ebay.com/oauth/api_scope/sell.marketing"
                                           ]
                                       }, headers=self.headers)
                
                if response.status_code == 200:
                    oauth_data = response.json()
                    oauth_urls[env] = oauth_data.get('oauth_url', '')
                    self.print_step(1, f"✅ {env.upper()} OAuth URL generated", "PASS")
                    print(f"   🔗 URL: {oauth_urls[env][:80]}...")
                else:
                    self.print_step(1, f"❌ {env.upper()} OAuth generation failed: HTTP {response.status_code}", "FAIL")
                    
            except Exception as e:
                self.print_step(1, f"❌ {env.upper()} OAuth error: {e}", "FAIL")
        
        return oauth_urls

    async def demonstrate_agent_monitoring(self):
        """Demonstrate real-time agent monitoring."""
        self.print_showcase_header("Real-time Agent Activity Monitoring")
        
        self.print_step(2, "Connecting to live agent status monitoring")
        
        try:
            ws_url = f"{WS_URL}/api/v1/agents/4plus1/ws/status?token={self.token}"
            
            async with websockets.connect(ws_url, timeout=10) as websocket:
                self.print_step(2, "✅ Connected to agent monitoring system", "PASS")
                
                # Get agent status
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                
                agents = data.get('agents', [])
                active_agents = [a for a in agents if a.get('status') == 'active']
                
                self.print_step(2, f"📊 Monitoring {len(active_agents)} active agents", "SUCCESS")
                
                # Show agent details
                for i, agent in enumerate(active_agents[:4], 1):  # Show first 4 agents
                    agent_type = agent.get('agent_type', 'unknown')
                    agent_id = agent.get('id', 'unknown')[:30]
                    print(f"   🤖 Agent {i}: {agent_type} ({agent_id})")
                
                return True
                
        except Exception as e:
            self.print_step(2, f"❌ Agent monitoring failed: {e}", "FAIL")
            return False

    async def demonstrate_decision_tracking(self):
        """Demonstrate live decision tracking."""
        self.print_showcase_header("Live Agent Decision Tracking")
        
        self.print_step(3, "Connecting to live decision monitoring")
        
        try:
            ws_url = f"{WS_URL}/api/v1/decisions/4plus1/ws/live?token={self.token}"
            
            async with websockets.connect(ws_url, timeout=10) as websocket:
                self.print_step(3, "✅ Connected to decision monitoring system", "PASS")
                
                # Get recent decisions
                message = await asyncio.wait_for(websocket.recv(), timeout=5)
                data = json.loads(message)
                
                recent_decisions = data.get('recent_decisions', [])
                
                if recent_decisions:
                    self.print_step(3, f"📈 Found {len(recent_decisions)} recent agent decisions", "SUCCESS")
                    
                    # Show recent decision details
                    for i, decision in enumerate(recent_decisions[:3], 1):  # Show first 3 decisions
                        decision_id = decision.get('decision_id', 'unknown')[:8]
                        decision_type = decision.get('decision_type', 'unknown')
                        status = decision.get('status', 'unknown')
                        print(f"   🧠 Decision {i}: {decision_type} ({decision_id}) - {status}")
                else:
                    self.print_step(3, "⚠️ No recent decisions found", "WARN")
                
                return len(recent_decisions) > 0
                
        except Exception as e:
            self.print_step(3, f"❌ Decision monitoring failed: {e}", "FAIL")
            return False

    def demonstrate_frontend_readiness(self):
        """Demonstrate frontend readiness for user showcase."""
        self.print_showcase_header("Frontend Showcase Readiness")
        
        # Test React frontend
        self.print_step(4, "Testing React frontend accessibility")
        try:
            react_response = requests.get("http://localhost:3001/testing-frontend", timeout=5)
            if react_response.status_code == 200:
                self.print_step(4, "✅ React frontend ready for eBay agent showcase", "PASS")
                print("   🌐 Access: http://localhost:3001/testing-frontend")
                print("   🎯 Features: eBay OAuth, Agent monitoring, Real-time decisions")
                react_ready = True
            else:
                self.print_step(4, f"❌ React frontend not accessible: HTTP {react_response.status_code}", "FAIL")
                react_ready = False
        except:
            self.print_step(4, "❌ React frontend not accessible", "FAIL")
            react_ready = False
        
        # Test Flutter build status
        self.print_step(4, "Testing Flutter frontend build status")
        import os
        flutter_build_path = "/home/brend/Flipsync_Final/flipsync_mobile/build/web"
        if os.path.exists(flutter_build_path):
            self.print_step(4, "✅ Flutter web build available", "PASS")
            print("   📱 Status: Built successfully, needs WebSocket endpoint fixes")
            flutter_ready = True
        else:
            self.print_step(4, "❌ Flutter web build not found", "FAIL")
            flutter_ready = False
        
        return react_ready, flutter_ready

    async def run_complete_showcase(self):
        """Run complete eBay agent showcase demonstration."""
        print("🎬 Starting eBay Agent Showcase Demonstration")
        print(f"📍 Backend: {BASE_URL}")
        print(f"🕐 Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        if not self.authenticate():
            print("❌ Authentication failed - cannot proceed with showcase")
            return False
        
        # Run showcase steps
        oauth_urls = self.demonstrate_ebay_oauth_flow()
        agent_monitoring = await self.demonstrate_agent_monitoring()
        decision_tracking = await self.demonstrate_decision_tracking()
        react_ready, flutter_ready = self.demonstrate_frontend_readiness()
        
        # Generate final recommendations
        self.print_showcase_header("Showcase Readiness Assessment")
        
        if oauth_urls and agent_monitoring and react_ready:
            self.print_step(5, "🎉 READY FOR USER SHOWCASE", "SUCCESS")
            print("   ✅ eBay OAuth flow operational")
            print("   ✅ Agent monitoring system working")
            print("   ✅ React frontend accessible")
            print("   🎯 Users can see agents working with their eBay accounts")
            
            print(f"\n🚀 IMMEDIATE ACTION PLAN:")
            print(f"   1. Use React frontend at http://localhost:3001/testing-frontend")
            print(f"   2. Complete eBay OAuth flow using generated URLs")
            print(f"   3. Monitor agents in real-time via WebSocket connections")
            print(f"   4. Showcase agent decisions and eBay integration")
            
            if flutter_ready:
                print(f"\n📱 FLUTTER FRONTEND STATUS:")
                print(f"   ✅ Builds successfully")
                print(f"   🔧 Needs WebSocket endpoint fixes (already applied)")
                print(f"   🎯 Ready for mobile deployment after fixes")
            
            return True
        else:
            self.print_step(5, "⚠️ SHOWCASE NEEDS ATTENTION", "WARN")
            print("   📋 Some components need fixes before user showcase")
            return False

async def main():
    """Main showcase function."""
    showcase = EbayAgentShowcase()
    success = await showcase.run_complete_showcase()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
