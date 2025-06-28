#!/usr/bin/env python3
"""
FlipSync Mobile App Chat Connectivity Investigation
Comprehensive analysis of chat feature connectivity issues
"""
import asyncio
import aiohttp
import websockets
import json
import time
import sys
from datetime import datetime


class MobileChatConnectivityInvestigation:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.mobile_url = "http://localhost:3000"
        self.findings = {}

    async def investigate_port_configuration(self):
        """Investigate port configuration issues"""
        print("🔍 Investigation 1: Port Configuration Analysis")
        print("=" * 60)

        # Test different port configurations
        ports_to_test = [
            ("Backend API", "http://localhost:8001/health"),
            ("Mobile App", "http://localhost:3000"),
        ]

        results = {}

        for name, url in ports_to_test:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        url, timeout=aiohttp.ClientTimeout(total=5)
                    ) as response:
                        results[name] = {
                            "status": response.status,
                            "accessible": True,
                            "url": url,
                        }
                        print(f"  ✅ {name}: {response.status} - {url}")
            except Exception as e:
                results[name] = {
                    "status": None,
                    "accessible": False,
                    "error": str(e),
                    "url": url,
                }
                print(f"  ❌ {name}: Failed - {url} ({e})")

        self.findings["port_configuration"] = results
        return results

    async def investigate_websocket_endpoints(self):
        """Investigate WebSocket endpoint configurations"""
        print("\n🔍 Investigation 2: WebSocket Endpoint Analysis")
        print("=" * 60)

        # Test different WebSocket endpoints based on Flutter config
        websocket_endpoints = [
            (
                "Chat WebSocket (Flutter Config)",
                "ws://localhost:8001/api/v1/ws/chat/main",
            ),
            ("Basic WebSocket", "ws://localhost:8001/api/v1/ws"),
            ("Alternative Chat", "ws://localhost:8001/ws/chat"),
            ("System WebSocket", "ws://localhost:8001/api/v1/ws/system"),
        ]

        results = {}

        for name, ws_url in websocket_endpoints:
            try:
                print(f"  🔌 Testing {name}: {ws_url}")

                async with websockets.connect(ws_url, timeout=10) as websocket:
                    print(f"    ✅ Connection established")

                    # Send test message
                    test_message = {
                        "type": "message",
                        "conversation_id": "main",
                        "data": {
                            "id": f"test_{int(time.time())}",
                            "content": "Test connectivity from investigation",
                            "sender": "user",
                            "timestamp": datetime.now().isoformat(),
                        },
                    }

                    await websocket.send(json.dumps(test_message))
                    print(f"    ✅ Test message sent")

                    # Wait for response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        response_data = json.loads(response)
                        print(
                            f"    ✅ Response received: {response_data.get('type', 'unknown')}"
                        )

                        results[name] = {
                            "accessible": True,
                            "url": ws_url,
                            "response_type": response_data.get("type"),
                            "response_data": response_data,
                        }
                    except asyncio.TimeoutError:
                        print(f"    ⚠️ No response received (timeout)")
                        results[name] = {
                            "accessible": True,
                            "url": ws_url,
                            "response_type": "timeout",
                            "note": "Connection established but no response",
                        }

            except Exception as e:
                print(f"    ❌ Connection failed: {e}")
                results[name] = {"accessible": False, "url": ws_url, "error": str(e)}

        self.findings["websocket_endpoints"] = results
        return results

    async def investigate_mobile_api_configuration(self):
        """Investigate mobile app API configuration"""
        print("\n🔍 Investigation 3: Mobile App API Configuration")
        print("=" * 60)

        # Check if mobile app is using correct backend URL
        try:
            async with aiohttp.ClientSession() as session:
                # Get mobile app HTML to check for configuration
                async with session.get(self.mobile_url) as response:
                    html_content = await response.text()

                    # Look for API configuration in the HTML
                    config_indicators = [
                        "10.0.2.2:8001",  # Android emulator localhost
                        "localhost:8001",  # Direct localhost
                        "api_base_url",
                        "ws_base_url",
                    ]

                    found_configs = []
                    for indicator in config_indicators:
                        if indicator.lower() in html_content.lower():
                            found_configs.append(indicator)

                    print(f"  📱 Mobile app HTML analysis:")
                    print(f"    - Response status: {response.status}")
                    print(f"    - Content length: {len(html_content)} bytes")
                    print(f"    - Configuration indicators found: {found_configs}")

                    # Check if it's a Flutter web app
                    is_flutter = "flutter" in html_content.lower()
                    has_main_dart = "main.dart" in html_content.lower()

                    print(f"    - Flutter app detected: {is_flutter}")
                    print(f"    - Main.dart referenced: {has_main_dart}")

                    self.findings["mobile_api_config"] = {
                        "status": response.status,
                        "is_flutter": is_flutter,
                        "has_main_dart": has_main_dart,
                        "config_indicators": found_configs,
                        "content_length": len(html_content),
                    }

        except Exception as e:
            print(f"  ❌ Mobile app analysis failed: {e}")
            self.findings["mobile_api_config"] = {"error": str(e)}

    async def investigate_backend_agent_responses(self):
        """Investigate backend agent response capability"""
        print("\n🔍 Investigation 4: Backend Agent Response Testing")
        print("=" * 60)

        try:
            # Test direct API call to backend
            async with aiohttp.ClientSession() as session:
                # Test health endpoint
                async with session.get(f"{self.backend_url}/health") as response:
                    health_data = await response.json()
                    print(f"  ✅ Backend health: {health_data.get('status')}")

                # Test if there's a chat API endpoint
                chat_endpoints = [
                    "/api/v1/chat/message",
                    "/api/v1/agents/status",
                    "/api/v1/ws/test",
                ]

                for endpoint in chat_endpoints:
                    try:
                        async with session.get(f"{self.backend_url}{endpoint}") as resp:
                            print(f"  ✅ {endpoint}: {resp.status}")
                    except Exception as e:
                        print(f"  ❌ {endpoint}: {e}")

                # Test WebSocket chat endpoint with proper authentication
                print(f"  🔌 Testing WebSocket chat with backend...")

                ws_url = "ws://localhost:8001/api/v1/ws/chat/investigation"
                async with websockets.connect(ws_url) as websocket:
                    # Send Flutter-style message
                    flutter_message = {
                        "type": "message",
                        "conversation_id": "investigation",
                        "data": {
                            "id": f"investigation_{int(time.time())}",
                            "content": "Test agent response for mobile connectivity investigation",
                            "sender": "user",
                            "timestamp": datetime.now().isoformat(),
                        },
                    }

                    await websocket.send(json.dumps(flutter_message))
                    print(f"    ✅ Investigation message sent")

                    # Wait for agent response
                    timeout_seconds = 30
                    start_time = time.time()

                    while time.time() - start_time < timeout_seconds:
                        try:
                            response = await asyncio.wait_for(
                                websocket.recv(), timeout=5.0
                            )
                            response_data = json.loads(response)

                            message_type = response_data.get("type")
                            print(f"    📨 Received: {message_type}")

                            if (
                                message_type == "message"
                                and response_data.get("data", {}).get("sender")
                                == "assistant"
                            ):
                                agent_response = response_data.get("data", {}).get(
                                    "content", ""
                                )
                                print(
                                    f"    🤖 Agent response: {agent_response[:100]}..."
                                )

                                self.findings["backend_agent_responses"] = {
                                    "working": True,
                                    "response_time": time.time() - start_time,
                                    "agent_response": agent_response[:200],
                                    "message_type": message_type,
                                }
                                break

                        except asyncio.TimeoutError:
                            continue
                    else:
                        print(
                            f"    ⚠️ No agent response received within {timeout_seconds}s"
                        )
                        self.findings["backend_agent_responses"] = {
                            "working": False,
                            "timeout": timeout_seconds,
                            "note": "WebSocket connected but no agent response",
                        }

        except Exception as e:
            print(f"  ❌ Backend agent testing failed: {e}")
            self.findings["backend_agent_responses"] = {"error": str(e)}

    async def investigate_cors_and_security(self):
        """Investigate CORS and security configuration"""
        print("\n🔍 Investigation 5: CORS and Security Analysis")
        print("=" * 60)

        try:
            async with aiohttp.ClientSession() as session:
                # Test CORS headers from backend
                async with session.options(f"{self.backend_url}/health") as response:
                    cors_headers = {
                        "Access-Control-Allow-Origin": response.headers.get(
                            "Access-Control-Allow-Origin"
                        ),
                        "Access-Control-Allow-Methods": response.headers.get(
                            "Access-Control-Allow-Methods"
                        ),
                        "Access-Control-Allow-Headers": response.headers.get(
                            "Access-Control-Allow-Headers"
                        ),
                    }

                    print(f"  🔒 CORS Headers Analysis:")
                    for header, value in cors_headers.items():
                        print(f"    - {header}: {value or 'Not set'}")

                    # Check if localhost:3000 is allowed
                    origin_header = cors_headers.get("Access-Control-Allow-Origin")
                    localhost_allowed = (
                        origin_header == "*"
                        or "localhost:3000" in (origin_header or "")
                        or "localhost" in (origin_header or "")
                    )

                    print(f"    - Localhost:3000 allowed: {localhost_allowed}")

                    self.findings["cors_security"] = {
                        "cors_headers": cors_headers,
                        "localhost_allowed": localhost_allowed,
                    }

        except Exception as e:
            print(f"  ❌ CORS analysis failed: {e}")
            self.findings["cors_security"] = {"error": str(e)}

    async def run_comprehensive_investigation(self):
        """Run comprehensive mobile chat connectivity investigation"""
        print("🔍 FlipSync Mobile App Chat Connectivity Investigation")
        print("=" * 80)

        # Run all investigations
        await self.investigate_port_configuration()
        await self.investigate_websocket_endpoints()
        await self.investigate_mobile_api_configuration()
        await self.investigate_backend_agent_responses()
        await self.investigate_cors_and_security()

        # Generate summary report
        print("\n📊 INVESTIGATION SUMMARY REPORT")
        print("=" * 80)

        # Port Configuration Summary
        port_config = self.findings.get("port_configuration", {})
        backend_accessible = port_config.get("Backend API", {}).get("accessible", False)
        mobile_accessible = port_config.get("Mobile App", {}).get("accessible", False)

        print(f"🔌 Port Configuration:")
        print(
            f"  - Backend API (8001): {'✅ Accessible' if backend_accessible else '❌ Not accessible'}"
        )
        print(
            f"  - Mobile App (3000): {'✅ Accessible' if mobile_accessible else '❌ Not accessible'}"
        )

        # WebSocket Summary
        ws_results = self.findings.get("websocket_endpoints", {})
        working_endpoints = [
            name for name, data in ws_results.items() if data.get("accessible")
        ]

        print(f"🔌 WebSocket Endpoints:")
        print(f"  - Working endpoints: {len(working_endpoints)}/{len(ws_results)}")
        for endpoint in working_endpoints:
            print(f"    ✅ {endpoint}")

        # Agent Response Summary
        agent_responses = self.findings.get("backend_agent_responses", {})
        agents_working = agent_responses.get("working", False)

        print(f"🤖 Agent Responses:")
        print(f"  - Agent system working: {'✅ Yes' if agents_working else '❌ No'}")
        if agents_working:
            response_time = agent_responses.get("response_time", 0)
            print(f"  - Response time: {response_time:.2f}s")

        # CORS Summary
        cors_data = self.findings.get("cors_security", {})
        localhost_allowed = cors_data.get("localhost_allowed", False)

        print(f"🔒 Security Configuration:")
        print(
            f"  - CORS allows localhost:3000: {'✅ Yes' if localhost_allowed else '❌ No'}"
        )

        # Overall Assessment
        critical_issues = []
        if not backend_accessible:
            critical_issues.append("Backend API not accessible")
        if not mobile_accessible:
            critical_issues.append("Mobile app not accessible")
        if not agents_working:
            critical_issues.append("Agent responses not working")
        if not localhost_allowed:
            critical_issues.append("CORS blocking mobile app")

        print(f"\n🎯 CRITICAL ISSUES IDENTIFIED: {len(critical_issues)}")
        for issue in critical_issues:
            print(f"  ❌ {issue}")

        if not critical_issues:
            print("  ✅ No critical connectivity issues found!")

        return self.findings


async def main():
    investigation = MobileChatConnectivityInvestigation()
    findings = await investigation.run_comprehensive_investigation()
    return findings


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n🔍 Investigation complete. Findings: {len(result)} areas analyzed.")
