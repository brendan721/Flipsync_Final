#!/usr/bin/env python3
"""
Test Agent Initialization Fix for FlipSync.
Verifies that all 12 agents are properly initializing after dependency fixes.
"""

import asyncio
import aiohttp
import logging
import time
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AgentInitializationFixTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.api_base = f"{self.backend_url}/api/v1"
        
        # Expected 12-agent system after fixes
        self.expected_agents = [
            "amazon_agent",      # Marketplace agent (may fail due to credentials)
            "ebay_agent",        # Marketplace agent  
            "inventory_agent",   # Inventory management (FIXED: correct import path)
            "executive_agent",   # Strategic coordination
            "content_agent",     # Content optimization
            "logistics_agent",   # Logistics and shipping
            "market_agent",      # Market analysis
            "listing_agent",     # Listing optimization
            "auto_pricing_agent", # Automated pricing
            "auto_listing_agent", # Automated listing
            "auto_inventory_agent", # Automated inventory
            "ai_executive_agent"  # AI-powered executive (FIXED: added to initialization)
        ]
        
    async def test_agent_status_endpoint(self) -> Dict[str, Any]:
        """Test the agent status endpoint to see current agent count."""
        logger.info("🔍 Testing Agent Status Endpoint")
        
        results = {
            "endpoint_accessible": False,
            "agents_found": 0,
            "agents_active": 0,
            "agent_details": {},
            "missing_agents": [],
            "unexpected_agents": []
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.api_base}/agents/status") as response:
                    if response.status == 200:
                        results["endpoint_accessible"] = True
                        agent_data = await response.json()
                        
                        if "agents" in agent_data:
                            agents = agent_data["agents"]
                            results["agents_found"] = len(agents)
                            
                            for agent_id, agent_info in agents.items():
                                results["agent_details"][agent_id] = {
                                    "type": agent_info.get("type", "unknown"),
                                    "status": agent_info.get("status", "unknown"),
                                    "marketplace": agent_info.get("marketplace", "unknown"),
                                    "initialized_at": agent_info.get("initialized_at", "unknown")
                                }
                                
                                if agent_info.get("status") == "active":
                                    results["agents_active"] += 1
                            
                            # Check for missing and unexpected agents
                            found_agent_ids = set(agents.keys())
                            expected_agent_ids = set(self.expected_agents)
                            
                            results["missing_agents"] = list(expected_agent_ids - found_agent_ids)
                            results["unexpected_agents"] = list(found_agent_ids - expected_agent_ids)
                            
                            logger.info(f"📊 Found {results['agents_found']} agents, {results['agents_active']} active")
                            
                            if results["missing_agents"]:
                                logger.warning(f"⚠️ Missing expected agents: {results['missing_agents']}")
                            if results["unexpected_agents"]:
                                logger.info(f"ℹ️ Additional agents found: {results['unexpected_agents']}")
                        
                    else:
                        logger.error(f"❌ Agent status endpoint returned {response.status}")
                        
        except Exception as e:
            logger.error(f"❌ Error testing agent status endpoint: {e}")
        
        return results
    
    async def wait_for_agent_initialization(self, max_wait_seconds: int = 30) -> bool:
        """Wait for agents to initialize after restart."""
        logger.info(f"⏳ Waiting up to {max_wait_seconds}s for agent initialization...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait_seconds:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{self.backend_url}/health") as response:
                        if response.status == 200:
                            # Check if agents are initialized
                            async with session.get(f"{self.api_base}/agents/status") as agent_response:
                                if agent_response.status == 200:
                                    agent_data = await agent_response.json()
                                    if "agents" in agent_data and len(agent_data["agents"]) > 0:
                                        logger.info("✅ Agents are initializing")
                                        return True
                
                await asyncio.sleep(2)
                
            except Exception:
                await asyncio.sleep(2)
        
        logger.warning(f"⏰ Timeout waiting for agent initialization after {max_wait_seconds}s")
        return False
    
    async def run_agent_initialization_test(self) -> Dict[str, Any]:
        """Run comprehensive agent initialization test."""
        logger.info("🚀 Starting Agent Initialization Fix Test")
        logger.info("=" * 70)
        
        test_results = {
            "initialization_wait": False,
            "agent_status_test": {},
            "fix_assessment": {}
        }
        
        # Wait for initialization
        logger.info("🧪 TEST 1: Wait for Agent Initialization")
        test_results["initialization_wait"] = await self.wait_for_agent_initialization()
        
        # Test agent status
        logger.info("🧪 TEST 2: Agent Status Verification")
        test_results["agent_status_test"] = await self.test_agent_status_endpoint()
        
        # Assess fixes
        status_test = test_results["agent_status_test"]
        test_results["fix_assessment"] = {
            "inventory_agent_fixed": "inventory_agent" in status_test.get("agent_details", {}),
            "ai_executive_agent_fixed": "ai_executive_agent" in status_test.get("agent_details", {}),
            "amazon_agent_expected_missing": "amazon_agent" in status_test.get("missing_agents", []),
            "total_agents_found": status_test.get("agents_found", 0),
            "total_agents_active": status_test.get("agents_active", 0),
            "target_agents_achieved": status_test.get("agents_active", 0) >= 11,  # 11 out of 12 (Amazon expected to fail)
            "fixes_successful": False
        }
        
        # Calculate overall success
        assessment = test_results["fix_assessment"]
        assessment["fixes_successful"] = (
            assessment["inventory_agent_fixed"] and
            assessment["ai_executive_agent_fixed"] and
            assessment["target_agents_achieved"]
        )
        
        return test_results

