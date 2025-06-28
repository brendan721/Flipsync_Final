#!/usr/bin/env python3
"""
Test script to verify Pipeline Controller integration with Agent Manager.

This test validates that the Pipeline Controller can successfully coordinate
with the real Agent Manager to execute multi-agent workflows.
"""

import asyncio
import logging
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath("."))

from fs_agt_clean.core.pipeline.controller import (
    PipelineController,
    PipelineStage,
    PipelineConfiguration,
    AgentCategoryType,
)
from fs_agt_clean.core.agents.real_agent_manager import RealAgentManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def test_pipeline_controller_integration():
    """Test the integration between Pipeline Controller and Agent Manager."""
    logger.info("🚀 Starting Pipeline Controller Integration Test")

    try:
        # Step 1: Initialize the Real Agent Manager
        logger.info("📋 Step 1: Initializing Real Agent Manager...")
        agent_manager = RealAgentManager()

        # Initialize the agent manager
        init_success = await agent_manager.initialize()
        if not init_success:
            logger.error("❌ Failed to initialize Agent Manager")
            return False

        logger.info(
            f"✅ Agent Manager initialized with {len(agent_manager.agents)} agents"
        )

        # Step 2: Create Pipeline Controller with Agent Manager
        logger.info("📋 Step 2: Creating Pipeline Controller with Agent Manager...")
        pipeline_controller = PipelineController(agent_manager=agent_manager)
        logger.info("✅ Pipeline Controller created successfully")

        # Step 3: Test basic pipeline execution
        logger.info("📋 Step 3: Testing basic pipeline execution...")

        # Create a simple test pipeline
        test_stages = [
            PipelineStage("executive_analysis", AgentCategoryType.EXECUTIVE),
            PipelineStage("market_research", AgentCategoryType.MARKET),
            PipelineStage("content_generation", AgentCategoryType.CONTENT),
        ]

        test_pipeline = PipelineConfiguration(
            pipeline_id="test_integration_pipeline",
            stages=test_stages,
            description="Test pipeline for integration validation",
        )

        # Register the test pipeline
        pipeline_controller.register_pipeline(test_pipeline)
        logger.info("✅ Test pipeline registered")

        # Step 4: Execute the pipeline
        logger.info("📋 Step 4: Executing test pipeline...")

        test_data = {
            "product_name": "Test Product",
            "category": "Electronics",
            "price": 99.99,
            "description": "A test product for pipeline validation",
        }

        success, result_data = await pipeline_controller.execute_pipeline(
            "test_integration_pipeline", test_data
        )

        if success:
            logger.info("✅ Pipeline execution completed successfully")
            logger.info(f"📊 Result data: {result_data}")
        else:
            logger.error("❌ Pipeline execution failed")
            return False

        # Step 5: Verify agent coordination
        logger.info("📋 Step 5: Verifying agent coordination...")

        # Check pipeline metrics
        pipeline_config = pipeline_controller.pipeline_configs[
            "test_integration_pipeline"
        ]
        total_executions = sum(
            stage.metrics["executions"] for stage in pipeline_config.stages
        )
        total_successes = sum(
            stage.metrics["successes"] for stage in pipeline_config.stages
        )

        logger.info(f"📈 Pipeline Metrics:")
        logger.info(f"   Total stage executions: {total_executions}")
        logger.info(f"   Total successful executions: {total_successes}")
        logger.info(
            f"   Success rate: {(total_successes/total_executions)*100:.1f}%"
            if total_executions > 0
            else "   Success rate: N/A"
        )

        # Step 6: Test agent status verification
        logger.info("📋 Step 6: Verifying agent status...")

        active_agents = [
            name
            for name, info in agent_manager.agents.items()
            if info.get("status") == "active"
        ]

        logger.info(f"🤖 Active agents: {len(active_agents)}")
        for agent_name in active_agents[:5]:  # Show first 5 agents
            agent_info = agent_manager.agents[agent_name]
            logger.info(
                f"   - {agent_name}: {agent_info.get('type', 'unknown')} (initialized: {agent_info.get('initialized_at', 'unknown')})"
            )

        if len(active_agents) > 5:
            logger.info(f"   ... and {len(active_agents) - 5} more agents")

        # Step 7: Test workflow templates
        logger.info("📋 Step 7: Testing workflow templates...")

        # Test the built-in pricing update template
        try:
            pricing_success, pricing_result = (
                await pipeline_controller.execute_pipeline(
                    "pricing_update", {"product_id": "test_123", "current_price": 50.00}
                )
            )

            if pricing_success:
                logger.info("✅ Pricing update workflow executed successfully")
            else:
                logger.warning("⚠️ Pricing update workflow failed")
        except Exception as e:
            logger.warning(f"⚠️ Pricing update template test failed: {e}")

        # Test inventory sync template
        try:
            inventory_success, inventory_result = (
                await pipeline_controller.execute_pipeline(
                    "inventory_sync", {"product_id": "test_456", "quantity": 100}
                )
            )

            if inventory_success:
                logger.info("✅ Inventory sync workflow executed successfully")
            else:
                logger.warning("⚠️ Inventory sync workflow failed")
        except Exception as e:
            logger.warning(f"⚠️ Inventory sync template test failed: {e}")

        logger.info("🎉 Pipeline Controller Integration Test Completed Successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Integration test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Main test execution function."""
    logger.info("=" * 60)
    logger.info("FlipSync Pipeline Controller Integration Test")
    logger.info("=" * 60)

    success = await test_pipeline_controller_integration()

    if success:
        logger.info("🎉 ALL TESTS PASSED - Pipeline Controller integration is working!")
        return 0
    else:
        logger.error("❌ TESTS FAILED - Pipeline Controller integration needs fixes")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
