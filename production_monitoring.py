#!/usr/bin/env python3
"""
FlipSync Production Monitoring Script
Monitors key production metrics and alerts on issues.
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

import aiohttp
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ProductionMonitor:
    """Production monitoring for FlipSync API."""
    
    def __init__(self, api_base_url: str = "http://localhost:8001"):
        self.api_base_url = api_base_url
        self.alerts = []
        self.metrics_history = []
        
    async def check_api_health(self) -> Dict:
        """Check API health endpoint."""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{self.api_base_url}/api/v1/health") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "status": "healthy",
                            "response_time": response_time,
                            "data": data
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "response_time": response_time,
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "response_time": None,
                "error": str(e)
            }
    
    async def check_agents_status(self) -> Dict:
        """Check agent status."""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{self.api_base_url}/api/v1/agents/status") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        data = await response.json()
                        active_agents = sum(1 for agent in data.values() if agent.get("status") == "active")
                        return {
                            "status": "healthy",
                            "response_time": response_time,
                            "active_agents": active_agents,
                            "total_agents": len(data),
                            "data": data
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "response_time": response_time,
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "response_time": None,
                "error": str(e)
            }
    
    async def check_database_connectivity(self) -> Dict:
        """Check database connectivity via API."""
        try:
            async with aiohttp.ClientSession() as session:
                start_time = time.time()
                async with session.get(f"{self.api_base_url}/api/v1/chat/conversations") as response:
                    response_time = time.time() - start_time
                    
                    if response.status == 200:
                        return {
                            "status": "healthy",
                            "response_time": response_time
                        }
                    else:
                        return {
                            "status": "unhealthy",
                            "response_time": response_time,
                            "error": f"HTTP {response.status}"
                        }
        except Exception as e:
            return {
                "status": "error",
                "response_time": None,
                "error": str(e)
            }
    
    def check_system_resources(self) -> Dict:
        """Check system resource usage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "status": "healthy",
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3)
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def run_health_check(self) -> Dict:
        """Run comprehensive health check."""
        logger.info("Running production health check...")
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "api_health": await self.check_api_health(),
            "agents_status": await self.check_agents_status(),
            "database_connectivity": await self.check_database_connectivity(),
            "system_resources": self.check_system_resources()
        }
        
        # Check for alerts
        alerts = []
        
        # API response time alerts
        if results["api_health"].get("response_time", 0) > 2.0:
            alerts.append(f"API response time high: {results['api_health']['response_time']:.2f}s")
        
        # Agent status alerts
        agents_data = results["agents_status"]
        if agents_data.get("status") == "healthy":
            if agents_data.get("active_agents", 0) < agents_data.get("total_agents", 0):
                alerts.append(f"Some agents inactive: {agents_data['active_agents']}/{agents_data['total_agents']}")
        
        # System resource alerts
        sys_resources = results["system_resources"]
        if sys_resources.get("cpu_percent", 0) > 80:
            alerts.append(f"High CPU usage: {sys_resources['cpu_percent']:.1f}%")
        if sys_resources.get("memory_percent", 0) > 85:
            alerts.append(f"High memory usage: {sys_resources['memory_percent']:.1f}%")
        if sys_resources.get("disk_percent", 0) > 90:
            alerts.append(f"High disk usage: {sys_resources['disk_percent']:.1f}%")
        
        results["alerts"] = alerts
        results["overall_status"] = "healthy" if not alerts else "warning"
        
        # Store metrics
        self.metrics_history.append(results)
        if len(self.metrics_history) > 100:  # Keep last 100 checks
            self.metrics_history.pop(0)
        
        return results
    
    async def continuous_monitoring(self, interval: int = 60):
        """Run continuous monitoring."""
        logger.info(f"Starting continuous monitoring (interval: {interval}s)")
        
        while True:
            try:
                results = await self.run_health_check()
                
                # Log results
                status = results["overall_status"]
                if status == "healthy":
                    logger.info("✅ System healthy")
                else:
                    logger.warning(f"⚠️ System status: {status}")
                    for alert in results["alerts"]:
                        logger.warning(f"  - {alert}")
                
                # Log key metrics
                api_time = results["api_health"].get("response_time")
                if api_time:
                    logger.info(f"API response time: {api_time:.3f}s")
                
                agents = results["agents_status"]
                if agents.get("status") == "healthy":
                    logger.info(f"Agents: {agents['active_agents']}/{agents['total_agents']} active")
                
                sys_res = results["system_resources"]
                logger.info(f"Resources: CPU {sys_res.get('cpu_percent', 0):.1f}%, "
                           f"Memory {sys_res.get('memory_percent', 0):.1f}%")
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
            
            await asyncio.sleep(interval)

async def main():
    """Main monitoring function."""
    monitor = ProductionMonitor()
    
    # Run single health check
    print("=== FlipSync Production Health Check ===")
    results = await monitor.run_health_check()
    
    print(f"\nOverall Status: {results['overall_status'].upper()}")
    print(f"Timestamp: {results['timestamp']}")
    
    # API Health
    api = results["api_health"]
    print(f"\n🌐 API Health: {api['status']}")
    if api.get("response_time"):
        print(f"   Response Time: {api['response_time']:.3f}s")
    
    # Agents
    agents = results["agents_status"]
    print(f"\n🤖 Agents: {agents['status']}")
    if agents.get("active_agents") is not None:
        print(f"   Active: {agents['active_agents']}/{agents['total_agents']}")
    
    # Database
    db = results["database_connectivity"]
    print(f"\n💾 Database: {db['status']}")
    if db.get("response_time"):
        print(f"   Response Time: {db['response_time']:.3f}s")
    
    # System Resources
    sys_res = results["system_resources"]
    print(f"\n💻 System Resources: {sys_res['status']}")
    if sys_res.get("cpu_percent") is not None:
        print(f"   CPU: {sys_res['cpu_percent']:.1f}%")
        print(f"   Memory: {sys_res['memory_percent']:.1f}% ({sys_res['memory_available_gb']:.1f}GB available)")
        print(f"   Disk: {sys_res['disk_percent']:.1f}% ({sys_res['disk_free_gb']:.1f}GB free)")
    
    # Alerts
    if results["alerts"]:
        print(f"\n⚠️ Alerts:")
        for alert in results["alerts"]:
            print(f"   - {alert}")
    else:
        print(f"\n✅ No alerts")
    
    print("\n" + "="*50)

if __name__ == "__main__":
    asyncio.run(main())
