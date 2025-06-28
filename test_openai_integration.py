#!/usr/bin/env python3
"""
Test OpenAI Integration for FlipSync
===================================

This script tests the OpenAI integration within the FlipSync Docker container
to verify that the backend is properly connected to OpenAI APIs and that
the confidence scoring and shipping arbitrage features are working.
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime

import aiohttp


async def register_test_user(session: aiohttp.ClientSession, base_url: str) -> bool:
    """Register a test user for authentication."""
    try:
        register_data = {
            "email": "flipsync_test@example.com",
            "username": "flipsync_test_user",
            "password": "FlipSyncTest123!",
            "first_name": "FlipSync",
            "last_name": "Test",
        }

        async with session.post(
            f"{base_url}/api/v1/auth/register",
            json=register_data,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status == 200:
                print("✅ Test user registered successfully")
                return True
            else:
                # User might already exist, which is fine
                print(
                    f"⚠️  User registration returned {response.status} (might already exist)"
                )
                return True
    except Exception as e:
        print(f"⚠️  User registration error: {e}")
        return False


async def get_auth_token(session: aiohttp.ClientSession, base_url: str) -> str:
    """Get a valid JWT token for testing authenticated endpoints."""
    try:
        # First try to register the test user
        await register_test_user(session, base_url)

        # Try the built-in test credentials first
        login_data = {"email": "test@example.com", "password": "SecurePassword!"}

        async with session.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("access_token", "")

        # If built-in test credentials don't work, try our registered user
        login_data = {
            "email": "flipsync_test@example.com",
            "password": "FlipSyncTest123!",
        }

        async with session.post(
            f"{base_url}/api/v1/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"},
        ) as response:
            if response.status == 200:
                result = await response.json()
                return result.get("access_token", "")
            else:
                print(f"⚠️  Failed to get auth token: {response.status}")
                error_text = await response.text()
                print(f"📄 Login error: {error_text}")
                return ""
    except Exception as e:
        print(f"⚠️  Auth token error: {e}")
        return ""


async def test_openai_integration():
    """Test OpenAI integration within FlipSync Docker container."""
    print("🤖 FlipSync OpenAI Integration Test")
    print("=" * 50)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Testing OpenAI integration in FlipSync backend...")
    print()

    # Test configuration
    base_url = "http://localhost:8001"
    test_results = {
        "openai_connection": False,
        "confidence_analysis": False,
        "shipping_arbitrage": False,
        "cost_tracking": False,
        "api_endpoints": False,
        "total_cost": 0.0,
        "response_times": [],
    }

    async with aiohttp.ClientSession() as session:
        # Test 1: Health check
        print("🏥 Test 1: Backend Health Check")
        try:
            start_time = time.time()
            async with session.get(f"{base_url}/health") as response:
                response_time = time.time() - start_time
                test_results["response_times"].append(response_time)

                if response.status == 200:
                    health_data = await response.json()
                    print(f"✅ Backend healthy: {health_data}")
                    print(f"⏱️  Response time: {response_time:.3f}s")
                else:
                    print(f"❌ Backend health check failed: {response.status}")
                    return test_results
        except Exception as e:
            print(f"❌ Backend connection failed: {e}")
            return test_results
        print()

        # Test 2: OpenAI API Key Configuration
        print("🔑 Test 2: OpenAI API Key Configuration")
        try:
            # Test if OpenAI endpoints are available
            async with session.get(f"{base_url}/api/v1/ai/ai/status") as response:
                if response.status == 200:
                    ai_status = await response.json()
                    print(f"✅ AI service status: {ai_status}")
                    test_results["openai_connection"] = True
                elif response.status == 404:
                    print("⚠️  AI status endpoint not found - creating test endpoint")
                    # This is expected since we need to create the endpoint
                else:
                    print(f"❌ AI service status check failed: {response.status}")
        except Exception as e:
            print(f"⚠️  AI status check error (expected): {e}")
        print()

        # Test 3: Confidence Analysis API
        print("🧠 Test 3: AI Confidence Analysis")
        confidence_data = {
            "analysis_type": "optimization_confidence",
            "recommendation": {
                "id": "test_rec_001",
                "type": "pricing",
                "title": "Optimize pricing for faster sales",
                "description": "Reduce price by $50 to match market rates",
                "confidence_score": 0.85,
                "current_value": {"price": 999.99},
                "recommended_value": {"price": 949.99},
            },
            "product": {
                "id": "test_prod_001",
                "title": "iPhone 14 Pro Max 256GB",
                "price": 999.99,
                "category": "Cell Phones",
            },
            "market_context": {
                "competition_level": "high",
                "demand": "moderate",
            },
            "model_preference": "gpt-4o-mini",
            "max_cost": 0.05,
        }

        try:
            start_time = time.time()
            async with session.post(
                f"{base_url}/api/v1/ai/ai/confidence-analysis",
                json=confidence_data,
                headers={"Content-Type": "application/json"},
            ) as response:
                response_time = time.time() - start_time
                test_results["response_times"].append(response_time)

                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Confidence analysis successful")
                    print(f"⏱️  Response time: {response_time:.3f}s")
                    print(f"💰 Estimated cost: ${result.get('cost_estimate', 0):.4f}")
                    test_results["confidence_analysis"] = True
                    test_results["total_cost"] += result.get("cost_estimate", 0)
                elif response.status == 404:
                    print("⚠️  Confidence analysis endpoint not found")
                    print("📝 This endpoint needs to be implemented in the backend")
                else:
                    error_text = await response.text()
                    print(f"❌ Confidence analysis failed: {response.status}")
                    print(f"📄 Error: {error_text}")
        except Exception as e:
            print(f"❌ Confidence analysis error: {e}")
        print()

        # Test 4: Shipping Arbitrage API (with authentication)
        print("🚚 Test 4: Shipping Arbitrage Analysis")

        # Get authentication token
        auth_token = await get_auth_token(session, base_url)
        if not auth_token:
            print("❌ Failed to get authentication token for shipping test")
            print("📝 Shipping arbitrage requires authentication")
        else:
            print(f"✅ Got authentication token: {auth_token[:20]}...")

        shipping_data = {
            "product_id": "test_prod_001",
            "dimensions": {
                "length": 6.33,
                "width": 3.07,
                "height": 0.31,
                "unit": "in",
            },
            "weight": 0.5,
            "value": 999.99,
            "origin_address": {
                "name": "FlipSync Test",
                "street1": "123 Test Street",
                "city": "Nashville",
                "state": "TN",
                "zip": "37203",
                "country": "US",
            },
            "enable_arbitrage": True,
        }

        try:
            start_time = time.time()
            headers = {"Content-Type": "application/json"}
            if auth_token:
                headers["Authorization"] = f"Bearer {auth_token}"

            async with session.post(
                f"{base_url}/api/v1/shipping/v1/shipping/arbitrage",
                json=shipping_data,
                headers=headers,
            ) as response:
                response_time = time.time() - start_time
                test_results["response_times"].append(response_time)

                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Shipping arbitrage successful")
                    print(f"⏱️  Response time: {response_time:.3f}s")
                    print(f"💰 API cost: ${result.get('api_cost', 0):.4f}")
                    test_results["shipping_arbitrage"] = True
                    test_results["total_cost"] += result.get("api_cost", 0)
                elif response.status == 404:
                    print("⚠️  Shipping arbitrage endpoint not found")
                    print("📝 This endpoint needs to be implemented in the backend")
                else:
                    error_text = await response.text()
                    print(f"❌ Shipping arbitrage failed: {response.status}")
                    print(f"📄 Error: {error_text}")
        except Exception as e:
            print(f"❌ Shipping arbitrage error: {e}")
        print()

        # Test 5: Cost Tracking
        print("💰 Test 5: OpenAI Cost Tracking")
        try:
            async with session.get(f"{base_url}/api/v1/ai/ai/usage-stats") as response:
                if response.status == 200:
                    stats = await response.json()
                    print(f"✅ Cost tracking working")
                    print(f"📊 Daily cost: ${stats.get('daily_cost', 0):.4f}")
                    print(
                        f"📊 Budget remaining: ${stats.get('budget_remaining', 0):.4f}"
                    )
                    print(f"📊 Total requests: {stats.get('total_requests', 0)}")
                    test_results["cost_tracking"] = True
                elif response.status == 404:
                    print("⚠️  Cost tracking endpoint not found")
                    print("📝 This endpoint needs to be implemented in the backend")
                else:
                    print(f"❌ Cost tracking failed: {response.status}")
        except Exception as e:
            print(f"❌ Cost tracking error: {e}")
        print()

        # Test 6: Direct OpenAI Test (if possible)
        print("🔬 Test 6: Direct OpenAI API Test")
        openai_test_data = {
            "prompt": "Test FlipSync OpenAI integration with a simple response",
            "task_complexity": "simple",
            "system_prompt": "You are FlipSync AI assistant. Respond briefly that the integration is working.",
        }

        try:
            start_time = time.time()
            async with session.post(
                f"{base_url}/api/v1/ai/ai/generate-text",
                json=openai_test_data,
                headers={"Content-Type": "application/json"},
            ) as response:
                response_time = time.time() - start_time
                test_results["response_times"].append(response_time)

                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Direct OpenAI test successful")
                    print(f"⏱️  Response time: {response_time:.3f}s")
                    print(
                        f"🤖 AI Response: {result.get('content', 'No content')[:100]}..."
                    )
                    print(f"💰 Cost: ${result.get('cost_estimate', 0):.4f}")
                    test_results["api_endpoints"] = True
                    test_results["total_cost"] += result.get("cost_estimate", 0)
                elif response.status == 404:
                    print("⚠️  Direct OpenAI endpoint not found")
                    print("📝 This endpoint needs to be implemented in the backend")
                else:
                    error_text = await response.text()
                    print(f"❌ Direct OpenAI test failed: {response.status}")
                    print(f"📄 Error: {error_text}")
        except Exception as e:
            print(f"❌ Direct OpenAI test error: {e}")
        print()

    # Test Summary
    print("📋 Test Summary")
    print("=" * 30)

    total_tests = 6
    passed_tests = sum(
        [
            test_results["openai_connection"],
            test_results["confidence_analysis"],
            test_results["shipping_arbitrage"],
            test_results["cost_tracking"],
            test_results["api_endpoints"],
            len(test_results["response_times"]) > 0,  # At least one response
        ]
    )

    print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
    print(f"💰 Total API Cost: ${test_results['total_cost']:.4f}")

    if test_results["response_times"]:
        avg_response_time = sum(test_results["response_times"]) / len(
            test_results["response_times"]
        )
        print(f"⏱️  Average Response Time: {avg_response_time:.3f}s")
        print(f"⏱️  Max Response Time: {max(test_results['response_times']):.3f}s")

    print()
    print("🔧 Required Backend Implementations:")
    if not test_results["confidence_analysis"]:
        print("   • /api/v1/ai/ai/confidence-analysis endpoint")
    if not test_results["shipping_arbitrage"]:
        print("   • /api/v1/shipping/v1/shipping/arbitrage endpoint")
    if not test_results["cost_tracking"]:
        print("   • /api/v1/ai/ai/usage-stats endpoint")
    if not test_results["api_endpoints"]:
        print("   • /api/v1/ai/ai/generate-text endpoint")

    print()
    print("🎯 Production Readiness Status:")
    if passed_tests >= 4:
        print("✅ READY - Most core functionality working")
    elif passed_tests >= 2:
        print("⚠️  PARTIAL - Some functionality needs implementation")
    else:
        print("❌ NOT READY - Major implementation required")

    return test_results


async def main():
    """Main test execution."""
    try:
        results = await test_openai_integration()

        # Save results to file for evidence
        with open("openai_integration_test_results.json", "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "test_results": results,
                    "summary": {
                        "total_tests": 6,
                        "passed_tests": sum(
                            [
                                results["openai_connection"],
                                results["confidence_analysis"],
                                results["shipping_arbitrage"],
                                results["cost_tracking"],
                                results["api_endpoints"],
                                len(results["response_times"]) > 0,
                            ]
                        ),
                        "total_cost": results["total_cost"],
                        "avg_response_time": (
                            sum(results["response_times"])
                            / len(results["response_times"])
                            if results["response_times"]
                            else 0
                        ),
                    },
                },
                f,
                indent=2,
            )

        print("💾 Test results saved to: openai_integration_test_results.json")

    except Exception as e:
        print(f"❌ Test execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
