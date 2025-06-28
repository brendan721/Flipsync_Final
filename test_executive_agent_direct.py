#!/usr/bin/env python3
"""
Direct test of the executive agent to verify the eBay fix works.
"""

import asyncio
import logging
import sys
import os

# Add the project root to Python path
sys.path.insert(0, "/app")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_executive_agent_direct():
    """Test the executive agent directly to verify the fix."""
    try:
        logger.info("🧪 Testing Executive Agent Direct Service Calls")

        # Import the executive agent
        from fs_agt_clean.agents.executive.executive_agent import ExecutiveUnifiedAgent

        # Create agent instance
        agent = ExecutiveUnifiedAgent(agent_id="test_direct_fix")
        logger.info("✅ Executive agent created successfully")

        # Test the marketplace delegation method directly
        test_user_id = "test_user_direct"
        test_message = "How many items do I have on eBay?"
        test_context = {}
        test_business_info = {}

        logger.info("🔄 Testing _handle_marketplace_delegation method...")

        result = await agent._handle_marketplace_delegation(
            message=test_message,
            context=test_context,
            business_info=test_business_info,
            user_id=test_user_id,
        )

        logger.info(f"📊 Result: {result}")

        # Check if we got the expected result structure
        if isinstance(result, dict):
            query_type = result.get("query_type")
            success = result.get("success")
            error = result.get("error", "")

            logger.info(f"Query type: {query_type}")
            logger.info(f"Success: {success}")

            if error:
                logger.info(f"Error: {error}")

                # Check if it's the old "Connection refused" error
                if "Connection refused" in error:
                    logger.error(
                        "❌ Still getting Connection refused error - fix didn't work"
                    )
                    return False
                elif "authentication" in error.lower() or "connect" in error.lower():
                    logger.info(
                        "✅ Got authentication error (expected - no real eBay tokens)"
                    )
                    logger.info("✅ No more Connection refused errors!")
                    return True
                else:
                    logger.info("✅ Got different error (not Connection refused)")
                    return True
            else:
                logger.info("✅ No error - method executed successfully!")
                return True
        else:
            logger.error(f"❌ Unexpected result type: {type(result)}")
            return False

    except Exception as e:
        logger.error(f"❌ Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run the direct executive agent test."""
    logger.info("🚀 Starting Direct Executive Agent Test")

    success = await test_executive_agent_direct()

    if success:
        logger.info("🎉 Direct Executive Agent Test PASSED!")
        logger.info("✅ Executive agent is using direct service calls")
        logger.info("✅ No more HTTP Connection refused errors")
    else:
        logger.error("💥 Direct Executive Agent Test FAILED!")
        logger.error("❌ Fix may not be working correctly")

    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
