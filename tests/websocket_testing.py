#!/usr/bin/env python3

"""
FlipSync WebSocket Testing and Optimization
==========================================
Comprehensive WebSocket testing and performance optimization
"""

import asyncio
import json
import logging
import time
import websockets
from datetime import datetime
from typing import Dict, List, Optional
import uuid

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('flipsync-websocket-test')

class WebSocketTester:
    """Comprehensive WebSocket testing for FlipSync"""
    
    def __init__(self, base_url: str = "wss://www.flipsyncai.com"):
        self.base_url = base_url
        self.websocket_url = f"{base_url}/ws/flipsync"
        self.test_results = []
        
    async def test_basic_connection(self) -> Dict:
        """Test basic WebSocket connection"""
        logger.info("Testing basic WebSocket connection...")
        
        start_time = time.time()
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                connection_time = time.time() - start_time
                
                # Test ping/pong
                ping_start = time.time()
                await websocket.ping()
                ping_time = time.time() - ping_start
                
                result = {
                    "test": "basic_connection",
                    "status": "success",
                    "connection_time_ms": round(connection_time * 1000, 2),
                    "ping_time_ms": round(ping_time * 1000, 2),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info(f"✅ Basic connection test passed: {connection_time*1000:.2f}ms")
                return result
                
        except Exception as e:
            result = {
                "test": "basic_connection",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.error(f"❌ Basic connection test failed: {e}")
            return result
    
    async def test_message_exchange(self) -> Dict:
        """Test message sending and receiving"""
        logger.info("Testing message exchange...")
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Send test message
                test_message = {
                    "type": "chat_message",
                    "conversation_id": str(uuid.uuid4()),
                    "message": "Hello, this is a test message",
                    "user_id": "test_user",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                send_start = time.time()
                await websocket.send(json.dumps(test_message))
                
                # Wait for response
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_time = time.time() - send_start
                
                response_data = json.loads(response)
                
                result = {
                    "test": "message_exchange",
                    "status": "success",
                    "response_time_ms": round(response_time * 1000, 2),
                    "message_sent": test_message,
                    "response_received": response_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info(f"✅ Message exchange test passed: {response_time*1000:.2f}ms")
                return result
                
        except asyncio.TimeoutError:
            result = {
                "test": "message_exchange",
                "status": "failed",
                "error": "Response timeout after 10 seconds",
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.error("❌ Message exchange test failed: timeout")
            return result
            
        except Exception as e:
            result = {
                "test": "message_exchange",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.error(f"❌ Message exchange test failed: {e}")
            return result
    
    async def test_concurrent_connections(self, num_connections: int = 5) -> Dict:
        """Test multiple concurrent connections"""
        logger.info(f"Testing {num_connections} concurrent connections...")
        
        async def create_connection(connection_id: int):
            try:
                start_time = time.time()
                async with websockets.connect(self.websocket_url) as websocket:
                    connection_time = time.time() - start_time
                    
                    # Send a test message
                    test_message = {
                        "type": "chat_message",
                        "conversation_id": f"test_conv_{connection_id}",
                        "message": f"Test message from connection {connection_id}",
                        "user_id": f"test_user_{connection_id}",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    await websocket.send(json.dumps(test_message))
                    
                    # Keep connection alive for a short time
                    await asyncio.sleep(2)
                    
                    return {
                        "connection_id": connection_id,
                        "status": "success",
                        "connection_time_ms": round(connection_time * 1000, 2)
                    }
                    
            except Exception as e:
                return {
                    "connection_id": connection_id,
                    "status": "failed",
                    "error": str(e)
                }
        
        try:
            # Create concurrent connections
            start_time = time.time()
            tasks = [create_connection(i) for i in range(num_connections)]
            connection_results = await asyncio.gather(*tasks, return_exceptions=True)
            total_time = time.time() - start_time
            
            successful_connections = sum(1 for r in connection_results if isinstance(r, dict) and r.get("status") == "success")
            
            result = {
                "test": "concurrent_connections",
                "status": "success" if successful_connections == num_connections else "partial",
                "total_connections": num_connections,
                "successful_connections": successful_connections,
                "failed_connections": num_connections - successful_connections,
                "total_time_ms": round(total_time * 1000, 2),
                "connection_results": connection_results,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Concurrent connections test: {successful_connections}/{num_connections} successful")
            return result
            
        except Exception as e:
            result = {
                "test": "concurrent_connections",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.error(f"❌ Concurrent connections test failed: {e}")
            return result
    
    async def test_performance_load(self, duration_seconds: int = 30) -> Dict:
        """Test WebSocket performance under load"""
        logger.info(f"Testing WebSocket performance for {duration_seconds} seconds...")
        
        messages_sent = 0
        messages_received = 0
        errors = 0
        response_times = []
        
        async def send_messages(websocket):
            nonlocal messages_sent, messages_received, errors, response_times
            
            end_time = time.time() + duration_seconds
            
            while time.time() < end_time:
                try:
                    # Send message
                    test_message = {
                        "type": "chat_message",
                        "conversation_id": "load_test_conv",
                        "message": f"Load test message {messages_sent}",
                        "user_id": "load_test_user",
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    send_start = time.time()
                    await websocket.send(json.dumps(test_message))
                    messages_sent += 1
                    
                    # Try to receive response (non-blocking)
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                        response_time = time.time() - send_start
                        response_times.append(response_time)
                        messages_received += 1
                    except asyncio.TimeoutError:
                        pass  # Continue sending messages
                    
                    # Small delay to prevent overwhelming
                    await asyncio.sleep(0.1)
                    
                except Exception as e:
                    errors += 1
                    logger.warning(f"Error during load test: {e}")
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                await send_messages(websocket)
            
            # Calculate statistics
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            min_response_time = min(response_times) if response_times else 0
            max_response_time = max(response_times) if response_times else 0
            
            result = {
                "test": "performance_load",
                "status": "success",
                "duration_seconds": duration_seconds,
                "messages_sent": messages_sent,
                "messages_received": messages_received,
                "errors": errors,
                "messages_per_second": round(messages_sent / duration_seconds, 2),
                "response_rate_percent": round((messages_received / messages_sent) * 100, 2) if messages_sent > 0 else 0,
                "average_response_time_ms": round(avg_response_time * 1000, 2),
                "min_response_time_ms": round(min_response_time * 1000, 2),
                "max_response_time_ms": round(max_response_time * 1000, 2),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            logger.info(f"✅ Performance load test completed: {messages_sent} messages sent, {messages_received} received")
            return result
            
        except Exception as e:
            result = {
                "test": "performance_load",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.error(f"❌ Performance load test failed: {e}")
            return result
    
    async def test_agent_communication(self) -> Dict:
        """Test communication with 4+1 agent architecture"""
        logger.info("Testing 4+1 agent architecture communication...")
        
        try:
            async with websockets.connect(self.websocket_url) as websocket:
                # Test agent status request
                agent_status_message = {
                    "type": "agent_status_request",
                    "conversation_id": str(uuid.uuid4()),
                    "user_id": "test_user",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await websocket.send(json.dumps(agent_status_message))
                
                # Wait for agent status response
                response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                response_data = json.loads(response)
                
                # Test chat with conversational interface
                chat_message = {
                    "type": "chat_message",
                    "conversation_id": str(uuid.uuid4()),
                    "message": "What is the status of all agents?",
                    "user_id": "test_user",
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                await websocket.send(json.dumps(chat_message))
                
                # Wait for chat response
                chat_response = await asyncio.wait_for(websocket.recv(), timeout=15.0)
                chat_response_data = json.loads(chat_response)
                
                result = {
                    "test": "agent_communication",
                    "status": "success",
                    "agent_status_response": response_data,
                    "chat_response": chat_response_data,
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                logger.info("✅ Agent communication test passed")
                return result
                
        except Exception as e:
            result = {
                "test": "agent_communication",
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
            logger.error(f"❌ Agent communication test failed: {e}")
            return result
    
    async def run_all_tests(self) -> Dict:
        """Run all WebSocket tests"""
        logger.info("Starting comprehensive WebSocket testing...")
        
        start_time = time.time()
        
        # Run all tests
        tests = [
            self.test_basic_connection(),
            self.test_message_exchange(),
            self.test_concurrent_connections(5),
            self.test_performance_load(30),
            self.test_agent_communication()
        ]
        
        test_results = await asyncio.gather(*tests, return_exceptions=True)
        
        total_time = time.time() - start_time
        
        # Count successful tests
        successful_tests = sum(1 for result in test_results if isinstance(result, dict) and result.get("status") == "success")
        total_tests = len(test_results)
        
        summary = {
            "websocket_test_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": total_tests - successful_tests,
                "success_rate_percent": round((successful_tests / total_tests) * 100, 2),
                "total_test_time_seconds": round(total_time, 2),
                "websocket_url": self.websocket_url,
                "timestamp": datetime.utcnow().isoformat()
            },
            "detailed_results": test_results
        }
        
        logger.info(f"🎯 WebSocket testing completed: {successful_tests}/{total_tests} tests passed")
        return summary

async def main():
    """Main function to run WebSocket tests"""
    tester = WebSocketTester()
    
    try:
        results = await tester.run_all_tests()
        
        # Save results to file
        with open('/tmp/websocket_test_results.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        # Display summary
        summary = results["websocket_test_summary"]
        print("\n" + "="*60)
        print("WEBSOCKET TESTING SUMMARY")
        print("="*60)
        print(f"📊 Tests: {summary['successful_tests']}/{summary['total_tests']} passed ({summary['success_rate_percent']}%)")
        print(f"⏱️ Total time: {summary['total_test_time_seconds']} seconds")
        print(f"🔗 WebSocket URL: {summary['websocket_url']}")
        print(f"📄 Detailed results saved to: /tmp/websocket_test_results.json")
        
        return 0 if summary['success_rate_percent'] == 100 else 1
        
    except Exception as e:
        logger.error(f"WebSocket testing failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
