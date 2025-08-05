"""
FlipSync Production Validation API Routes
Week 4: Production Deployment & Operational Excellence - Objective 5

API endpoints for controlling and monitoring production validation & go-live procedures.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from fs_agt_clean.core.validation.production_validation_system import (
    get_production_validation_system,
    ValidationStatus,
    ValidationSeverity
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/validation", tags=["Production Validation"])


class ValidationRequest(BaseModel):
    """Request model for validation operations."""
    action: str  # "initialize", "execute", "status", "report"
    test_categories: Optional[List[str]] = None
    include_revenue_validation: bool = True
    configuration: Optional[Dict[str, Any]] = None


class ValidationStatusResponse(BaseModel):
    """Response model for validation status."""
    validation_active: bool
    tests_registered: int
    tests_completed: int
    revenue_scenarios_tested: int
    overall_success_rate: float
    go_live_approved: bool


@router.get("/status", response_model=ValidationStatusResponse)
async def get_validation_status():
    """
    Get the current status of production validation system.
    
    Returns:
        ValidationStatusResponse: Current validation status
    """
    try:
        validation_system = get_production_validation_system()
        
        # Get validation status
        status_info = validation_system.get_validation_status()
        
        # Calculate success rate
        completed_tests = status_info["tests_completed"]
        if completed_tests > 0:
            passed_tests = sum(
                1 for test in validation_system.test_results
                if test.status == ValidationStatus.PASSED
            )
            success_rate = passed_tests / completed_tests
        else:
            success_rate = 0.0
        
        # Determine go-live approval (simplified check)
        go_live_approved = (
            completed_tests > 0 and
            success_rate >= 0.8 and
            status_info["revenue_scenarios_tested"] > 0
        )
        
        return ValidationStatusResponse(
            validation_active=status_info["validation_active"],
            tests_registered=status_info["tests_registered"],
            tests_completed=status_info["tests_completed"],
            revenue_scenarios_tested=status_info["revenue_scenarios_tested"],
            overall_success_rate=success_rate,
            go_live_approved=go_live_approved
        )
        
    except Exception as e:
        logger.error(f"Error getting validation status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation status: {str(e)}"
        )


@router.post("/initialize")
async def initialize_validation():
    """
    Initialize the production validation system.
    
    Returns:
        Dict: Initialization result
    """
    try:
        validation_system = get_production_validation_system()
        
        success = await validation_system.initialize()
        
        if success:
            return {
                "success": True,
                "message": "Production validation system initialized successfully",
                "validation_categories": list(validation_system.validation_categories.keys()),
                "total_tests": len(validation_system.validation_tests),
                "performance_targets": validation_system.performance_targets,
                "revenue_targets": validation_system.revenue_targets,
                "production_configuration": {
                    "database": f"{validation_system.validation_config['database_host']}:{validation_system.validation_config['database_port']}",
                    "backend": validation_system.validation_config["backend_url"],
                    "websocket": validation_system.validation_config["websocket_url"]
                }
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to initialize production validation system"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error initializing validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize validation: {str(e)}"
        )


@router.post("/execute")
async def execute_production_validation():
    """
    Execute comprehensive production validation and go-live procedures.
    
    Returns:
        Dict: Validation execution result
    """
    try:
        validation_system = get_production_validation_system()
        
        if validation_system.validation_active:
            return {
                "success": False,
                "message": "Validation is already running",
                "status": "running"
            }
        
        # Execute production validation
        logger.info("🚀 Starting production validation execution...")
        success, validation_report = await validation_system.execute_production_validation()
        
        if success:
            return {
                "success": True,
                "message": "Production validation completed successfully - READY FOR GO-LIVE",
                "go_live_status": "APPROVED",
                "validation_report": validation_report,
                "next_steps": [
                    "✅ All validation tests passed",
                    "✅ Revenue generation validated",
                    "✅ System ready for production deployment",
                    "🚀 Proceed with go-live procedures"
                ]
            }
        else:
            return {
                "success": False,
                "message": "Production validation failed - NOT READY FOR GO-LIVE",
                "go_live_status": "NOT_APPROVED",
                "validation_report": validation_report,
                "next_steps": [
                    "❌ Review failed validation tests",
                    "🔧 Address identified issues",
                    "🔄 Re-run validation after fixes",
                    "⏸️ Do not proceed with go-live"
                ]
            }
            
    except Exception as e:
        logger.error(f"Error executing production validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute production validation: {str(e)}"
        )


@router.get("/report")
async def get_validation_report():
    """
    Get comprehensive validation report.
    
    Returns:
        Dict: Detailed validation report
    """
    try:
        validation_system = get_production_validation_system()
        
        if not validation_system.test_results:
            return {
                "success": False,
                "message": "No validation results available. Execute validation first.",
                "report": None
            }
        
        # Generate current report
        validation_results = {}
        
        # Group test results by category
        for category in validation_system.validation_categories.keys():
            category_tests = [
                test for test in validation_system.test_results
                if test.test_category == category
            ]
            
            if category_tests:
                passed_tests = sum(1 for test in category_tests if test.status == ValidationStatus.PASSED)
                validation_results[category] = {
                    "tests_executed": len(category_tests),
                    "tests_passed": passed_tests,
                    "tests_failed": len(category_tests) - passed_tests,
                    "success_rate": passed_tests / len(category_tests),
                    "test_details": [
                        {
                            "test_name": test.test_name,
                            "status": test.status.value,
                            "execution_time_ms": test.execution_time_ms,
                            "severity": test.severity.value
                        }
                        for test in category_tests
                    ]
                }
        
        # Add revenue validation results
        if validation_system.revenue_validation_results:
            total_revenue = sum(r.revenue_generated for r in validation_system.revenue_validation_results)
            avg_margin = sum(r.profit_margin for r in validation_system.revenue_validation_results) / len(validation_system.revenue_validation_results)
            
            validation_results["revenue_validation"] = {
                "success": total_revenue >= validation_system.revenue_targets["daily_revenue_target"],
                "total_revenue_generated": total_revenue,
                "average_profit_margin": avg_margin,
                "scenarios_tested": len(validation_system.revenue_validation_results),
                "revenue_targets": validation_system.revenue_targets
            }
        
        # Generate final report
        report = await validation_system._generate_validation_report(validation_results)
        
        return {
            "success": True,
            "validation_report": report,
            "summary": {
                "go_live_status": report.get("go_live_status", "PENDING"),
                "overall_success": report["validation_summary"]["overall_success_rate"],
                "tests_passed": report["validation_summary"]["tests_passed"],
                "tests_failed": report["validation_summary"]["tests_failed"],
                "revenue_validation": validation_results.get("revenue_validation", {}).get("success", False)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting validation report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation report: {str(e)}"
        )


@router.get("/tests")
async def get_validation_tests():
    """
    Get list of all validation tests and their status.
    
    Returns:
        Dict: Validation tests information
    """
    try:
        validation_system = get_production_validation_system()
        
        # Group tests by category
        tests_by_category = {}
        for category in validation_system.validation_categories.keys():
            category_tests = [
                test for test in validation_system.validation_tests.values()
                if test.test_category == category
            ]
            
            tests_by_category[category] = [
                {
                    "test_id": test.test_id,
                    "test_name": test.test_name,
                    "description": test.description,
                    "severity": test.severity.value,
                    "status": test.status.value,
                    "execution_time_ms": test.execution_time_ms
                }
                for test in category_tests
            ]
        
        # Get execution status
        completed_tests = [test for test in validation_system.validation_tests.values() if test.status != ValidationStatus.PENDING]
        passed_tests = [test for test in completed_tests if test.status == ValidationStatus.PASSED]
        
        return {
            "success": True,
            "tests_by_category": tests_by_category,
            "test_summary": {
                "total_tests": len(validation_system.validation_tests),
                "completed_tests": len(completed_tests),
                "passed_tests": len(passed_tests),
                "failed_tests": len(completed_tests) - len(passed_tests),
                "pending_tests": len(validation_system.validation_tests) - len(completed_tests)
            },
            "validation_categories": list(validation_system.validation_categories.keys())
        }
        
    except Exception as e:
        logger.error(f"Error getting validation tests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get validation tests: {str(e)}"
        )


@router.get("/revenue-validation")
async def get_revenue_validation():
    """
    Get revenue generation validation results.
    
    Returns:
        Dict: Revenue validation information
    """
    try:
        validation_system = get_production_validation_system()
        
        if not validation_system.revenue_validation_results:
            return {
                "success": False,
                "message": "No revenue validation results available. Execute validation first.",
                "revenue_results": []
            }
        
        # Process revenue validation results
        revenue_results = []
        total_revenue = 0
        total_profit = 0
        
        for result in validation_system.revenue_validation_results:
            revenue_results.append({
                "test_scenario": result.test_scenario,
                "revenue_generated": result.revenue_generated,
                "profit_margin": result.profit_margin,
                "arbitrage_opportunities": result.arbitrage_opportunities,
                "success_rate": result.success_rate,
                "execution_time_ms": result.execution_time_ms,
                "validation_passed": result.validation_passed
            })
            
            if result.validation_passed:
                total_revenue += result.revenue_generated
                total_profit += result.revenue_generated * result.profit_margin
        
        # Calculate metrics
        avg_profit_margin = (
            sum(r.profit_margin for r in validation_system.revenue_validation_results) / 
            len(validation_system.revenue_validation_results)
        )
        
        scenarios_passed = sum(1 for r in validation_system.revenue_validation_results if r.validation_passed)
        success_rate = scenarios_passed / len(validation_system.revenue_validation_results)
        
        # Check against targets
        targets_met = {
            "daily_revenue": total_revenue >= validation_system.revenue_targets["daily_revenue_target"],
            "profit_margin": avg_profit_margin >= validation_system.revenue_targets["minimum_profit_margin"],
            "success_rate": success_rate >= validation_system.revenue_targets["success_rate"]
        }
        
        return {
            "success": True,
            "revenue_validation_summary": {
                "total_revenue_generated": total_revenue,
                "total_profit": total_profit,
                "average_profit_margin": avg_profit_margin,
                "scenarios_tested": len(validation_system.revenue_validation_results),
                "scenarios_passed": scenarios_passed,
                "overall_success_rate": success_rate,
                "targets_met": targets_met,
                "validation_passed": all(targets_met.values())
            },
            "revenue_targets": validation_system.revenue_targets,
            "scenario_results": revenue_results
        }
        
    except Exception as e:
        logger.error(f"Error getting revenue validation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get revenue validation: {str(e)}"
        )


@router.get("/go-live-status")
async def get_go_live_status():
    """
    Get go-live approval status and readiness assessment.
    
    Returns:
        Dict: Go-live status information
    """
    try:
        validation_system = get_production_validation_system()
        
        # Check validation completion
        if not validation_system.test_results:
            return {
                "success": False,
                "go_live_status": "NOT_READY",
                "message": "Production validation not executed",
                "readiness_assessment": {
                    "validation_completed": False,
                    "revenue_validated": False,
                    "performance_validated": False,
                    "infrastructure_validated": False
                }
            }
        
        # Assess readiness criteria
        total_tests = len(validation_system.test_results)
        passed_tests = sum(1 for test in validation_system.test_results if test.status == ValidationStatus.PASSED)
        success_rate = passed_tests / total_tests if total_tests > 0 else 0
        
        # Check critical categories
        critical_categories = ["infrastructure", "agents", "ebay_integration"]
        critical_tests_passed = True
        
        for category in critical_categories:
            category_tests = [test for test in validation_system.test_results if test.test_category == category]
            if category_tests:
                category_passed = sum(1 for test in category_tests if test.status == ValidationStatus.PASSED)
                category_rate = category_passed / len(category_tests)
                if category_rate < 0.9:  # 90% required for critical categories
                    critical_tests_passed = False
                    break
        
        # Check revenue validation
        revenue_validated = False
        if validation_system.revenue_validation_results:
            total_revenue = sum(r.revenue_generated for r in validation_system.revenue_validation_results)
            revenue_validated = total_revenue >= validation_system.revenue_targets["daily_revenue_target"]
        
        # Determine go-live status
        readiness_criteria = {
            "validation_completed": total_tests > 0,
            "overall_success_rate": success_rate >= 0.8,
            "critical_tests_passed": critical_tests_passed,
            "revenue_validated": revenue_validated,
            "performance_validated": success_rate >= 0.9,
            "infrastructure_validated": critical_tests_passed
        }
        
        go_live_approved = all(readiness_criteria.values())
        
        return {
            "success": True,
            "go_live_status": "APPROVED" if go_live_approved else "NOT_APPROVED",
            "go_live_approved": go_live_approved,
            "readiness_assessment": readiness_criteria,
            "validation_summary": {
                "total_tests": total_tests,
                "tests_passed": passed_tests,
                "overall_success_rate": success_rate,
                "revenue_scenarios_tested": len(validation_system.revenue_validation_results)
            },
            "next_steps": [
                "🚀 Proceed with production deployment" if go_live_approved else "🔧 Address validation failures",
                "📊 Monitor system performance" if go_live_approved else "🔄 Re-run validation after fixes",
                "💰 Begin revenue generation" if go_live_approved else "⏸️ Hold production deployment"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error getting go-live status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get go-live status: {str(e)}"
        )


@router.post("/test-validation")
async def test_validation_system():
    """
    Test the validation system with sample operations.
    
    Returns:
        Dict: Test results
    """
    try:
        validation_system = get_production_validation_system()
        
        # Initialize if not already done
        if not validation_system.validation_tests:
            await validation_system.initialize()
        
        # Execute a subset of validation tests for testing
        test_categories = ["infrastructure", "agents"]
        
        logger.info("🧪 Running validation system test...")
        
        # Simulate partial validation execution
        test_results = {}
        for category in test_categories:
            category_result = await validation_system._execute_category_tests(category)
            test_results[category] = category_result
        
        # Calculate test summary
        total_tests = sum(result["tests_executed"] for result in test_results.values())
        total_passed = sum(result["tests_passed"] for result in test_results.values())
        success_rate = total_passed / total_tests if total_tests > 0 else 0
        
        return {
            "success": True,
            "test_summary": {
                "validation_system_operational": True,
                "categories_tested": len(test_categories),
                "total_tests_executed": total_tests,
                "tests_passed": total_passed,
                "overall_success_rate": success_rate,
                "test_performance": "EXCELLENT" if success_rate >= 0.9 else "GOOD" if success_rate >= 0.8 else "NEEDS_IMPROVEMENT"
            },
            "category_results": test_results,
            "recommendations": [
                "✅ Validation system operational - ready for production validation" if success_rate >= 0.8
                else "⚠️ Some validation tests failed - review system configuration"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error testing validation system: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to test validation system: {str(e)}"
        )
