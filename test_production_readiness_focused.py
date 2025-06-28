#!/usr/bin/env python3
"""
FlipSync Production Readiness Focused Validation
AGENT_CONTEXT: Validate working agent functionality for production deployment
AGENT_PRIORITY: Measure real agent performance, API response times, and business workflows
AGENT_PATTERN: Production validation, performance measurement, real functionality testing
"""

import asyncio
import sys
import time
import json
from datetime import datetime, timezone
from typing import Dict, Any, List

# Add project root to path
sys.path.insert(0, '/app')

class ProductionReadinessValidator:
    """Validates FlipSync's working agent functionality for production readiness."""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "test_suite": "Production Readiness Focused Validation",
            "infrastructure": {},
            "agent_functionality": {},
            "api_performance": {},
            "business_workflows": {},
            "production_readiness_score": 0
        }

    def log_result(self, category: str, test_name: str, success: bool, details: Dict[str, Any], metrics: Dict[str, float] = None):
        """Log test result with production metrics."""
        result = {
            "success": success,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "details": details,
            "metrics": metrics or {}
        }
        
        self.results[category][test_name] = result
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if metrics:
            for key, value in metrics.items():
                print(f"  📊 {key}: {value}")
        print()

    async def test_infrastructure_health(self) -> bool:
        """Test core infrastructure health."""
        print("🏗️ Testing Infrastructure Health...")
        
        try:
            # Test API health endpoint
            import requests
            start_time = time.time()
            response = requests.get("http://localhost:8000/health", timeout=5)
            api_response_time = (time.time() - start_time) * 1000
            
            api_healthy = response.status_code == 200
            
            # Test database connectivity
            import psycopg2
            start_time = time.time()
            conn = psycopg2.connect(
                host='flipsync-infrastructure-postgres',
                port=5432,
                user='postgres',
                password='postgres',
                database='flipsync'
            )
            conn.close()
            db_response_time = (time.time() - start_time) * 1000
            
            # Test Redis
            import redis
            start_time = time.time()
            r = redis.Redis(host='flipsync-infrastructure-redis', port=6379, db=0)
            r.ping()
            redis_response_time = (time.time() - start_time) * 1000
            
            metrics = {
                "api_response_time_ms": api_response_time,
                "db_response_time_ms": db_response_time,
                "redis_response_time_ms": redis_response_time,
                "api_healthy": api_healthy,
                "meets_1s_target": api_response_time < 1000
            }
            
            success = api_healthy and api_response_time < 1000 and db_response_time < 100
            
            self.log_result("infrastructure", "health_check", success, {
                "api_status": response.status_code,
                "database_connected": True,
                "redis_connected": True
            }, metrics)
            
            return success
            
        except Exception as e:
            self.log_result("infrastructure", "health_check", False, {"error": str(e)})
            return False

    async def test_working_agents(self) -> Dict[str, Any]:
        """Test the agents we know are working."""
        print("🤖 Testing Working Agent Functionality...")
        
        agent_results = {}
        
        # Test ExecutiveAgent
        try:
            from fs_agt_clean.agents.executive.executive_agent import ExecutiveAgent
            start_time = time.time()
            exec_agent = ExecutiveAgent(agent_id='prod_test_executive')
            init_time = (time.time() - start_time) * 1000
            
            # Test decision making
            start_time = time.time()
            decision = await exec_agent.make_decision('pricing_decision', {
                'product': 'iPhone 13',
                'current_price': 599.99,
                'competitor_prices': [579.99, 619.99, 589.99]
            })
            decision_time = (time.time() - start_time) * 1000
            
            agent_results["ExecutiveAgent"] = {
                "initialization_time_ms": init_time,
                "decision_time_ms": decision_time,
                "decision_result": decision.get("decision", "unknown"),
                "confidence": decision.get("confidence", 0),
                "functional": True
            }
            
        except Exception as e:
            agent_results["ExecutiveAgent"] = {"error": str(e), "functional": False}
        
        # Test ContentAgent
        try:
            from fs_agt_clean.agents.content.content_agent import ContentAgent
            start_time = time.time()
            content_agent = ContentAgent(agent_id='prod_test_content')
            init_time = (time.time() - start_time) * 1000
            
            # Test content generation
            start_time = time.time()
            content = await content_agent.generate_content({
                'product_name': 'iPhone 13 Pro',
                'category': 'Electronics',
                'marketplace': 'amazon'
            })
            generation_time = (time.time() - start_time) * 1000
            
            agent_results["ContentAgent"] = {
                "initialization_time_ms": init_time,
                "generation_time_ms": generation_time,
                "title_length": len(content.get("title", "")),
                "seo_score": content.get("seo_score", 0),
                "functional": True
            }
            
        except Exception as e:
            agent_results["ContentAgent"] = {"error": str(e), "functional": False}
        
        # Test MarketAgent
        try:
            from fs_agt_clean.agents.market.market_agent import MarketAgent
            start_time = time.time()
            market_agent = MarketAgent(agent_id='prod_test_market')
            init_time = (time.time() - start_time) * 1000
            
            # Test market analysis with real eBay data
            start_time = time.time()
            analysis = await market_agent.analyze_market('iPhone 13')
            analysis_time = (time.time() - start_time) * 1000
            
            agent_results["MarketAgent"] = {
                "initialization_time_ms": init_time,
                "analysis_time_ms": analysis_time,
                "listings_found": len(analysis.get("listings", [])),
                "competition_level": analysis.get("competition_level", "unknown"),
                "functional": True
            }
            
        except Exception as e:
            agent_results["MarketAgent"] = {"error": str(e), "functional": False}
        
        # Calculate metrics
        functional_agents = sum(1 for result in agent_results.values() if result.get("functional", False))
        total_agents = len(agent_results)
        avg_init_time = sum(result.get("initialization_time_ms", 0) for result in agent_results.values()) / max(total_agents, 1)
        
        metrics = {
            "functional_agents": functional_agents,
            "total_agents_tested": total_agents,
            "functionality_rate": functional_agents / max(total_agents, 1),
            "average_init_time_ms": avg_init_time,
            "meets_performance_target": avg_init_time < 1000
        }
        
        success = functional_agents >= 3 and avg_init_time < 1000
        
        self.log_result("agent_functionality", "working_agents", success, agent_results, metrics)
        
        return agent_results

    async def test_ebay_integration(self) -> bool:
        """Test real eBay sandbox integration."""
        print("🛒 Testing eBay Sandbox Integration...")
        
        try:
            from fs_agt_clean.agents.market.ebay_client import eBayClient
            import os
            
            # Test eBay client with real credentials
            start_time = time.time()
            client = eBayClient(
                client_id=os.environ.get('SB_EBAY_APP_ID'),
                client_secret=os.environ.get('SB_EBAY_CERT_ID')
            )
            
            # Test credential validation
            async with client:
                is_valid = await client.validate_credentials()
                
                # Test product search
                results = await client.search_products('iPhone', limit=5)
                
            integration_time = (time.time() - start_time) * 1000
            
            metrics = {
                "integration_time_ms": integration_time,
                "credentials_valid": is_valid,
                "search_results_count": len(results),
                "real_api_working": len(results) > 0,
                "meets_performance_target": integration_time < 5000
            }
            
            success = is_valid and len(results) > 0 and integration_time < 5000
            
            self.log_result("business_workflows", "ebay_integration", success, {
                "credentials_valid": is_valid,
                "sample_results": [r.title[:50] + "..." for r in results[:2]]
            }, metrics)
            
            return success
            
        except Exception as e:
            self.log_result("business_workflows", "ebay_integration", False, {"error": str(e)})
            return False

    async def test_end_to_end_workflow(self) -> bool:
        """Test complete business workflow."""
        print("🔄 Testing End-to-End Business Workflow...")
        
        try:
            # Initialize agents
            from fs_agt_clean.agents.market.market_agent import MarketAgent
            from fs_agt_clean.agents.content.content_agent import ContentAgent
            from fs_agt_clean.agents.executive.executive_agent import ExecutiveAgent
            
            start_time = time.time()
            
            # Step 1: Market Analysis
            market_agent = MarketAgent(agent_id='workflow_market')
            market_data = await market_agent.analyze_market('iPhone 13')
            
            # Step 2: Content Generation
            content_agent = ContentAgent(agent_id='workflow_content')
            content = await content_agent.generate_content({
                'product_name': 'iPhone 13',
                'category': 'Electronics',
                'marketplace': 'ebay'
            })
            
            # Step 3: Executive Decision
            exec_agent = ExecutiveAgent(agent_id='workflow_executive')
            decision = await exec_agent.make_decision('listing_optimization', {
                'market_data': market_data,
                'content': content
            })
            
            workflow_time = (time.time() - start_time) * 1000
            
            # Validate workflow results
            workflow_success = (
                len(market_data.get("listings", [])) > 0 and
                len(content.get("title", "")) > 0 and
                decision.get("decision") != "defer"
            )
            
            metrics = {
                "workflow_time_ms": workflow_time,
                "market_listings_found": len(market_data.get("listings", [])),
                "content_generated": len(content.get("title", "")) > 0,
                "decision_made": decision.get("decision") != "defer",
                "meets_performance_target": workflow_time < 10000
            }
            
            success = workflow_success and workflow_time < 10000
            
            self.log_result("business_workflows", "end_to_end_workflow", success, {
                "market_analysis": "completed",
                "content_generation": "completed", 
                "executive_decision": decision.get("decision", "unknown")
            }, metrics)
            
            return success
            
        except Exception as e:
            self.log_result("business_workflows", "end_to_end_workflow", False, {"error": str(e)})
            return False

    def calculate_production_readiness_score(self) -> float:
        """Calculate overall production readiness score."""
        score_components = {
            "infrastructure": 0,
            "agent_functionality": 0,
            "ebay_integration": 0,
            "business_workflows": 0
        }
        
        # Infrastructure (25 points)
        if self.results.get("infrastructure", {}).get("health_check", {}).get("success", False):
            score_components["infrastructure"] = 25
        else:
            score_components["infrastructure"] = 10
        
        # Agent Functionality (30 points)
        agent_metrics = self.results.get("agent_functionality", {}).get("working_agents", {}).get("metrics", {})
        functionality_rate = agent_metrics.get("functionality_rate", 0)
        performance_ok = agent_metrics.get("meets_performance_target", False)
        
        if functionality_rate >= 1.0 and performance_ok:
            score_components["agent_functionality"] = 30
        elif functionality_rate >= 0.8 and performance_ok:
            score_components["agent_functionality"] = 25
        elif functionality_rate >= 0.6:
            score_components["agent_functionality"] = 20
        else:
            score_components["agent_functionality"] = 10
        
        # eBay Integration (20 points)
        if self.results.get("business_workflows", {}).get("ebay_integration", {}).get("success", False):
            score_components["ebay_integration"] = 20
        else:
            score_components["ebay_integration"] = 5
        
        # Business Workflows (25 points)
        if self.results.get("business_workflows", {}).get("end_to_end_workflow", {}).get("success", False):
            score_components["business_workflows"] = 25
        else:
            score_components["business_workflows"] = 10
        
        total_score = sum(score_components.values())
        self.results["production_readiness_score"] = total_score
        self.results["score_breakdown"] = score_components
        
        return total_score

    async def run_production_validation(self) -> Dict[str, Any]:
        """Run complete production readiness validation."""
        print("🎯 FlipSync Production Readiness Focused Validation")
        print("=" * 80)
        print(f"Target: Validate working functionality for production deployment")
        print(f"Focus: Real agent performance, API response times, business workflows")
        print()
        
        # Run validation tests
        await self.test_infrastructure_health()
        await self.test_working_agents()
        await self.test_ebay_integration()
        await self.test_end_to_end_workflow()
        
        # Calculate production readiness score
        score = self.calculate_production_readiness_score()
        
        # Print summary
        print("=" * 80)
        print("📊 PRODUCTION READINESS SUMMARY")
        print("=" * 80)
        print(f"Production Readiness Score: {score}/100")
        
        breakdown = self.results.get("score_breakdown", {})
        print(f"Infrastructure: {breakdown.get('infrastructure', 0)}/25")
        print(f"Agent Functionality: {breakdown.get('agent_functionality', 0)}/30")
        print(f"eBay Integration: {breakdown.get('ebay_integration', 0)}/20")
        print(f"Business Workflows: {breakdown.get('business_workflows', 0)}/25")
        
        if score >= 85:
            print("🎉 FlipSync is READY for production deployment!")
        elif score >= 70:
            print("⚠️ FlipSync needs minor optimizations before production")
        else:
            print("❌ FlipSync requires significant work before production")
        
        return self.results


if __name__ == "__main__":
    validator = ProductionReadinessValidator()
    results = asyncio.run(validator.run_production_validation())
    
    # Save results for production readiness scorecard
    with open("/app/production_readiness_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    # Exit with appropriate code
    score = results.get("production_readiness_score", 0)
    sys.exit(0 if score >= 70 else 1)
