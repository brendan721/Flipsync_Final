#!/usr/bin/env python3
import sys
import asyncio

sys.path.append("/app")


async def test_openai_call():
    try:
        from fs_agt_clean.core.ai.openai_client import create_openai_client

        client = create_openai_client()
        print("🔑 Testing OpenAI API call from container...")

        response = await client.generate_text(
            prompt="Test connectivity - respond with just OK",
            system_prompt="You are a test assistant. Respond briefly.",
        )

        print("✅ OpenAI API call successful!")
        print("Response content:", response.content)
        print("Response time:", f"{response.response_time:.2f}s")
        print("Tokens used:", response.tokens_used)
        print("Cost:", f"${response.cost:.4f}")

        # Test cost controls
        usage_stats = client.get_usage_stats()
        print("Usage stats:", usage_stats)

        return True

    except Exception as e:
        print("❌ OpenAI API call failed:", str(e))
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test_openai_call())
    sys.exit(0 if result else 1)
