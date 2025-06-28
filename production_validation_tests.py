#!/usr/bin/env python3
"""
FlipSync Production Validation Tests
Real end-to-end testing without mocks or simulations
"""

import asyncio
import json
import time
import requests
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import concurrent.futures
import threading
import statistics

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ProductionValidationTester:
    """Comprehensive production validation testing suite."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.test_results = {}
        self.performance_metrics = {}
        self.critical_issues = []
        self.session = requests.Session()
        self.session.timeout = 180  # 3 minutes timeout for AI operations
        
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Log test result with details."""
        self.test_results[test_name] = {
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if not success:
            logger.error(f"   Error: {details.get('error', 'Unknown error')}")
        
    def log_performance_metric(self, metric_name: str, value: float, unit: str = "seconds"):
        """Log performance metric."""
        self.performance_metrics[metric_name] = {
            'value': value,
            'unit': unit,
            'timestamp': datetime.now().isoformat()
        }
        logger.info(f"📊 {metric_name}: {value:.2f} {unit}")

    async def test_real_ai_integration(self) -> bool:
        """Test 1: Real AI Model Integration - No Mocks."""
        logger.info("🔄 Starting Real AI Integration Tests...")
        
        try:
            # Import AI components directly
            from fs_agt_clean.core.ai.llm_adapter import FlipSyncLLMFactory
            from fs_agt_clean.agents.market.ai_market_agent import AIMarketAgent, MarketAnalysisRequest
            
            # Test 1.1: Direct AI Model Response
            start_time = time.time()
            client = FlipSyncLLMFactory.create_smart_client()
            
            # Real product analysis query
            response = await client.generate_response(
                prompt="Analyze the current market for 'Apple AirPods Pro 2nd Generation' including pricing trends, competition, and selling recommendations for eBay sellers.",
                system_prompt="You are a professional market analyst. Provide detailed, actionable insights."
            )
            
            ai_response_time = time.time() - start_time
            self.log_performance_metric("ai_direct_response_time", ai_response_time)
            
            if not response or not response.content:
                self.log_test_result("ai_direct_response", False, {"error": "No response from AI model"})
                return False
                
            # Validate response quality
            response_quality = len(response.content) > 100 and "airpods" in response.content.lower()
            self.log_test_result("ai_direct_response", response_quality, {
                "response_length": len(response.content),
                "response_time": ai_response_time,
                "model": response.model,
                "provider": str(response.provider)
            })
            
            # Test 1.2: Market Analysis Agent with Real Data
            start_time = time.time()
            agent = AIMarketAgent(agent_id="production_test_agent")
            await agent.initialize()
            
            # Real market analysis request
            request = MarketAnalysisRequest(
                product_query="Nintendo Switch OLED Console",
                target_marketplace="all",
                analysis_depth="detailed",
                include_competitors=True,
                price_range=(250.0, 400.0)
            )
            
            analysis_result = await agent.analyze_market(request)
            market_analysis_time = time.time() - start_time
            self.log_performance_metric("market_analysis_time", market_analysis_time)
            
            # Validate analysis result
            analysis_valid = (
                analysis_result is not None and
                hasattr(analysis_result, 'confidence_score') and
                analysis_result.confidence_score > 0.5 and
                hasattr(analysis_result, 'market_summary') and
                len(analysis_result.market_summary) > 50
            )
            
            self.log_test_result("market_analysis_agent", analysis_valid, {
                "confidence_score": getattr(analysis_result, 'confidence_score', 0),
                "analysis_time": market_analysis_time,
                "summary_length": len(getattr(analysis_result, 'market_summary', '')),
                "competitors_found": len(getattr(analysis_result, 'competitor_analysis', []))
            })
            
            # Test 1.3: Concurrent AI Requests (Load Test)
            logger.info("🔄 Testing concurrent AI requests...")
            start_time = time.time()
            
            async def single_ai_request(query_id: int):
                try:
                    response = await client.generate_response(
                        prompt=f"Provide a brief market insight for product category #{query_id}: Electronics",
                        system_prompt="You are a market analyst. Be concise but informative."
                    )
                    return {
                        'query_id': query_id,
                        'success': bool(response and response.content),
                        'response_length': len(response.content) if response else 0,
                        'response_time': time.time()
                    }
                except Exception as e:
                    return {
                        'query_id': query_id,
                        'success': False,
                        'error': str(e),
                        'response_time': time.time()
                    }
            
            # Run 5 concurrent requests
            concurrent_tasks = [single_ai_request(i) for i in range(5)]
            concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
            
            concurrent_test_time = time.time() - start_time
            successful_requests = sum(1 for r in concurrent_results if isinstance(r, dict) and r.get('success', False))
            
            self.log_performance_metric("concurrent_ai_requests_time", concurrent_test_time)
            self.log_test_result("concurrent_ai_requests", successful_requests >= 4, {
                "total_requests": 5,
                "successful_requests": successful_requests,
                "total_time": concurrent_test_time,
                "average_time_per_request": concurrent_test_time / 5
            })
            
            return analysis_valid and response_quality and successful_requests >= 4
            
        except Exception as e:
            self.log_test_result("ai_integration_test", False, {"error": str(e)})
            return False

    def test_live_api_endpoints(self) -> bool:
        """Test 2: Live API Endpoint Testing - Real Requests."""
        logger.info("🔄 Starting Live API Endpoint Tests...")
        
        try:
            # Test 2.1: Health Check
            response = self.session.get(f"{self.base_url}/health")
            health_check = response.status_code == 200 and response.json().get('status') == 'ok'
            self.log_test_result("health_endpoint", health_check, {
                "status_code": response.status_code,
                "response": response.json() if response.status_code == 200 else None
            })
            
            # Test 2.2: Agent Status
            response = self.session.get(f"{self.base_url}/api/v1/agents/status")
            agents_status = response.status_code == 200
            if agents_status:
                agents_data = response.json()
                active_agents = sum(1 for agent in agents_data.get('agents', []) if agent.get('status') == 'active')
                agents_status = active_agents >= 3  # Expect at least 3 active agents
                
            self.log_test_result("agents_status_endpoint", agents_status, {
                "status_code": response.status_code,
                "active_agents": active_agents if agents_status else 0,
                "overall_status": agents_data.get('overall_status') if agents_status else None
            })
            
            # Test 2.3: Chat Conversation Creation
            chat_payload = {
                "title": f"Production Test Chat {datetime.now().strftime('%H:%M:%S')}",
                "agent_type": "general"
            }
            response = self.session.post(f"{self.base_url}/api/v1/chat/conversations", json=chat_payload)
            chat_creation = response.status_code == 200
            conversation_id = None
            
            if chat_creation:
                conversation_data = response.json()
                conversation_id = conversation_data.get('id')
                
            self.log_test_result("chat_creation_endpoint", chat_creation, {
                "status_code": response.status_code,
                "conversation_id": conversation_id
            })
            
            # Test 2.4: Message Sending (if chat creation succeeded)
            message_sending = False
            if chat_creation and conversation_id:
                message_payload = {
                    "text": "Test message for production validation",
                    "role": "user"
                }
                response = self.session.post(
                    f"{self.base_url}/api/v1/chat/conversations/{conversation_id}/messages",
                    json=message_payload
                )
                message_sending = response.status_code == 200
                
            self.log_test_result("message_sending_endpoint", message_sending, {
                "status_code": response.status_code if conversation_id else "N/A - No conversation",
                "conversation_id": conversation_id
            })
            
            return health_check and agents_status and chat_creation
            
        except Exception as e:
            self.log_test_result("live_api_endpoints", False, {"error": str(e)})
            return False

    def test_performance_under_load(self) -> bool:
        """Test 5: Performance and Load Testing."""
        logger.info("🔄 Starting Performance and Load Tests...")
        
        try:
            # Test concurrent API requests
            def make_request(request_id: int) -> Dict[str, Any]:
                start_time = time.time()
                try:
                    response = requests.get(f"{self.base_url}/api/v1/agents/status", timeout=30)
                    response_time = time.time() - start_time
                    return {
                        'request_id': request_id,
                        'success': response.status_code == 200,
                        'response_time': response_time,
                        'status_code': response.status_code
                    }
                except Exception as e:
                    return {
                        'request_id': request_id,
                        'success': False,
                        'response_time': time.time() - start_time,
                        'error': str(e)
                    }
            
            # Run 20 concurrent requests
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(make_request, i) for i in range(20)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            total_time = time.time() - start_time
            successful_requests = sum(1 for r in results if r['success'])
            response_times = [r['response_time'] for r in results if r['success']]
            
            if response_times:
                avg_response_time = statistics.mean(response_times)
                max_response_time = max(response_times)
                min_response_time = min(response_times)
            else:
                avg_response_time = max_response_time = min_response_time = 0
            
            self.log_performance_metric("load_test_total_time", total_time)
            self.log_performance_metric("load_test_avg_response_time", avg_response_time)
            self.log_performance_metric("load_test_max_response_time", max_response_time)
            
            load_test_success = successful_requests >= 18  # 90% success rate
            self.log_test_result("performance_load_test", load_test_success, {
                "total_requests": 20,
                "successful_requests": successful_requests,
                "success_rate": (successful_requests / 20) * 100,
                "avg_response_time": avg_response_time,
                "max_response_time": max_response_time,
                "min_response_time": min_response_time
            })
            
            return load_test_success
            
        except Exception as e:
            self.log_test_result("performance_load_test", False, {"error": str(e)})
            return False

async def main():
    """Run all production validation tests."""
    logger.info("🚀 Starting FlipSync Production Validation Tests")
    logger.info("=" * 80)
    
    tester = ProductionValidationTester()
    
    # Test 1: Real AI Integration
    logger.info("\n📋 Test Category 1: Real AI Model Integration")
    ai_test_result = await tester.test_real_ai_integration()
    
    # Test 2: Live API Endpoints
    logger.info("\n📋 Test Category 2: Live API Endpoints")
    api_test_result = tester.test_live_api_endpoints()
    
    # Test 5: Performance and Load Testing
    logger.info("\n📋 Test Category 5: Performance and Load Testing")
    performance_test_result = tester.test_performance_under_load()
    
    # Generate Summary Report
    logger.info("\n" + "=" * 80)
    logger.info("📊 PRODUCTION VALIDATION SUMMARY")
    logger.info("=" * 80)
    
    total_tests = len(tester.test_results)
    passed_tests = sum(1 for result in tester.test_results.values() if result['success'])
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed Tests: {passed_tests}")
    logger.info(f"Success Rate: {success_rate:.1f}%")
    
    # Log individual test results
    for test_name, result in tester.test_results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        logger.info(f"  {status}: {test_name}")
    
    # Performance metrics summary
    logger.info("\n📈 Performance Metrics:")
    for metric_name, metric_data in tester.performance_metrics.items():
        logger.info(f"  {metric_name}: {metric_data['value']:.2f} {metric_data['unit']}")
    
    # Final assessment
    if success_rate >= 90:
        logger.info("\n🎉 PRODUCTION VALIDATION: ✅ PASSED")
        logger.info("   Application is ready for production deployment")
    elif success_rate >= 75:
        logger.info("\n⚠️ PRODUCTION VALIDATION: 🟡 PARTIAL PASS")
        logger.info("   Application has minor issues but core functionality works")
    else:
        logger.info("\n❌ PRODUCTION VALIDATION: ❌ FAILED")
        logger.info("   Critical issues found - not ready for production")
    
    return success_rate >= 75

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
