#!/usr/bin/env python3
"""
Test 4+1 Architecture Agent Integration
=====================================

Comprehensive test suite to validate that all 4 autonomous agents properly
integrate with the new 4+1 architecture database schema.

Tests:
1. Agent registration in autonomous_agents table
2. Decision recording in autonomous_agent_decisions table
3. Heartbeat updates functionality
4. 4+1 architecture compliance validation
5. Cross-agent coordination with new schema
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Dict, List, Any

# Add the project root to the Python path
sys.path.append("/home/brend/Flipsync_Final")

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Set environment variables for database connection
os.environ["DATABASE_URL"] = (
    "sqlite:///flipsync_local.db"
)
os.environ["DB_NAME"] = "flipsync_agentic_test"


class FourPlusOneAgentIntegrationTester:
    """Test suite for 4+1 architecture agent integration."""

    def __init__(self):
        self.test_results = {}
        self.agents = {}
        self.database = None

    async def initialize(self):
        """Initialize test environment."""
        try:
            from fs_agt_clean.core.db.database import get_database
            from fs_agt_clean.database.repositories.autonomous_agent_repository import (
                AutonomousAgentRepository,
            )

            self.database = get_database()
            await self.database.initialize()
            self.repository = AutonomousAgentRepository()

            logger.info("✅ Test environment initialized")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize test environment: {e}")
            return False

    async def test_agent_registration(self) -> bool:
        """Test that all 4 agents register properly in autonomous_agents table."""
        logger.info("🧪 Testing agent registration in 4+1 architecture...")

        try:
            # Import all 4 autonomous agents
            from fs_agt_clean.agents.market.market_agent import MarketAutonomousAgent
            from fs_agt_clean.agents.content.content_agent import ContentAutonomousAgent
            from fs_agt_clean.agents.executive.executive_agent import (
                ExecutiveAutonomousAgent,
            )
            from fs_agt_clean.agents.logistics.logistics_agent import (
                LogisticsAutonomousAgent,
            )

            # Create test agents with unique IDs
            test_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            agents_to_test = [
                (
                    "market",
                    MarketAutonomousAgent,
                    f"test_market_agent_{test_timestamp}",
                ),
                (
                    "content",
                    ContentAutonomousAgent,
                    f"test_content_agent_{test_timestamp}",
                ),
                (
                    "executive",
                    ExecutiveAutonomousAgent,
                    f"test_executive_agent_{test_timestamp}",
                ),
                (
                    "logistics",
                    LogisticsAutonomousAgent,
                    f"test_logistics_agent_{test_timestamp}",
                ),
            ]

            registration_results = {}

            for agent_type, agent_class, agent_id in agents_to_test:
                try:
                    logger.info(f"Testing {agent_type} agent registration...")

                    # Create agent instance
                    agent = agent_class(agent_id=agent_id)

                    # Initialize agent (this should register it in the database)
                    success = await agent.initialize_async()

                    if success:
                        # Verify agent is registered in database
                        async with self.database.get_session() as session:
                            db_agent = await self.repository.get_autonomous_agent(
                                session, agent_id
                            )

                            if db_agent:
                                registration_results[agent_type] = {
                                    "registered": True,
                                    "agent_id": agent_id,
                                    "db_id": db_agent.id,
                                    "agent_type": db_agent.agent_type,
                                    "status": db_agent.status,
                                    "capabilities": db_agent.capabilities,
                                    "optimization_config": db_agent.optimization_config,
                                    "llm_free": db_agent.llm_free,
                                    "uses_standard_decision_pipeline": db_agent.uses_standard_decision_pipeline,
                                }
                                logger.info(
                                    f"✅ {agent_type} agent registered successfully"
                                )
                            else:
                                registration_results[agent_type] = {
                                    "registered": False,
                                    "error": "Not found in database",
                                }
                                logger.error(
                                    f"❌ {agent_type} agent not found in database"
                                )
                    else:
                        registration_results[agent_type] = {
                            "registered": False,
                            "error": "Initialization failed",
                        }
                        logger.error(f"❌ {agent_type} agent initialization failed")

                    # Store agent for further testing
                    self.agents[agent_type] = agent

                except Exception as e:
                    registration_results[agent_type] = {
                        "registered": False,
                        "error": str(e),
                    }
                    logger.error(f"❌ {agent_type} agent registration failed: {e}")

            # Validate results
            all_registered = all(
                result.get("registered", False)
                for result in registration_results.values()
            )

            self.test_results["agent_registration"] = {
                "passed": all_registered,
                "details": registration_results,
                "summary": f"{sum(1 for r in registration_results.values() if r.get('registered', False))}/4 agents registered successfully",
            }

            logger.info(
                f"🧪 Agent registration test: {'✅ PASSED' if all_registered else '❌ FAILED'}"
            )
            return all_registered

        except Exception as e:
            logger.error(f"❌ Agent registration test failed: {e}")
            self.test_results["agent_registration"] = {"passed": False, "error": str(e)}
            return False

    async def test_decision_recording(self) -> bool:
        """Test that agent decisions are properly recorded in autonomous_agent_decisions table."""
        logger.info("🧪 Testing decision recording in 4+1 architecture...")

        try:
            from fs_agt_clean.core.coordination.decision.models import DecisionType

            decision_results = {}

            for agent_type, agent in self.agents.items():
                try:
                    logger.info(f"Testing {agent_type} agent decision recording...")

                    # Create test decision context
                    test_context = {
                        "test_decision": True,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "agent_type": agent_type,
                    }

                    # Make a test decision
                    decision = await agent.make_autonomous_decision(
                        decision_context=test_context,
                        decision_type=DecisionType.OPTIMIZATION,
                        use_cache=False,
                    )

                    # Verify decision was recorded in database
                    async with self.database.get_session() as session:
                        decisions = await self.repository.get_agent_decisions(
                            session=session, agent_id=agent.agent_id, limit=1
                        )

                        if decisions and len(decisions) > 0:
                            latest_decision = decisions[0]
                            decision_results[agent_type] = {
                                "recorded": True,
                                "decision_id": latest_decision.decision_id,
                                "execution_time_ms": latest_decision.execution_time_ms,
                                "confidence": latest_decision.confidence,
                                "used_llm": latest_decision.used_llm,
                                "used_standard_pipeline": latest_decision.used_standard_pipeline,
                                "algorithm_used": latest_decision.algorithm_used,
                            }
                            logger.info(
                                f"✅ {agent_type} agent decision recorded successfully"
                            )
                        else:
                            decision_results[agent_type] = {
                                "recorded": False,
                                "error": "Decision not found in database",
                            }
                            logger.error(f"❌ {agent_type} agent decision not recorded")

                except Exception as e:
                    decision_results[agent_type] = {"recorded": False, "error": str(e)}
                    logger.error(
                        f"❌ {agent_type} agent decision recording failed: {e}"
                    )

            # Validate results
            all_recorded = all(
                result.get("recorded", False) for result in decision_results.values()
            )

            self.test_results["decision_recording"] = {
                "passed": all_recorded,
                "details": decision_results,
                "summary": f"{sum(1 for r in decision_results.values() if r.get('recorded', False))}/{len(self.agents)} agent decisions recorded successfully",
            }

            logger.info(
                f"🧪 Decision recording test: {'✅ PASSED' if all_recorded else '❌ FAILED'}"
            )
            return all_recorded

        except Exception as e:
            logger.error(f"❌ Decision recording test failed: {e}")
            self.test_results["decision_recording"] = {"passed": False, "error": str(e)}
            return False

    async def test_heartbeat_updates(self) -> bool:
        """Test that agent heartbeat updates work properly."""
        logger.info("🧪 Testing heartbeat updates in 4+1 architecture...")

        try:
            heartbeat_results = {}

            for agent_type, agent in self.agents.items():
                try:
                    logger.info(f"Testing {agent_type} agent heartbeat...")

                    # Get initial heartbeat
                    async with self.database.get_session() as session:
                        initial_agent = await self.repository.get_autonomous_agent(
                            session, agent.agent_id
                        )
                        initial_heartbeat = (
                            initial_agent.last_heartbeat if initial_agent else None
                        )

                    # Wait a moment and update heartbeat
                    await asyncio.sleep(0.1)
                    await agent.update_heartbeat()

                    # Get updated heartbeat
                    async with self.database.get_session() as session:
                        updated_agent = await self.repository.get_autonomous_agent(
                            session, agent.agent_id
                        )
                        updated_heartbeat = (
                            updated_agent.last_heartbeat if updated_agent else None
                        )

                    # Verify heartbeat was updated
                    if (
                        initial_heartbeat
                        and updated_heartbeat
                        and updated_heartbeat > initial_heartbeat
                    ):
                        heartbeat_results[agent_type] = {
                            "updated": True,
                            "initial_heartbeat": initial_heartbeat.isoformat(),
                            "updated_heartbeat": updated_heartbeat.isoformat(),
                        }
                        logger.info(
                            f"✅ {agent_type} agent heartbeat updated successfully"
                        )
                    else:
                        heartbeat_results[agent_type] = {
                            "updated": False,
                            "error": "Heartbeat not updated",
                        }
                        logger.error(f"❌ {agent_type} agent heartbeat not updated")

                except Exception as e:
                    heartbeat_results[agent_type] = {"updated": False, "error": str(e)}
                    logger.error(f"❌ {agent_type} agent heartbeat test failed: {e}")

            # Validate results
            all_updated = all(
                result.get("updated", False) for result in heartbeat_results.values()
            )

            self.test_results["heartbeat_updates"] = {
                "passed": all_updated,
                "details": heartbeat_results,
                "summary": f"{sum(1 for r in heartbeat_results.values() if r.get('updated', False))}/{len(self.agents)} agent heartbeats updated successfully",
            }

            logger.info(
                f"🧪 Heartbeat updates test: {'✅ PASSED' if all_updated else '❌ FAILED'}"
            )
            return all_updated

        except Exception as e:
            logger.error(f"❌ Heartbeat updates test failed: {e}")
            self.test_results["heartbeat_updates"] = {"passed": False, "error": str(e)}
            return False

    async def test_4plus1_compliance(self) -> bool:
        """Test that all agents maintain 4+1 architecture compliance."""
        logger.info("🧪 Testing 4+1 architecture compliance...")

        try:
            compliance_results = {}

            async with self.database.get_session() as session:
                # Get all test agents from database
                for agent_type, agent in self.agents.items():
                    try:
                        db_agent = await self.repository.get_autonomous_agent(
                            session, agent.agent_id
                        )

                        if db_agent:
                            # Check 4+1 architecture compliance
                            compliance_checks = {
                                "llm_free": db_agent.llm_free is True,
                                "uses_standard_decision_pipeline": db_agent.uses_standard_decision_pipeline
                                is True,
                                "architecture_type": db_agent.architecture_type
                                == "autonomous",
                                "valid_agent_type": db_agent.agent_type
                                in ["market", "content", "executive", "logistics"],
                                "has_capabilities": db_agent.capabilities is not None,
                                "has_optimization_config": db_agent.optimization_config
                                is not None,
                            }

                            all_compliant = all(compliance_checks.values())

                            compliance_results[agent_type] = {
                                "compliant": all_compliant,
                                "checks": compliance_checks,
                                "agent_type": db_agent.agent_type,
                                "architecture_type": db_agent.architecture_type,
                            }

                            if all_compliant:
                                logger.info(
                                    f"✅ {agent_type} agent is 4+1 architecture compliant"
                                )
                            else:
                                failed_checks = [
                                    k for k, v in compliance_checks.items() if not v
                                ]
                                logger.error(
                                    f"❌ {agent_type} agent failed compliance checks: {failed_checks}"
                                )
                        else:
                            compliance_results[agent_type] = {
                                "compliant": False,
                                "error": "Agent not found in database",
                            }

                    except Exception as e:
                        compliance_results[agent_type] = {
                            "compliant": False,
                            "error": str(e),
                        }
                        logger.error(
                            f"❌ {agent_type} agent compliance check failed: {e}"
                        )

            # Validate results
            all_compliant = all(
                result.get("compliant", False) for result in compliance_results.values()
            )

            self.test_results["4plus1_compliance"] = {
                "passed": all_compliant,
                "details": compliance_results,
                "summary": f"{sum(1 for r in compliance_results.values() if r.get('compliant', False))}/{len(self.agents)} agents are 4+1 architecture compliant",
            }

            logger.info(
                f"🧪 4+1 architecture compliance test: {'✅ PASSED' if all_compliant else '❌ FAILED'}"
            )
            return all_compliant

        except Exception as e:
            logger.error(f"❌ 4+1 architecture compliance test failed: {e}")
            self.test_results["4plus1_compliance"] = {"passed": False, "error": str(e)}
            return False

    def generate_test_report(self) -> str:
        """Generate comprehensive test report."""
        report = f"""
