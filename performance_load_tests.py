#!/usr/bin/env python3
"""
Performance and Load Testing for FlipSync Production Validation
Real load testing without simulations
"""

import asyncio
import time
import requests
import logging
import sys
import statistics
import psutil
import threading
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import concurrent.futures

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PerformanceLoadTester:
    """Performance and load testing suite."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.test_results = {}
        self.performance_metrics = {}
        
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

    def test_sustained_load(self) -> bool:
        """Test sustained load over time."""
        logger.info("🔄 Testing Sustained Load (60 requests over 30 seconds)...")
        
        def make_request(request_id: int) -> Dict[str, Any]:
            start_time = time.time()
            try:
                response = requests.get(f"{self.base_url}/api/v1/agents/status", timeout=30)
                response_time = time.time() - start_time
                return {
                    'request_id': request_id,
                    'success': response.status_code == 200,
                    'response_time': response_time,
                    'status_code': response.status_code,
                    'timestamp': time.time()
                }
            except Exception as e:
                return {
                    'request_id': request_id,
                    'success': False,
                    'response_time': time.time() - start_time,
                    'error': str(e),
                    'timestamp': time.time()
                }
        
        # Run sustained load test
        start_time = time.time()
        results = []
        
        # Send requests at intervals over 30 seconds
        for i in range(60):
            result = make_request(i)
            results.append(result)
            
            # Wait 0.5 seconds between requests
            if i < 59:  # Don't wait after the last request
                time.sleep(0.5)
        
        total_time = time.time() - start_time
        successful_requests = sum(1 for r in results if r['success'])
        response_times = [r['response_time'] for r in results if r['success']]
        
        if response_times:
            avg_response_time = statistics.mean(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)
            p95_response_time = statistics.quantiles(response_times, n=20)[18]  # 95th percentile
        else:
            avg_response_time = max_response_time = min_response_time = p95_response_time = 0
        
        self.log_performance_metric("sustained_load_total_time", total_time)
        self.log_performance_metric("sustained_load_avg_response_time", avg_response_time)
        self.log_performance_metric("sustained_load_p95_response_time", p95_response_time)
        
        sustained_load_success = successful_requests >= 54  # 90% success rate
        self.log_test_result("sustained_load_test", sustained_load_success, {
            "total_requests": 60,
            "successful_requests": successful_requests,
            "success_rate": (successful_requests / 60) * 100,
            "avg_response_time": avg_response_time,
            "max_response_time": max_response_time,
            "min_response_time": min_response_time,
            "p95_response_time": p95_response_time,
            "total_duration": total_time
        })
        
        return sustained_load_success

    def test_concurrent_users(self) -> bool:
        """Test concurrent user simulation."""
        logger.info("🔄 Testing Concurrent Users (50 simultaneous requests)...")
        
        def simulate_user(user_id: int) -> Dict[str, Any]:
            start_time = time.time()
            try:
                # Simulate user workflow: check health, get agents, create conversation
                session = requests.Session()
                session.timeout = 30
                
                # Step 1: Health check
                health_response = session.get(f"{self.base_url}/health")
                
                # Step 2: Get agents status
                agents_response = session.get(f"{self.base_url}/api/v1/agents/status")
                
                # Step 3: Create conversation
                conversation_payload = {
                    "title": f"User {user_id} Test Conversation",
                    "agent_type": "general"
                }
                conversation_response = session.post(
                    f"{self.base_url}/api/v1/chat/conversations",
                    json=conversation_payload
                )
                
                total_time = time.time() - start_time
                
                success = (
                    health_response.status_code == 200 and
                    agents_response.status_code == 200 and
                    conversation_response.status_code == 200
                )
                
                return {
                    'user_id': user_id,
                    'success': success,
                    'total_time': total_time,
                    'health_status': health_response.status_code,
                    'agents_status': agents_response.status_code,
                    'conversation_status': conversation_response.status_code
                }
                
            except Exception as e:
                return {
                    'user_id': user_id,
                    'success': False,
                    'total_time': time.time() - start_time,
                    'error': str(e)
                }
        
        # Run concurrent user simulation
        start_time = time.time()
        with concurrent.futures.ThreadPoolExecutor(max_workers=25) as executor:
            futures = [executor.submit(simulate_user, i) for i in range(50)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        total_time = time.time() - start_time
        successful_users = sum(1 for r in results if r['success'])
        user_times = [r['total_time'] for r in results if r['success']]
        
        if user_times:
            avg_user_time = statistics.mean(user_times)
            max_user_time = max(user_times)
        else:
            avg_user_time = max_user_time = 0
        
        self.log_performance_metric("concurrent_users_total_time", total_time)
        self.log_performance_metric("concurrent_users_avg_time", avg_user_time)
        
        concurrent_success = successful_users >= 45  # 90% success rate
        self.log_test_result("concurrent_users_test", concurrent_success, {
            "total_users": 50,
            "successful_users": successful_users,
            "success_rate": (successful_users / 50) * 100,
            "avg_user_workflow_time": avg_user_time,
            "max_user_workflow_time": max_user_time,
            "total_test_duration": total_time
        })
        
        return concurrent_success

    def test_resource_utilization(self) -> bool:
        """Test resource utilization during load."""
        logger.info("🔄 Testing Resource Utilization...")
        
        try:
            # Get initial resource usage
            initial_cpu = psutil.cpu_percent(interval=1)
            initial_memory = psutil.virtual_memory().percent
            
            # Run load while monitoring resources
            def monitor_resources():
                cpu_readings = []
                memory_readings = []
                
                for _ in range(30):  # Monitor for 30 seconds
                    cpu_readings.append(psutil.cpu_percent(interval=1))
                    memory_readings.append(psutil.virtual_memory().percent)
                
                return cpu_readings, memory_readings
            
            def generate_load():
                # Generate load by making requests
                for i in range(30):
                    try:
                        requests.get(f"{self.base_url}/api/v1/agents/status", timeout=5)
                    except:
                        pass
                    time.sleep(1)
            
            # Start monitoring and load generation
            monitor_thread = threading.Thread(target=monitor_resources)
            load_thread = threading.Thread(target=generate_load)
            
            start_time = time.time()
            monitor_thread.start()
            load_thread.start()
            
            monitor_thread.join()
            load_thread.join()
            total_time = time.time() - start_time
            
            # Get final resource usage
            final_cpu = psutil.cpu_percent(interval=1)
            final_memory = psutil.virtual_memory().percent
            
            # Calculate resource usage metrics
            cpu_increase = final_cpu - initial_cpu
            memory_increase = final_memory - initial_memory
            
            self.log_performance_metric("cpu_usage_increase", cpu_increase, "percent")
            self.log_performance_metric("memory_usage_increase", memory_increase, "percent")
            
            # Resource utilization is acceptable if increases are reasonable
            resource_test_success = cpu_increase < 50 and memory_increase < 20  # Reasonable thresholds
            
            self.log_test_result("resource_utilization_test", resource_test_success, {
                "initial_cpu_percent": initial_cpu,
                "final_cpu_percent": final_cpu,
                "cpu_increase_percent": cpu_increase,
                "initial_memory_percent": initial_memory,
                "final_memory_percent": final_memory,
                "memory_increase_percent": memory_increase,
                "test_duration": total_time
            })
            
            return resource_test_success
            
        except Exception as e:
            self.log_test_result("resource_utilization_test", False, {"error": str(e)})
            return False

    def test_graceful_degradation(self) -> bool:
        """Test graceful degradation under extreme load."""
        logger.info("🔄 Testing Graceful Degradation...")
        
        try:
            # Test with very high concurrent load
            def stress_request(request_id: int) -> Dict[str, Any]:
                try:
                    start_time = time.time()
                    response = requests.get(f"{self.base_url}/health", timeout=10)
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
            
            # Generate extreme load (100 concurrent requests)
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(stress_request, i) for i in range(100)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            total_time = time.time() - start_time
            successful_requests = sum(1 for r in results if r['success'])
            
            # Under extreme load, we expect some degradation but not complete failure
            degradation_success = successful_requests >= 70  # 70% success rate under stress
            
            self.log_test_result("graceful_degradation_test", degradation_success, {
                "total_stress_requests": 100,
                "successful_requests": successful_requests,
                "success_rate_under_stress": (successful_requests / 100) * 100,
                "total_stress_test_time": total_time
            })
            
            return degradation_success
            
        except Exception as e:
            self.log_test_result("graceful_degradation_test", False, {"error": str(e)})
            return False

async def main():
    """Run performance and load tests."""
    logger.info("🚀 Starting Performance and Load Tests")
    logger.info("=" * 60)
    
    tester = PerformanceLoadTester()
    
    # Test 1: Sustained Load
    logger.info("\n📋 Test 1: Sustained Load Testing")
    sustained_result = tester.test_sustained_load()
    
    # Test 2: Concurrent Users
    logger.info("\n📋 Test 2: Concurrent Users Simulation")
    concurrent_result = tester.test_concurrent_users()
    
    # Test 3: Resource Utilization
    logger.info("\n📋 Test 3: Resource Utilization")
    resource_result = tester.test_resource_utilization()
    
    # Test 4: Graceful Degradation
    logger.info("\n📋 Test 4: Graceful Degradation")
    degradation_result = tester.test_graceful_degradation()
    
    # Generate Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 PERFORMANCE AND LOAD TEST SUMMARY")
    logger.info("=" * 60)
    
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
        logger.info("\n🎉 PERFORMANCE TESTING: ✅ PASSED")
        logger.info("   Application performance is production ready")
    elif success_rate >= 75:
        logger.info("\n⚠️ PERFORMANCE TESTING: 🟡 PARTIAL PASS")
        logger.info("   Performance has minor issues but acceptable for production")
    else:
        logger.info("\n❌ PERFORMANCE TESTING: ❌ FAILED")
        logger.info("   Critical performance issues found")
    
    return success_rate >= 75

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
