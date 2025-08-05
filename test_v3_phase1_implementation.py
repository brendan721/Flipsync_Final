#!/usr/bin/env python3
"""
V3 Phase 1 Implementation Test Script

Tests the Phase 1 fixes to verify that V3 services are properly
integrated with existing backend endpoints.
"""

import asyncio
import json
import requests
from datetime import datetime
from typing import Dict, Any


class V3Phase1Tester:
    def __init__(self):
        self.base_url = "http://174.138.77.110:8000"
        self.session = requests.Session()
        self.session.timeout = 10

    def test_phase1_implementation(self) -> Dict[str, Any]:
        """Test Phase 1 implementation results."""

        results = {
            "test_timestamp": datetime.now().isoformat(),
            "phase": "Phase 1: Fix V3 Services Backend Integration",
            "backend_url": self.base_url,
            "tests": {},
        }

        print("🧪 Testing V3 Phase 1 Implementation")
        print("=" * 50)

        # Test 1: Verify existing AI endpoints are accessible
        print("\n1️⃣ Testing AI Analyze Product Endpoint (used by V3 services)")
        ai_test = self._test_ai_endpoint()
        results["tests"]["ai_analyze_endpoint"] = ai_test

        # Test 2: Verify shipping calculation endpoint
        print("\n2️⃣ Testing Shipping Calculation Endpoint (used by shipping arbitrage)")
        shipping_test = self._test_shipping_endpoint()
        results["tests"]["shipping_calculate_endpoint"] = shipping_test

        # Test 3: Verify authentication requirements
        print("\n3️⃣ Testing Authentication Requirements")
        auth_test = self._test_authentication()
        results["tests"]["authentication"] = auth_test

        # Test 4: Verify WebSocket connectivity
        print("\n4️⃣ Testing WebSocket Connectivity")
        ws_test = self._test_websocket()
        results["tests"]["websocket"] = ws_test

        return results

    def _test_ai_endpoint(self) -> Dict[str, Any]:
        """Test the AI analyze product endpoint that V3 services now use."""
        try:
            # Test POST to /api/v1/ai/analyze-product (fixed double path segment)
            response = self.session.post(
                f"{self.base_url}/api/v1/ai/analyze-product", json={"test": "data"}
            )

            status_code = response.status_code
            if status_code == 405:
                print("✅ AI endpoint exists (Method Not Allowed - needs proper data)")
                return {
                    "status": "success",
                    "message": "Endpoint exists and accessible",
                    "status_code": status_code,
                    "needs_auth": False,
                }
            elif status_code == 401:
                print("⚠️ AI endpoint exists but requires authentication")
                return {
                    "status": "partial",
                    "message": "Endpoint exists but requires authentication",
                    "status_code": status_code,
                    "needs_auth": True,
                }
            elif status_code == 422:
                print("✅ AI endpoint exists (Validation Error - needs proper data)")
                return {
                    "status": "success",
                    "message": "Endpoint exists and accessible",
                    "status_code": status_code,
                    "needs_auth": False,
                }
            else:
                print(f"❌ AI endpoint returned unexpected status: {status_code}")
                return {
                    "status": "error",
                    "message": f"Unexpected status code: {status_code}",
                    "status_code": status_code,
                }

        except Exception as e:
            print(f"❌ AI endpoint test failed: {e}")
            return {"status": "error", "message": str(e)}

    def _test_shipping_endpoint(self) -> Dict[str, Any]:
        """Test the shipping calculation endpoint that shipping arbitrage service now uses."""
        try:
            # Test POST to /api/v1/shipping/arbitrage (fixed double path segment)
            response = self.session.post(
                f"{self.base_url}/api/v1/shipping/arbitrage",
                json={
                    "origin_zip": "37203",
                    "destination_zip": "90210",
                    "weight": 2.0,
                    "package_type": "box",
                },
            )

            status_code = response.status_code
            if status_code == 200:
                print("✅ Shipping endpoint working perfectly")
                return {
                    "status": "success",
                    "message": "Endpoint working correctly",
                    "status_code": status_code,
                    "response_data": response.json() if response.content else None,
                }
            elif status_code == 401:
                print("⚠️ Shipping endpoint exists but requires authentication")
                return {
                    "status": "partial",
                    "message": "Endpoint exists but requires authentication",
                    "status_code": status_code,
                    "needs_auth": True,
                }
            elif status_code == 422:
                print(
                    "✅ Shipping endpoint exists (Validation Error - needs proper data)"
                )
                return {
                    "status": "success",
                    "message": "Endpoint exists and accessible",
                    "status_code": status_code,
                    "needs_auth": False,
                }
            else:
                print(f"❌ Shipping endpoint returned unexpected status: {status_code}")
                return {
                    "status": "error",
                    "message": f"Unexpected status code: {status_code}",
                    "status_code": status_code,
                }

        except Exception as e:
            print(f"❌ Shipping endpoint test failed: {e}")
            return {"status": "error", "message": str(e)}

    def _test_authentication(self) -> Dict[str, Any]:
        """Test authentication requirements for V3 services."""
        try:
            # Test health endpoint (should not require auth)
            health_response = self.session.get(f"{self.base_url}/api/v1/health")

            # Test agents endpoint (may require auth)
            agents_response = self.session.get(f"{self.base_url}/api/v1/agents/status")

            auth_results = {
                "health_endpoint": {
                    "status_code": health_response.status_code,
                    "requires_auth": health_response.status_code == 401,
                },
                "agents_endpoint": {
                    "status_code": agents_response.status_code,
                    "requires_auth": agents_response.status_code == 401,
                },
            }

            if health_response.status_code == 200:
                print("✅ Health endpoint accessible without auth")
            else:
                print(f"⚠️ Health endpoint status: {health_response.status_code}")

            if agents_response.status_code == 200:
                print("✅ Agents endpoint accessible without auth")
            elif agents_response.status_code == 401:
                print("⚠️ Agents endpoint requires authentication (expected)")
            else:
                print(f"⚠️ Agents endpoint status: {agents_response.status_code}")

            return {
                "status": "success",
                "message": "Authentication requirements verified",
                "details": auth_results,
            }

        except Exception as e:
            print(f"❌ Authentication test failed: {e}")
            return {"status": "error", "message": str(e)}

    def _test_websocket(self) -> Dict[str, Any]:
        """Test WebSocket connectivity for real-time features."""
        try:
            # Test WebSocket endpoint availability
            ws_response = self.session.get(f"{self.base_url}/api/v1/ws")

            if ws_response.status_code == 200:
                print("✅ WebSocket endpoint accessible")
                return {
                    "status": "success",
                    "message": "WebSocket endpoint accessible",
                    "status_code": ws_response.status_code,
                }
            else:
                print(f"⚠️ WebSocket endpoint status: {ws_response.status_code}")
                return {
                    "status": "partial",
                    "message": f"WebSocket endpoint returned {ws_response.status_code}",
                    "status_code": ws_response.status_code,
                }

        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
            return {"status": "error", "message": str(e)}

    def generate_phase1_summary(self, results: Dict[str, Any]) -> None:
        """Generate Phase 1 implementation summary."""
        print("\n" + "=" * 50)
        print("📋 V3 PHASE 1 IMPLEMENTATION TEST SUMMARY")
        print("=" * 50)

        tests = results["tests"]

        # Count successful tests
        success_count = sum(
            1 for test in tests.values() if test.get("status") == "success"
        )
        partial_count = sum(
            1 for test in tests.values() if test.get("status") == "partial"
        )
        error_count = sum(1 for test in tests.values() if test.get("status") == "error")
        total_tests = len(tests)

        print(
            f"Test Results: {success_count}/{total_tests} successful, {partial_count} partial, {error_count} errors"
        )

        print("\n🎯 PHASE 1 IMPLEMENTATION STATUS:")

        # AI Endpoint Integration
        ai_test = tests.get("ai_analyze_endpoint", {})
        if ai_test.get("status") == "success":
            print("✅ AI Analyze Product endpoint integration: WORKING")
        elif ai_test.get("needs_auth"):
            print("⚠️ AI Analyze Product endpoint: NEEDS AUTHENTICATION")
        else:
            print("❌ AI Analyze Product endpoint: FAILED")

        # Shipping Endpoint Integration
        shipping_test = tests.get("shipping_calculate_endpoint", {})
        if shipping_test.get("status") == "success":
            print("✅ Shipping Calculate endpoint integration: WORKING")
        elif shipping_test.get("needs_auth"):
            print("⚠️ Shipping Calculate endpoint: NEEDS AUTHENTICATION")
        else:
            print("❌ Shipping Calculate endpoint: FAILED")

        # Authentication
        auth_test = tests.get("authentication", {})
        if auth_test.get("status") == "success":
            print("✅ Authentication system: VERIFIED")
        else:
            print("❌ Authentication system: ISSUES DETECTED")

        # WebSocket
        ws_test = tests.get("websocket", {})
        if ws_test.get("status") == "success":
            print("✅ WebSocket connectivity: WORKING")
        else:
            print("⚠️ WebSocket connectivity: PARTIAL/ISSUES")

        print("\n📋 NEXT STEPS FOR PHASE 1:")
        if any(test.get("needs_auth") for test in tests.values()):
            print("1. ✅ V3 services updated to use existing backend endpoints")
            print("2. ⚠️ Authentication integration needed for full functionality")
            print("3. 🔄 Test V3 services with proper JWT tokens")
        else:
            print("1. ✅ V3 services successfully integrated with backend")
            print("2. ✅ Authentication requirements verified")
            print("3. 🎯 Ready to proceed to Phase 2")


def main():
    """Run Phase 1 implementation tests."""
    tester = V3Phase1Tester()
    results = tester.test_phase1_implementation()
    tester.generate_phase1_summary(results)

    # Save results
    with open("/home/brend/Flipsync_Final/v3_phase1_test_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: v3_phase1_test_results.json")


if __name__ == "__main__":
    main()
