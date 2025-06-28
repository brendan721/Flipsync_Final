#!/usr/bin/env python3
"""
Chat System Debug Test
Comprehensive test to identify why chat responses are not working
"""
import asyncio
import aiohttp
import json
import time
import websockets
import jwt
from datetime import datetime


class ChatSystemDebugTest:
    def __init__(self):
        self.backend_url = "http://localhost:8001"
        self.test_results = {}

    async def get_auth_token(self):
        """Get authentication token for API calls"""
        try:
            # Create JWT token for testing
            secret = "development-jwt-secret-not-for-production-use"
            payload = {
                "sub": "test_user_debug",
                "iat": int(time.time()),
                "exp": int(time.time()) + 3600,
                "user_id": "test_user_debug",
                "email": "debug@test.com",
            }
            token = jwt.encode(payload, secret, algorithm="HS256")
            return token
        except Exception as e:
            print(f"❌ Auth token error: {e}")
            return None

    async def test_websocket_chat_endpoint(self, token):
        """Test the actual WebSocket chat endpoint that mobile app uses"""
        print("\n🔌 Testing WebSocket Chat Endpoint...")
        try:
            conversation_id = "debug_test_conversation"
            uri = f"ws://localhost:8001/api/v1/ws/chat/{conversation_id}?token={token}&client_id=debug_test_client"

            print(f"  📡 Connecting to: {uri}")

            async with websockets.connect(uri) as websocket:
                print(f"  ✅ WebSocket connected successfully")

                # Send test message exactly like mobile app does
                message = {
                    "type": "message",
                    "conversation_id": conversation_id,
                    "data": {
                        "id": f"debug_test_{int(time.time())}",
                        "content": "Hello, I need help with eBay listing optimization. Can you help me analyze my product and create a better listing?",
                        "sender": "user",
                        "timestamp": datetime.now().isoformat(),
                    },
                }

                print(f"  📤 Sending message: {json.dumps(message, indent=2)}")
                await websocket.send(json.dumps(message))
                print(f"  ✅ Message sent successfully")

                # Wait for responses with detailed logging
                responses_received = 0
                timeout_seconds = 30
                start_time = time.time()

                while time.time() - start_time < timeout_seconds:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        responses_received += 1
                        response_data = json.loads(response)

                        print(
                            f"  📥 Response {responses_received}: {json.dumps(response_data, indent=2)}"
                        )

                        # Check if this is an agent response
                        if (
                            response_data.get("type") == "message"
                            and response_data.get("data", {}).get("sender") == "agent"
                        ):
                            print(f"  🤖 AGENT RESPONSE DETECTED!")
                            print(
                                f"  🤖 Content: {response_data.get('data', {}).get('content', 'No content')}"
                            )
                            print(
                                f"  🤖 Agent Type: {response_data.get('data', {}).get('agent_type', 'No agent type')}"
                            )

                            self.test_results["agent_response_received"] = True
                            self.test_results["agent_response_content"] = (
                                response_data.get("data", {}).get("content", "")
                            )
                            return True

                        # Check for typing indicators
                        elif response_data.get("type") == "typing":
                            typing_status = response_data.get("data", {}).get(
                                "is_typing", False
                            )
                            print(f"  ⌨️ Typing indicator: {typing_status}")

                            if typing_status:
                                print(f"  ⌨️ Agent is typing... waiting for response")
                            else:
                                print(f"  ⌨️ Agent stopped typing")

                        # Check for ping/pong
                        elif response_data.get("type") == "ping":
                            print(f"  🏓 Ping received, sending pong...")
                            pong_message = {
                                "type": "pong",
                                "timestamp": response_data.get(
                                    "timestamp", datetime.now().isoformat()
                                ),
                            }
                            await websocket.send(json.dumps(pong_message))
                            print(f"  🏓 Pong sent")

                        # Check for errors
                        elif response_data.get("type") == "error":
                            print(
                                f"  ❌ Error response: {response_data.get('content', 'Unknown error')}"
                            )
                            self.test_results["websocket_error"] = response_data.get(
                                "content", "Unknown error"
                            )
                            return False

                    except asyncio.TimeoutError:
                        print(f"  ⏰ No response in 5 seconds, continuing to wait...")
                        continue
                    except Exception as e:
                        print(f"  ❌ Error receiving response: {e}")
                        break

                print(f"  ⏰ Test completed after {timeout_seconds} seconds")
                print(f"  📊 Total responses received: {responses_received}")

                if responses_received == 0:
                    print(
                        f"  ❌ NO RESPONSES RECEIVED - This indicates a backend processing issue"
                    )
                    self.test_results["no_responses"] = True
                elif not self.test_results.get("agent_response_received", False):
                    print(
                        f"  ⚠️ Responses received but no agent response - check agent coordination"
                    )
                    self.test_results["no_agent_response"] = True

                return self.test_results.get("agent_response_received", False)

        except Exception as e:
            print(f"  ❌ WebSocket test failed: {e}")
            self.test_results["websocket_connection_failed"] = str(e)
            return False

    async def test_rest_api_chat_endpoint(self, token):
        """Test the REST API chat endpoint as fallback"""
        print("\n🌐 Testing REST API Chat Endpoint...")
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            }

            # Create conversation first
            conversation_data = {
                "title": "Debug Test Conversation",
                "description": "Testing REST API chat functionality",
            }

            async with aiohttp.ClientSession() as session:
                # Create conversation
                async with session.post(
                    f"{self.backend_url}/api/v1/chat/conversations",
                    headers=headers,
                    json=conversation_data,
                ) as response:
                    if response.status in [200, 201]:
                        conversation = await response.json()
                        conversation_id = conversation.get("id") or conversation.get(
                            "conversation_id"
                        )
                        print(f"  ✅ Conversation created: {conversation_id}")
                    else:
                        print(f"  ❌ Failed to create conversation: {response.status}")
                        return False

                # Send message
                message_data = {
                    "text": "Hello, I need help with eBay listing optimization. Can you help me analyze my product and create a better listing?",
                    "sender": "user",
                }

                print(f"  📤 Sending message via REST API...")
                async with session.post(
                    f"{self.backend_url}/api/v1/chat/conversations/{conversation_id}/messages",
                    headers=headers,
                    json=message_data,
                ) as response:
                    print(f"  📡 Message send response: {response.status}")

                    if response.status in [200, 201]:
                        message_response = await response.json()
                        print(f"  ✅ Message sent successfully")

                        # Wait for agent processing
                        await asyncio.sleep(5)

                        # Get messages to see if agent responded
                        async with session.get(
                            f"{self.backend_url}/api/v1/chat/conversations/{conversation_id}/messages",
                            headers=headers,
                        ) as messages_response:
                            if messages_response.status == 200:
                                messages = await messages_response.json()

                                # The API returns a list directly, not a wrapper object
                                agent_messages = [
                                    msg
                                    for msg in messages
                                    if msg.get("sender") == "agent"
                                ]

                                print(f"  📊 Total messages: {len(messages)}")
                                print(f"  🤖 Agent messages: {len(agent_messages)}")

                                if agent_messages:
                                    latest_agent_message = agent_messages[-1]
                                    print(
                                        f"  🤖 Latest agent response: {latest_agent_message.get('text', '')[:100]}..."
                                    )
                                    self.test_results["rest_api_agent_response"] = True
                                    return True
                                else:
                                    print(f"  ❌ No agent responses found via REST API")
                                    return False
                            else:
                                print(
                                    f"  ❌ Failed to get messages: {messages_response.status}"
                                )
                                return False
                    else:
                        response_text = await response.text()
                        print(f"  ❌ Message send failed: {response.status}")
                        print(f"  ❌ Response: {response_text[:200]}...")
                        return False

        except Exception as e:
            print(f"  ❌ REST API test failed: {e}")
            return False

    async def test_agent_system_health(self):
        """Test if the agent system is healthy and responding"""
        print("\n🤖 Testing Agent System Health...")
        try:
            async with aiohttp.ClientSession() as session:
                # Test agent list endpoint
                async with session.get(f"{self.backend_url}/api/v1/agents") as response:
                    if response.status == 200:
                        agents = await response.json()
                        active_agents = [
                            agent for agent in agents if agent.get("status") == "active"
                        ]

                        print(f"  ✅ Agent system accessible")
                        print(f"  ✅ Total agents: {len(agents)}")
                        print(f"  ✅ Active agents: {len(active_agents)}")

                        # Check for key agent types
                        agent_types = [agent.get("type") for agent in active_agents]
                        has_executive = "executive" in agent_types
                        has_market = "market" in agent_types
                        has_content = "content" in agent_types

                        print(
                            f"  ✅ Executive agents: {'✅' if has_executive else '❌'}"
                        )
                        print(f"  ✅ Market agents: {'✅' if has_market else '❌'}")
                        print(f"  ✅ Content agents: {'✅' if has_content else '❌'}")

                        self.test_results["agent_system_healthy"] = (
                            len(active_agents) >= 20
                        )
                        return len(active_agents) >= 20
                    else:
                        print(f"  ❌ Agent system not accessible: {response.status}")
                        return False

        except Exception as e:
            print(f"  ❌ Agent system health check failed: {e}")
            return False

    async def run_comprehensive_debug_test(self):
        """Run comprehensive debug test to identify chat issues"""
        print("🔍 Chat System Comprehensive Debug Test")
        print("=" * 80)
        print("🎯 Goal: Identify why chat responses are not working")
        print("=" * 80)

        # Get authentication token
        token = await self.get_auth_token()
        if not token:
            print("❌ Failed to get authentication token")
            return False

        print(f"✅ Authentication token obtained")

        # Run tests
        tests = [
            ("Agent System Health", self.test_agent_system_health),
            (
                "WebSocket Chat Endpoint",
                lambda: self.test_websocket_chat_endpoint(token),
            ),
            ("REST API Chat Endpoint", lambda: self.test_rest_api_chat_endpoint(token)),
        ]

        results = {}

        for test_name, test_func in tests:
            try:
                print(f"\n{'='*60}")
                print(f"🧪 Running: {test_name}")
                print(f"{'='*60}")
                result = await test_func()
                results[test_name] = result
                print(f"📊 {test_name}: {'✅ PASS' if result else '❌ FAIL'}")
            except Exception as e:
                print(f"❌ {test_name} failed with exception: {e}")
                results[test_name] = False

        # Analysis and recommendations
        print(f"\n{'='*80}")
        print("🔍 DEBUG ANALYSIS & RECOMMENDATIONS")
        print(f"{'='*80}")

        if not results.get("Agent System Health", False):
            print("❌ ISSUE: Agent system is not healthy")
            print("   💡 SOLUTION: Check agent initialization and health status")

        if not results.get("WebSocket Chat Endpoint", False):
            print("❌ ISSUE: WebSocket chat is not working")
            if self.test_results.get("websocket_connection_failed"):
                print(
                    f"   🔍 Connection Error: {self.test_results['websocket_connection_failed']}"
                )
            elif self.test_results.get("no_responses"):
                print("   🔍 No responses received - backend message processing issue")
            elif self.test_results.get("no_agent_response"):
                print(
                    "   🔍 Responses received but no agent response - agent coordination issue"
                )
            print(
                "   💡 SOLUTION: Check WebSocket message handlers and agent response generation"
            )

        if not results.get("REST API Chat Endpoint", False):
            print("❌ ISSUE: REST API chat is not working")
            print(
                "   💡 SOLUTION: Check REST API message processing and agent integration"
            )

        # Overall assessment
        working_systems = sum(1 for result in results.values() if result)
        total_systems = len(results)

        print(f"\n📊 OVERALL ASSESSMENT:")
        print(f"   Working Systems: {working_systems}/{total_systems}")
        print(f"   Success Rate: {(working_systems/total_systems)*100:.1f}%")

        if working_systems == 0:
            print(f"🚨 CRITICAL: No chat systems are working - complete system failure")
        elif working_systems < total_systems:
            print(
                f"⚠️ PARTIAL: Some chat systems working - investigate failed components"
            )
        else:
            print(f"✅ SUCCESS: All chat systems working properly")

        return working_systems > 0


async def main():
    test_suite = ChatSystemDebugTest()
    success = await test_suite.run_comprehensive_debug_test()
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    print(f"\n🎯 Chat System Debug test {'✅ PASSED' if result else '❌ FAILED'}")
