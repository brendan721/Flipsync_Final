#!/usr/bin/env python3
"""
Comprehensive Test Suite Runner for FlipSync Phase 1
AGENT_CONTEXT: Execute all validation tests and generate comprehensive report
AGENT_PRIORITY: Validate Phase 1 completion and readiness for Phase 2
AGENT_PATTERN: Test orchestration, comprehensive reporting, progress tracking
"""

import subprocess
import sys
import json
from datetime import datetime, timezone
from pathlib import Path

class FlipSyncTestRunner:
    """
    AGENT_CONTEXT: Comprehensive test runner for FlipSync validation
    AGENT_CAPABILITY: Test execution, result aggregation, progress reporting
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.results = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "phase": "Phase 1 - Core Validation",
            "test_suites": {},
            "summary": {},
            "recommendations": []
        }
    
    def run_test_suite(self, test_file, description):
        """Run a specific test suite and capture results"""
        print(f"\n🔄 Running {description}...")
        print("=" * 60)
        
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_file, "-v", "--tb=short"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Parse pytest output
            lines = result.stdout.split('\n')
            passed = 0
            failed = 0
            errors = 0
            
            for line in lines:
                if " PASSED " in line:
                    passed += 1
                elif " FAILED " in line:
                    failed += 1
                elif " ERROR " in line:
                    errors += 1
            
            # Extract summary line
            summary_line = ""
            for line in lines:
                if "passed" in line and ("failed" in line or "error" in line or line.strip().endswith("passed")):
                    summary_line = line.strip()
                    break
            
            self.results["test_suites"][test_file] = {
                "description": description,
                "return_code": result.returncode,
                "passed": passed,
                "failed": failed,
                "errors": errors,
                "summary": summary_line,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
            
            if result.returncode == 0:
                print(f"✅ {description}: {passed} tests passed")
            else:
                print(f"❌ {description}: {failed} failed, {errors} errors")
                
        except subprocess.TimeoutExpired:
            print(f"⏰ {description}: Timeout")
            self.results["test_suites"][test_file] = {
                "description": description,
                "error": "timeout"
            }
        except Exception as e:
            print(f"❌ {description}: Error - {e}")
            self.results["test_suites"][test_file] = {
                "description": description,
                "error": str(e)
            }
    
    def run_all_tests(self):
        """Run all test suites"""
        print("🎯 FlipSync Phase 1 Comprehensive Test Suite")
        print("=" * 80)
        print(f"Timestamp: {datetime.now(timezone.utc).isoformat()}")
        print(f"Project: FlipSync Multi-Agent E-commerce Platform")
        print(f"Phase: Phase 1 - Core Validation")
        
        # Define test suites
        test_suites = [
            ("test_core_functionality.py", "Core Functionality Validation"),
            ("test_authentication_validation.py", "Authentication System Validation"),
            ("test_api_validation.py", "API Endpoint Validation"),
            ("test_runner_validation.py", "Test Infrastructure Validation")
        ]
        
        # Run each test suite
        for test_file, description in test_suites:
            if (self.project_root / test_file).exists():
                self.run_test_suite(test_file, description)
            else:
                print(f"⚠️ {description}: Test file not found - {test_file}")
                self.results["test_suites"][test_file] = {
                    "description": description,
                    "error": "file_not_found"
                }
    
    def generate_summary(self):
        """Generate comprehensive test summary"""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        total_passed = 0
        total_failed = 0
        total_errors = 0
        successful_suites = 0
        total_suites = len(self.results["test_suites"])
        
        for test_file, result in self.results["test_suites"].items():
            if "error" not in result:
                total_passed += result.get("passed", 0)
                total_failed += result.get("failed", 0)
                total_errors += result.get("errors", 0)
                
                if result.get("return_code") == 0:
                    successful_suites += 1
        
        self.results["summary"] = {
            "total_test_suites": total_suites,
            "successful_suites": successful_suites,
            "total_tests_passed": total_passed,
            "total_tests_failed": total_failed,
            "total_errors": total_errors,
            "success_rate": (total_passed / (total_passed + total_failed + total_errors)) if (total_passed + total_failed + total_errors) > 0 else 0
        }
        
        # Print summary
        print(f"📈 Test Suites: {successful_suites}/{total_suites} successful")
        print(f"✅ Tests Passed: {total_passed}")
        print(f"❌ Tests Failed: {total_failed}")
        print(f"⚠️ Errors: {total_errors}")
        print(f"📊 Success Rate: {self.results['summary']['success_rate']:.1%}")
        
        # Detailed results
        print("\n📋 Detailed Results:")
        for test_file, result in self.results["test_suites"].items():
            if "error" in result:
                print(f"  ❌ {result['description']}: {result['error']}")
            else:
                status = "✅" if result.get("return_code") == 0 else "❌"
                print(f"  {status} {result['description']}: {result.get('summary', 'No summary')}")
    
    def generate_recommendations(self):
        """Generate recommendations based on test results"""
        print("\n💡 RECOMMENDATIONS")
        print("=" * 80)
        
        recommendations = []
        
        # Check overall success rate
        success_rate = self.results["summary"]["success_rate"]
        if success_rate >= 0.9:
            recommendations.append({
                "priority": "info",
                "category": "success",
                "message": f"Excellent test coverage with {success_rate:.1%} success rate"
            })
        elif success_rate >= 0.7:
            recommendations.append({
                "priority": "medium",
                "category": "improvement",
                "message": f"Good test coverage ({success_rate:.1%}) but some issues need attention"
            })
        else:
            recommendations.append({
                "priority": "high",
                "category": "critical",
                "message": f"Low test success rate ({success_rate:.1%}) - immediate attention required"
            })
        
        # Check for failed test suites
        failed_suites = [
            result["description"] for result in self.results["test_suites"].values()
            if result.get("return_code", 1) != 0 or "error" in result
        ]
        
        if failed_suites:
            recommendations.append({
                "priority": "high",
                "category": "failures",
                "message": f"Failed test suites need investigation: {', '.join(failed_suites)}"
            })
        
        # Phase 1 completion assessment
        if success_rate >= 0.8 and len(failed_suites) <= 1:
            recommendations.append({
                "priority": "info",
                "category": "phase_completion",
                "message": "Phase 1 (Core Validation) is ready for completion - proceed to Phase 2"
            })
        else:
            recommendations.append({
                "priority": "medium",
                "category": "phase_completion",
                "message": "Phase 1 needs additional work before proceeding to Phase 2"
            })
        
        self.results["recommendations"] = recommendations
        
        # Print recommendations
        for rec in recommendations:
            priority_icon = {"info": "ℹ️", "medium": "🟡", "high": "🔴"}.get(rec["priority"], "📝")
            print(f"  {priority_icon} {rec['category'].upper()}: {rec['message']}")
    
    def save_results(self):
        """Save comprehensive results to file"""
        results_file = self.project_root / "phase1_test_results.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Detailed results saved to: {results_file}")
    
    def run_comprehensive_validation(self):
        """Run complete validation process"""
        self.run_all_tests()
        self.generate_summary()
        self.generate_recommendations()
        self.save_results()
        
        print("\n" + "=" * 80)
        print("🎯 PHASE 1 VALIDATION COMPLETE")
        print("=" * 80)
        
        # Final status
        success_rate = self.results["summary"]["success_rate"]
        if success_rate >= 0.8:
            print("🎉 Phase 1 validation SUCCESSFUL - Ready for Phase 2!")
        else:
            print("⚠️ Phase 1 validation needs attention before proceeding")
        
        return self.results


if __name__ == "__main__":
    runner = FlipSyncTestRunner()
    results = runner.run_comprehensive_validation()