🧪 4+1 ARCHITECTURE AGENT INTEGRATION TEST REPORT
================================================

Test Execution Time: {datetime.now().isoformat()}
Database: flipsync_agentic_test

📊 TEST SUMMARY:
"""

        total_tests = len(self.test_results)
        passed_tests = sum(
            1 for result in self.test_results.values() if result.get("passed", False)
        )

        report += f"Total Tests: {total_tests}\n"
        report += f"Passed: {passed_tests}\n"
        report += f"Failed: {total_tests - passed_tests}\n"
        report += f"Success Rate: {(passed_tests/total_tests*100):.1f}%\n\n"

        # Detailed results
        for test_name, result in self.test_results.items():
            status = "✅ PASSED" if result.get("passed", False) else "❌ FAILED"
            report += f"🧪 {test_name.replace('_', ' ').title()}: {status}\n"

            if "summary" in result:
                report += f"   Summary: {result['summary']}\n"

            if not result.get("passed", False) and "error" in result:
                report += f"   Error: {result['error']}\n"

            report += "\n"

        # Overall assessment
        if passed_tests == total_tests:
            report += "🎉 ALL TESTS PASSED - 4+1 ARCHITECTURE INTEGRATION SUCCESSFUL!\n"
            report += "✅ Agents are properly integrated with new database schema\n"
            report += "✅ Decision recording is working correctly\n"
            report += "✅ 4+1 architecture compliance is maintained\n"
            report += "✅ Ready for Phase 3: API and WebSocket Integration\n"
        else:
            report += "⚠️ SOME TESTS FAILED - REVIEW REQUIRED\n"
            report += "❌ Agent integration needs attention before proceeding\n"

        return report

    async def run_all_tests(self) -> bool:
        """Run all integration tests."""
        logger.info("🚀 Starting 4+1 Architecture Agent Integration Tests...")

        try:
            # Initialize test environment
            if not await self.initialize():
                return False

            # Run all tests
            tests = [
                ("Agent Registration", self.test_agent_registration),
                ("Decision Recording", self.test_decision_recording),
                ("Heartbeat Updates", self.test_heartbeat_updates),
                ("4+1 Compliance", self.test_4plus1_compliance),
            ]

            all_passed = True
            for test_name, test_func in tests:
                logger.info(f"🧪 Running {test_name} test...")
                result = await test_func()
                if not result:
                    all_passed = False
                    logger.error(f"❌ {test_name} test failed")
                else:
                    logger.info(f"✅ {test_name} test passed")

            # Generate and display report
            report = self.generate_test_report()
            logger.info(report)

            return all_passed

        except Exception as e:
            logger.error(f"❌ Test suite execution failed: {e}")
            return False


async def main():
    """Main test execution function."""
    tester = FourPlusOneAgentIntegrationTester()
    success = await tester.run_all_tests()

    if success:
        print("\n🎉 4+1 ARCHITECTURE AGENT INTEGRATION TESTS PASSED!")
        print("✅ All agents are properly integrated with new database schema")
        print("✅ Ready to proceed with Phase 3: API and WebSocket Integration")
    else:
        print("\n❌ 4+1 ARCHITECTURE AGENT INTEGRATION TESTS FAILED")
        print("⚠️ Review test results and fix issues before proceeding")

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
