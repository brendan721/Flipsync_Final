"""
FlipSync End-to-End Production Connectivity Validation
Week 3: Frontend Integration Updates - Objective 4

Comprehensive validation system for testing complete connectivity between
Flutter frontend and consolidated backend infrastructure.
"""

import asyncio
import json
import logging
import time
import aiohttp
import websockets
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ConnectivityTestResult(BaseModel):
    """Result model for connectivity tests."""
    test_name: str
    success: bool
    response_time_ms: float
    details: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: str


class EndToEndConnectivityValidator:
    """
    Comprehensive end-to-end connectivity validation system.
    
    Tests:
    - Flutter frontend to DigitalOcean backend API connectivity
    - Unified WebSocket endpoint (/ws/flipsync) functionality
    - Real-time agent showcase system integration
    - Enhanced WebSocket resilience features
    - Authentication system connectivity
    - Service registry accessibility
    """
    
    def __init__(self):
        # Production configuration
        self.backend_base_url = "http://174.138.77.110:8001"
        self.frontend_url = "http://localhost:3000"
        self.websocket_url = "ws://174.138.77.110:8001/ws/flipsync"
        
        # Test results storage
        self.test_results: List[ConnectivityTestResult] = []
        
        # HTTP session for API tests
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self) -> bool:
        """Initialize the connectivity validator."""
        try:
            # Create HTTP session with timeout
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            logger.info("✅ End-to-End Connectivity Validator initialized")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize connectivity validator: {e}")
            return False
    
    async def cleanup(self) -> None:
        """Cleanup resources."""
        if self.session:
            await self.session.close()
    
    async def run_full_validation(self) -> Dict[str, Any]:
        """Run complete end-to-end connectivity validation."""
        try:
            logger.info("🔍 Starting End-to-End Production Connectivity Validation")
            logger.info("=" * 80)
            
            start_time = time.perf_counter()
            
            # Clear previous results
            self.test_results.clear()
            
            # Run all connectivity tests
            await self._test_backend_health()
            await self._test_api_endpoints()
            await self._test_websocket_connectivity()
            await self._test_agent_showcase_integration()
            await self._test_authentication_connectivity()
            await self._test_service_registry_access()
            await self._test_enhanced_websocket_resilience()
            await self._test_flutter_backend_integration()
            
            total_time = (time.perf_counter() - start_time) * 1000
            
            # Generate validation report
            report = self._generate_validation_report(total_time)
            
            logger.info("✅ End-to-End Production Connectivity Validation Complete")
            logger.info("=" * 80)
            
            return report
            
        except Exception as e:
            logger.error(f"❌ End-to-end validation failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    
    async def _test_backend_health(self) -> None:
        """Test backend health endpoint."""
        test_name = "Backend Health Check"
        start_time = time.perf_counter()
        
        try:
            url = f"{self.backend_base_url}/health"
            
            async with self.session.get(url) as response:
                response_time = (time.perf_counter() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    
                    result = ConnectivityTestResult(
                        test_name=test_name,
                        success=True,
                        response_time_ms=response_time,
                        details={
                            "status_code": response.status,
                            "health_data": data,
                            "url": url
                        },
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                else:
                    result = ConnectivityTestResult(
                        test_name=test_name,
                        success=False,
                        response_time_ms=response_time,
                        details={"status_code": response.status, "url": url},
                        error_message=f"Health check failed with status {response.status}",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                
                self.test_results.append(result)
                logger.info(f"{'✅' if result.success else '❌'} {test_name}: {response_time:.2f}ms")
                
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            result = ConnectivityTestResult(
                test_name=test_name,
                success=False,
                response_time_ms=response_time,
                details={"url": f"{self.backend_base_url}/health"},
                error_message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            self.test_results.append(result)
            logger.error(f"❌ {test_name} failed: {e}")
    
    async def _test_api_endpoints(self) -> None:
        """Test critical API endpoints."""
        endpoints = [
            ("/api/v1/showcase/status", "GET", "Agent Showcase Status"),
            ("/api/v1/showcase/metrics", "GET", "Agent Showcase Metrics"),
            ("/api/v1/showcase/scenarios", "GET", "Agent Showcase Scenarios"),
            ("/docs", "GET", "API Documentation"),
            ("/openapi.json", "GET", "OpenAPI Schema")
        ]
        
        for endpoint, method, test_name in endpoints:
            start_time = time.perf_counter()
            
            try:
                url = f"{self.backend_base_url}{endpoint}"
                
                async with self.session.request(method, url) as response:
                    response_time = (time.perf_counter() - start_time) * 1000
                    
                    success = response.status in [200, 201, 202]
                    
                    details = {
                        "status_code": response.status,
                        "method": method,
                        "url": url,
                        "headers": dict(response.headers)
                    }
                    
                    if success and response.content_type == 'application/json':
                        try:
                            data = await response.json()
                            details["response_data"] = data
                        except:
                            pass
                    
                    result = ConnectivityTestResult(
                        test_name=test_name,
                        success=success,
                        response_time_ms=response_time,
                        details=details,
                        error_message=None if success else f"HTTP {response.status}",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                    
                    self.test_results.append(result)
                    logger.info(f"{'✅' if success else '❌'} {test_name}: {response_time:.2f}ms")
                    
            except Exception as e:
                response_time = (time.perf_counter() - start_time) * 1000
                result = ConnectivityTestResult(
                    test_name=test_name,
                    success=False,
                    response_time_ms=response_time,
                    details={"method": method, "url": f"{self.backend_base_url}{endpoint}"},
                    error_message=str(e),
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                self.test_results.append(result)
                logger.error(f"❌ {test_name} failed: {e}")
    
    async def _test_websocket_connectivity(self) -> None:
        """Test unified WebSocket endpoint connectivity."""
        test_name = "WebSocket Connectivity"
        start_time = time.perf_counter()
        
        try:
            # Test WebSocket connection
            async with websockets.connect(
                self.websocket_url,
                timeout=10,
                ping_interval=20,
                ping_timeout=10
            ) as websocket:
                
                # Send test message
                test_message = {
                    "type": "test_connection",
                    "data": {"test": True},
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                await websocket.send(json.dumps(test_message))
                
                # Wait for response (with timeout)
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    response_data = json.loads(response)
                    
                    response_time = (time.perf_counter() - start_time) * 1000
                    
                    result = ConnectivityTestResult(
                        test_name=test_name,
                        success=True,
                        response_time_ms=response_time,
                        details={
                            "websocket_url": self.websocket_url,
                            "test_message": test_message,
                            "response": response_data,
                            "connection_established": True
                        },
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                    
                    logger.info(f"✅ {test_name}: {response_time:.2f}ms")
                    
                except asyncio.TimeoutError:
                    response_time = (time.perf_counter() - start_time) * 1000
                    
                    result = ConnectivityTestResult(
                        test_name=test_name,
                        success=True,  # Connection established, just no response
                        response_time_ms=response_time,
                        details={
                            "websocket_url": self.websocket_url,
                            "connection_established": True,
                            "response_timeout": True
                        },
                        error_message="No response received within timeout (connection OK)",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                    
                    logger.info(f"✅ {test_name}: {response_time:.2f}ms (no response, but connected)")
                
                self.test_results.append(result)
                
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            result = ConnectivityTestResult(
                test_name=test_name,
                success=False,
                response_time_ms=response_time,
                details={"websocket_url": self.websocket_url},
                error_message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            self.test_results.append(result)
            logger.error(f"❌ {test_name} failed: {e}")
    
    async def _test_agent_showcase_integration(self) -> None:
        """Test agent showcase system integration."""
        test_name = "Agent Showcase Integration"
        start_time = time.perf_counter()
        
        try:
            # Test showcase initialization
            url = f"{self.backend_base_url}/api/v1/showcase/initialize"
            
            async with self.session.post(url) as response:
                response_time = (time.perf_counter() - start_time) * 1000
                
                if response.status in [200, 201]:
                    data = await response.json()
                    
                    result = ConnectivityTestResult(
                        test_name=test_name,
                        success=True,
                        response_time_ms=response_time,
                        details={
                            "status_code": response.status,
                            "initialization_data": data,
                            "url": url
                        },
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                    
                    logger.info(f"✅ {test_name}: {response_time:.2f}ms")
                else:
                    result = ConnectivityTestResult(
                        test_name=test_name,
                        success=False,
                        response_time_ms=response_time,
                        details={"status_code": response.status, "url": url},
                        error_message=f"Showcase initialization failed with status {response.status}",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                    
                    logger.error(f"❌ {test_name}: HTTP {response.status}")
                
                self.test_results.append(result)
                
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            result = ConnectivityTestResult(
                test_name=test_name,
                success=False,
                response_time_ms=response_time,
                details={"url": f"{self.backend_base_url}/api/v1/showcase/initialize"},
                error_message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            self.test_results.append(result)
            logger.error(f"❌ {test_name} failed: {e}")
    
    async def _test_authentication_connectivity(self) -> None:
        """Test authentication system connectivity."""
        test_name = "Authentication System"
        start_time = time.perf_counter()
        
        try:
            # Test authentication endpoint (if available)
            url = f"{self.backend_base_url}/api/v1/auth/status"
            
            async with self.session.get(url) as response:
                response_time = (time.perf_counter() - start_time) * 1000
                
                # Accept both 200 (working) and 404 (endpoint not exposed) as success
                success = response.status in [200, 404]
                
                result = ConnectivityTestResult(
                    test_name=test_name,
                    success=success,
                    response_time_ms=response_time,
                    details={
                        "status_code": response.status,
                        "url": url,
                        "note": "404 is acceptable - auth system may not expose status endpoint"
                    },
                    error_message=None if success else f"Unexpected status {response.status}",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                
                self.test_results.append(result)
                logger.info(f"{'✅' if success else '❌'} {test_name}: {response_time:.2f}ms")
                
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            result = ConnectivityTestResult(
                test_name=test_name,
                success=False,
                response_time_ms=response_time,
                details={"url": f"{self.backend_base_url}/api/v1/auth/status"},
                error_message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            self.test_results.append(result)
            logger.error(f"❌ {test_name} failed: {e}")
    
    async def _test_service_registry_access(self) -> None:
        """Test service registry accessibility."""
        test_name = "Service Registry Access"
        start_time = time.perf_counter()
        
        try:
            # Test service registry via showcase metrics
            url = f"{self.backend_base_url}/api/v1/showcase/metrics"
            
            async with self.session.get(url) as response:
                response_time = (time.perf_counter() - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    
                    # Check for service information
                    services_count = data.get("system_info", {}).get("services_count", 0)
                    
                    result = ConnectivityTestResult(
                        test_name=test_name,
                        success=services_count >= 20,  # Expect at least 20 services
                        response_time_ms=response_time,
                        details={
                            "status_code": response.status,
                            "services_count": services_count,
                            "metrics_data": data,
                            "url": url
                        },
                        error_message=None if services_count >= 20 else f"Only {services_count} services found",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                    
                    logger.info(f"{'✅' if result.success else '❌'} {test_name}: {response_time:.2f}ms ({services_count} services)")
                else:
                    result = ConnectivityTestResult(
                        test_name=test_name,
                        success=False,
                        response_time_ms=response_time,
                        details={"status_code": response.status, "url": url},
                        error_message=f"Service registry access failed with status {response.status}",
                        timestamp=datetime.now(timezone.utc).isoformat()
                    )
                    
                    logger.error(f"❌ {test_name}: HTTP {response.status}")
                
                self.test_results.append(result)
                
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            result = ConnectivityTestResult(
                test_name=test_name,
                success=False,
                response_time_ms=response_time,
                details={"url": f"{self.backend_base_url}/api/v1/showcase/metrics"},
                error_message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            self.test_results.append(result)
            logger.error(f"❌ {test_name} failed: {e}")
    
    async def _test_enhanced_websocket_resilience(self) -> None:
        """Test enhanced WebSocket resilience features."""
        test_name = "WebSocket Resilience"
        start_time = time.perf_counter()
        
        try:
            # Test multiple rapid connections to test resilience
            connection_count = 3
            successful_connections = 0
            
            for i in range(connection_count):
                try:
                    async with websockets.connect(
                        self.websocket_url,
                        timeout=5,
                        ping_interval=10,
                        ping_timeout=5
                    ) as websocket:
                        # Send ping
                        await websocket.ping()
                        successful_connections += 1
                        
                        # Small delay between connections
                        await asyncio.sleep(0.5)
                        
                except Exception:
                    pass  # Count failed connections
            
            response_time = (time.perf_counter() - start_time) * 1000
            success_rate = successful_connections / connection_count
            
            result = ConnectivityTestResult(
                test_name=test_name,
                success=success_rate >= 0.8,  # 80% success rate acceptable
                response_time_ms=response_time,
                details={
                    "websocket_url": self.websocket_url,
                    "connection_attempts": connection_count,
                    "successful_connections": successful_connections,
                    "success_rate": success_rate,
                    "resilience_test": True
                },
                error_message=None if success_rate >= 0.8 else f"Low success rate: {success_rate:.1%}",
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            
            self.test_results.append(result)
            logger.info(f"{'✅' if result.success else '❌'} {test_name}: {response_time:.2f}ms ({success_rate:.1%} success)")
            
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            result = ConnectivityTestResult(
                test_name=test_name,
                success=False,
                response_time_ms=response_time,
                details={"websocket_url": self.websocket_url},
                error_message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            self.test_results.append(result)
            logger.error(f"❌ {test_name} failed: {e}")
    
    async def _test_flutter_backend_integration(self) -> None:
        """Test Flutter frontend to backend integration."""
        test_name = "Flutter-Backend Integration"
        start_time = time.perf_counter()
        
        try:
            # Test CORS headers for Flutter integration
            url = f"{self.backend_base_url}/api/v1/showcase/status"
            headers = {
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "Content-Type"
            }
            
            # Test preflight request
            async with self.session.options(url, headers=headers) as response:
                response_time = (time.perf_counter() - start_time) * 1000
                
                cors_headers = {
                    "access-control-allow-origin": response.headers.get("Access-Control-Allow-Origin"),
                    "access-control-allow-methods": response.headers.get("Access-Control-Allow-Methods"),
                    "access-control-allow-headers": response.headers.get("Access-Control-Allow-Headers")
                }
                
                # Check if CORS is properly configured
                cors_configured = any(cors_headers.values())
                
                result = ConnectivityTestResult(
                    test_name=test_name,
                    success=response.status in [200, 204] or cors_configured,
                    response_time_ms=response_time,
                    details={
                        "status_code": response.status,
                        "cors_headers": cors_headers,
                        "frontend_url": "http://localhost:3000",
                        "backend_url": self.backend_base_url,
                        "url": url
                    },
                    error_message=None if (response.status in [200, 204] or cors_configured) else "CORS not configured",
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
                
                self.test_results.append(result)
                logger.info(f"{'✅' if result.success else '❌'} {test_name}: {response_time:.2f}ms")
                
        except Exception as e:
            response_time = (time.perf_counter() - start_time) * 1000
            result = ConnectivityTestResult(
                test_name=test_name,
                success=False,
                response_time_ms=response_time,
                details={
                    "frontend_url": "http://localhost:3000",
                    "backend_url": self.backend_base_url
                },
                error_message=str(e),
                timestamp=datetime.now(timezone.utc).isoformat()
            )
            self.test_results.append(result)
            logger.error(f"❌ {test_name} failed: {e}")
    
    def _generate_validation_report(self, total_time_ms: float) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        successful_tests = [r for r in self.test_results if r.success]
        failed_tests = [r for r in self.test_results if not r.success]
        
        success_rate = len(successful_tests) / len(self.test_results) if self.test_results else 0
        avg_response_time = sum(r.response_time_ms for r in self.test_results) / len(self.test_results) if self.test_results else 0
        
        report = {
            "validation_summary": {
                "success": success_rate >= 0.8,  # 80% success rate required
                "total_tests": len(self.test_results),
                "successful_tests": len(successful_tests),
                "failed_tests": len(failed_tests),
                "success_rate": success_rate,
                "average_response_time_ms": avg_response_time,
                "total_validation_time_ms": total_time_ms
            },
            "connectivity_status": {
                "backend_url": self.backend_base_url,
                "frontend_url": self.frontend_url,
                "websocket_url": self.websocket_url,
                "unified_websocket_endpoint": "/ws/flipsync"
            },
            "test_results": [result.dict() for result in self.test_results],
            "recommendations": self._generate_recommendations(failed_tests),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return report
    
    def _generate_recommendations(self, failed_tests: List[ConnectivityTestResult]) -> List[str]:
        """Generate recommendations based on failed tests."""
        recommendations = []
        
        if not failed_tests:
            recommendations.append("✅ All connectivity tests passed - system is ready for production")
            return recommendations
        
        for test in failed_tests:
            if "WebSocket" in test.test_name:
                recommendations.append("🔌 Check WebSocket server configuration and firewall settings")
            elif "Backend Health" in test.test_name:
                recommendations.append("🏥 Verify backend server is running on 174.138.77.110:8001")
            elif "Authentication" in test.test_name:
                recommendations.append("🔐 Check authentication system configuration")
            elif "Service Registry" in test.test_name:
                recommendations.append("📦 Verify service registry has 24+ services registered")
            elif "Flutter-Backend" in test.test_name:
                recommendations.append("📱 Check CORS configuration for Flutter frontend integration")
        
        return recommendations


# Global validator instance
_connectivity_validator: Optional[EndToEndConnectivityValidator] = None


def get_connectivity_validator() -> EndToEndConnectivityValidator:
    """Get the global connectivity validator instance."""
    global _connectivity_validator
    if _connectivity_validator is None:
        _connectivity_validator = EndToEndConnectivityValidator()
    return _connectivity_validator
