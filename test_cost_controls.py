#!/usr/bin/env python3
import sys
import asyncio
import os

sys.path.append("/app")


async def test_cost_controls():
    try:
        from fs_agt_clean.core.ai.openai_client import create_openai_client
        from fs_agt_clean.core.monitoring.cost_tracker import (
            get_cost_tracker,
            record_ai_cost,
        )

        print("💰 Testing OpenAI Cost Control Mechanisms")
        print("=" * 50)

        # Check environment configuration
        print("📋 Configuration Check:")
        print("  Daily Budget:", os.getenv("OPENAI_DAILY_BUDGET", "Not set"))
        print(
            "  Max Cost Per Request:",
            os.getenv("OPENAI_MAX_COST_PER_REQUEST", "Not set"),
        )
        print("  LLM Provider:", os.getenv("LLM_PROVIDER", "Not set"))
        print("  Use OpenAI Primary:", os.getenv("USE_OPENAI_PRIMARY", "Not set"))
        print("  Fallback to Ollama:", os.getenv("FALLBACK_TO_OLLAMA", "Not set"))
        print()

        # Test cost tracking
        print("📊 Cost Tracking Test:")
        try:
            cost_tracker = get_cost_tracker()
            print("  Cost tracker retrieved:", type(cost_tracker).__name__)
            print("  Cost tracker available:", cost_tracker is not None)
        except Exception as e:
            print("  Cost tracking error:", str(e))
        print()

        # Test client cost estimation
        print("🧮 Cost Estimation Test:")
        client = create_openai_client()
        estimated_cost = await client.estimate_cost("Test prompt for cost estimation")
        print("  Estimated cost:", f"${estimated_cost:.6f}")
        print()

        # Test usage statistics
        print("📈 Usage Statistics Test:")
        try:
            usage_stats = client.get_usage_stats()
            print("  Usage stats:", usage_stats)
        except Exception as e:
            print("  Usage stats error:", str(e))
        print()

        # Test actual API call with cost tracking
        print("🔍 Real API Call Cost Test:")
        response = await client.generate_text(
            prompt="Brief test for cost verification",
            system_prompt="Respond with just OK",
        )
        print("  Response:", response.content)
        print("  Actual cost:", f"${response.cost_estimate:.6f}")
        print("  Model used:", response.model)
        print("  Success:", response.success)
        print("  Usage info:", response.usage)
        print()

        # Test cost recording
        print("💾 Cost Recording Test:")
        try:
            await record_ai_cost(
                category="test",
                model="gpt-4o-mini",
                operation="cost_control_validation",
                cost=0.001,
                agent_id="test_agent",
                tokens_used=10,
            )
            print("  Cost recording: Successful")
        except Exception as e:
            print("  Cost recording error:", str(e))
        print()

        # Test budget enforcement simulation
        print("🚨 Budget Enforcement Test:")
        try:
            # Check if request would exceed limits
            viability = await client.check_request_viability(
                "Large test prompt that might cost more"
            )
            print("  Request viability check:", viability)
        except Exception as e:
            print("  Budget enforcement error:", str(e))

        return True

    except Exception as e:
        print("❌ Cost control test failed:", str(e))
        import traceback

        traceback.print_exc()
        return False


async def main():
    print("🧪 OpenAI Cost Control Validation Suite")
    print("=" * 60)

    result = await test_cost_controls()

    print()
    print("📊 Overall Cost Control Test Result:")
    print(f'  Status: {"✅ PASS" if result else "❌ FAIL"}')

    return result


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
