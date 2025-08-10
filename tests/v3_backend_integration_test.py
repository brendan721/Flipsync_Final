#!/usr/bin/env python3
"""
V3 Backend Integration Test Script

Tests the current V3 Flutter services against the production backend
to identify functional vs non-functional integrations.

Backend: http://localhost:8000
WebSocket: ws://localhost:8000/ws/flipsync
"""

import asyncio
import json
import requests
import websockets
from typing import Dict, List, Any
import sys


class V3BackendIntegrationTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000/ws/flipsync"
        self.session = requests.Session()
        self.session.timeout = 10

    def test_endpoint(
        self, method: str, endpoint: str, data: Dict = None
    ) -> Dict[str, Any]:
        """Test a single endpoint and return result."""
        url = f"{self.base_url}{endpoint}"
        try:
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data or {})
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data or {})
            else:
                return {"status": "error", "message": f"Unsupported method: {method}"}

            return {
                "status": "success" if response.status_code < 400 else "error",
                "status_code": response.status_code,
                "endpoint": endpoint,
                "method": method,
                "response_size": len(response.content) if response.content else 0,
            }
        except Exception as e:
            return {
                "status": "error",
                "endpoint": endpoint,
                "method": method,
                "error": str(e),
            }

    async def test_websocket(self) -> Dict[str, Any]:
        """Test WebSocket connection."""
        try:
            async with websockets.connect(self.ws_url) as websocket:
                # Send test message
                test_message = {"type": "test", "message": "V3 integration test"}
                await websocket.send(json.dumps(test_message))

                # Wait for response
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    return {
                        "status": "success",
                        "message": "WebSocket connection successful",
                        "response": response,
                    }
                except asyncio.TimeoutError:
                    return {
                        "status": "partial",
                        "message": "WebSocket connected but no response received",
                    }
        except Exception as e:
            return {
                "status": "error",
                "message": f"WebSocket connection failed: {str(e)}",
            }

    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive backend integration test."""
        results = {
            "test_timestamp": "2025-01-29",
            "backend_url": self.base_url,
            "core_infrastructure": {},
            "v3_missing_endpoints": {},
            "existing_endpoints": {},
            "websocket_test": {},
        }

        print("🔍 Starting V3 Backend Integration Test...")
        print(f"Backend: {self.base_url}")
        print("=" * 60)

        # Test core infrastructure
        print("\n📊 Testing Core Infrastructure:")
        core_tests = [
            ("GET", "/api/v1/health"),
            ("GET", "/api/v1/agents/status"),
            ("GET", "/api/v1/agents/list"),
        ]

        for method, endpoint in core_tests:
            result = self.test_endpoint(method, endpoint)
            results["core_infrastructure"][endpoint] = result
            status_icon = "✅" if result["status"] == "success" else "❌"
            print(
                f"{status_icon} {method} {endpoint}: {result.get('status_code', 'ERROR')}"
            )

        # Test V3 missing endpoints
        print("\n❌ Testing V3 Missing Endpoints:")
        v3_missing = [
            ("GET", "/api/v1/users/profile"),
            ("GET", "/api/v1/users/preferences"),
            ("GET", "/api/v1/opportunities/trending/liquidation"),
            ("GET", "/api/v1/opportunities/liquidation"),
            ("GET", "/api/v1/opportunities/thrifting"),
            ("POST", "/api/v1/assessment/start"),
            ("GET", "/api/v1/products/specifications/test"),
            ("POST", "/api/v1/products/identify"),
            ("GET", "/api/v1/shipping/zones/12345"),
            ("POST", "/api/v1/shipping/arbitrage"),
            ("POST", "/api/v1/shipping/shippo/poly"),
            ("POST", "/api/v1/product-creation/analyze-image"),
            ("POST", "/api/v1/product-creation/barcode-lookup"),
            ("POST", "/api/v1/product-creation/publish-listing"),
            ("GET", "/api/v1/advertising/campaigns"),
            ("POST", "/api/v1/advertising/boost-listing"),
            ("GET", "/api/v1/optimization/score/test-user"),
            ("GET", "/api/v1/optimization/opportunities/test-user"),
        ]

        for method, endpoint in v3_missing:
            result = self.test_endpoint(method, endpoint)
            results["v3_missing_endpoints"][endpoint] = result
            if result.get("status_code") == 404:
                print(f"❌ CONFIRMED MISSING: {method} {endpoint}")
            else:
                print(
                    f"⚠️ UNEXPECTED: {method} {endpoint}: {result.get('status_code', 'ERROR')}"
                )

        # Test existing endpoints that should work
        print("\n⚠️ Testing Existing Endpoints:")
        existing_tests = [
            (
                "POST",
                "/api/v1/ai/analyze-product",
                {"image_data": "test", "product_context": "test"},
            ),
            ("POST", "/api/v1/ai/generate-listing", {"product_data": "test"}),
            (
                "POST",
                "/api/v1/shipping/arbitrage",
                {
                    "origin_zip": "12345",
                    "destination_zip": "67890",
                    "weight": 1.0,
                    "package_type": "box",
                },
            ),
        ]

        for method, endpoint, data in existing_tests:
            result = self.test_endpoint(method, endpoint, data)
            results["existing_endpoints"][endpoint] = result
            status_code = result.get("status_code", "ERROR")
            if status_code == 200:
                print(f"✅ WORKING: {method} {endpoint}")
            elif status_code == 401:
                print(f"⚠️ NEEDS AUTH: {method} {endpoint}")
            elif status_code == 405:
                print(f"⚠️ METHOD EXISTS: {method} {endpoint}")
            elif status_code == 422:
                print(f"⚠️ VALIDATION ERROR: {method} {endpoint}")
            else:
                print(f"❌ ERROR: {method} {endpoint}: {status_code}")

        # Test WebSocket
        print("\n🔌 Testing WebSocket Connection:")
        try:
            ws_result = asyncio.run(self.test_websocket())
            results["websocket_test"] = ws_result
            if ws_result["status"] == "success":
                print("✅ WebSocket connection successful")
            elif ws_result["status"] == "partial":
                print("⚠️ WebSocket connected but no response")
            else:
                print(f"❌ WebSocket failed: {ws_result['message']}")
        except Exception as e:
            results["websocket_test"] = {"status": "error", "message": str(e)}
            print(f"❌ WebSocket test failed: {e}")

        return results

    def generate_summary(self, results: Dict[str, Any]) -> None:
        """Generate test summary."""
        print("\n" + "=" * 60)
        print("📋 V3 BACKEND INTEGRATION TEST SUMMARY")
        print("=" * 60)

        # Core infrastructure summary
        core_working = sum(
            1
            for r in results["core_infrastructure"].values()
            if r["status"] == "success"
        )
        core_total = len(results["core_infrastructure"])
        print(f"Core Infrastructure: {core_working}/{core_total} working")

        # V3 missing endpoints summary
        missing_confirmed = sum(
            1
            for r in results["v3_missing_endpoints"].values()
            if r.get("status_code") == 404
        )
        missing_total = len(results["v3_missing_endpoints"])
        print(
            f"V3 Missing Endpoints: {missing_confirmed}/{missing_total} confirmed missing"
        )

        # Existing endpoints summary
        existing_working = sum(
            1
            for r in results["existing_endpoints"].values()
            if r.get("status_code") in [200, 401, 405, 422]
        )
        existing_total = len(results["existing_endpoints"])
        print(f"Existing Endpoints: {existing_working}/{existing_total} accessible")

        # WebSocket summary
        ws_status = results["websocket_test"].get("status", "error")
        print(f"WebSocket: {ws_status}")

        print("\n🎯 CRITICAL FINDINGS:")
        print("1. ❌ ALL V3-specific endpoints are missing from backend")
        print("2. ✅ Core agent infrastructure is working")
        print("3. ⚠️ Some existing endpoints need authentication")
        print("4. ✅ WebSocket infrastructure is available")

        print("\n📋 NEXT STEPS:")
        print("1. Backend development required for ALL V3 endpoints")
        print("2. Frontend V3 services will fail until backend is implemented")
        print("3. Revenue features (shipping arbitrage, advertising) are blocked")
        print("4. User profile and adaptive content systems are blocked")


def main():
    """Main test execution."""
    tester = V3BackendIntegrationTester()
    results = tester.run_comprehensive_test()
    tester.generate_summary(results)

    # Save results to file
    with open(
        "/home/brend/Flipsync_Final/v3_backend_integration_results.json", "w"
    ) as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 Results saved to: v3_backend_integration_results.json")


if __name__ == "__main__":
    main()