async def main():
    """Main test execution."""
    tester = AgentInitializationFixTest()
    results = await tester.run_agent_initialization_test()
    
    # Print comprehensive results
    logger.info("=" * 70)
    logger.info("🏁 AGENT INITIALIZATION FIX TEST RESULTS")
    logger.info("=" * 70)
    
    # Initialization Results
    logger.info("📊 INITIALIZATION STATUS:")
    logger.info(f"Agents Ready: {'✅' if results['initialization_wait'] else '❌'}")
    
    # Agent Status Results
    status_results = results["agent_status_test"]
    logger.info("📊 AGENT STATUS:")
    logger.info(f"Endpoint Accessible: {'✅' if status_results.get('endpoint_accessible') else '❌'}")
    logger.info(f"Total Agents Found: {status_results.get('agents_found', 0)}")
    logger.info(f"Active Agents: {status_results.get('agents_active', 0)}")
    
    if status_results.get("agent_details"):
        logger.info("🤖 AGENT DETAILS:")
        for agent_id, details in status_results["agent_details"].items():
            status_icon = "✅" if details["status"] == "active" else "❌"
            logger.info(f"  {status_icon} {agent_id}: {details['type']} ({details['status']})")
    
    if status_results.get("missing_agents"):
        logger.warning(f"⚠️ Missing Agents: {status_results['missing_agents']}")
    
    if status_results.get("unexpected_agents"):
        logger.info(f"ℹ️ Additional Agents: {status_results['unexpected_agents']}")
    
    # Fix Assessment
    assessment = results["fix_assessment"]
    logger.info("📊 FIX ASSESSMENT:")
    logger.info(f"Inventory Agent Fixed: {'✅' if assessment['inventory_agent_fixed'] else '❌'}")
    logger.info(f"AI Executive Agent Fixed: {'✅' if assessment['ai_executive_agent_fixed'] else '❌'}")
    logger.info(f"Amazon Agent (Expected Missing): {'✅' if assessment['amazon_agent_expected_missing'] else '❌'}")
    logger.info(f"Target Agents Achieved (11+): {'✅' if assessment['target_agents_achieved'] else '❌'}")
    
    logger.info("=" * 70)
    if assessment["fixes_successful"]:
        logger.info("🎉 SUCCESS: Agent initialization fixes working!")
        logger.info("✅ All expected agents are now initializing properly")
        logger.info(f"✅ {assessment['total_agents_active']} out of 12 agents active (Amazon missing credentials as expected)")
    else:
        logger.error("💥 ISSUES: Some agent initialization fixes need attention")
        
        if not assessment["inventory_agent_fixed"]:
            logger.error("❌ Inventory agent still not initializing")
        if not assessment["ai_executive_agent_fixed"]:
            logger.error("❌ AI Executive agent still not initializing")
        if not assessment["target_agents_achieved"]:
            logger.error(f"❌ Only {assessment['total_agents_active']} agents active, need 11+")
    
    return results

if __name__ == "__main__":
    results = asyncio.run(main())
