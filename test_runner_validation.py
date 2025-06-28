#!/usr/bin/env python3
"""
FlipSync Test Runner and Validation Script
AGENT_CONTEXT: Validate test infrastructure and run available tests
AGENT_PRIORITY: Ensure testing framework is operational and identify gaps
AGENT_PATTERN: Environment validation, dependency checking, test execution
"""

import os
import sys
import subprocess
import importlib
from pathlib import Path
import json
from datetime import datetime

# AGENT_INSTRUCTION: Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class FlipSyncTestValidator:
    """
    AGENT_CONTEXT: Comprehensive test validation for FlipSync
    AGENT_CAPABILITY: Environment check, dependency validation, test execution
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_dir = self.project_root / "fs_agt_clean" / "tests"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "environment": {},
            "dependencies": {},
            "test_files": {},
            "execution_results": {},
            "recommendations": []
        }
    
    def validate_environment(self):
        """Validate Python environment and basic setup"""
        print("🔍 Validating Environment...")
        
        # Python version
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.results["environment"]["python_version"] = python_version
        print(f"  ✅ Python version: {python_version}")
        
        # Project structure
        key_paths = {
            "project_root": self.project_root.exists(),
            "fs_agt_clean": (self.project_root / "fs_agt_clean").exists(),
            "tests_dir": self.test_dir.exists(),
            "requirements": (self.project_root / "requirements.txt").exists(),
            "pytest_config": (self.project_root / "pytest.ini").exists()
        }
        
        self.results["environment"]["paths"] = key_paths
        
        for path_name, exists in key_paths.items():
            status = "✅" if exists else "❌"
            print(f"  {status} {path_name}: {exists}")
    
    def check_dependencies(self):
        """Check for required dependencies"""
        print("\n📦 Checking Dependencies...")
        
        required_packages = [
            "pytest", "fastapi", "pydantic", "sqlalchemy", 
            "asyncpg", "uvicorn", "httpx", "python-jose"
        ]
        
        for package in required_packages:
            try:
                importlib.import_module(package.replace("-", "_"))
                self.results["dependencies"][package] = "available"
                print(f"  ✅ {package}: Available")
            except ImportError:
                self.results["dependencies"][package] = "missing"
                print(f"  ❌ {package}: Missing")
    
    def analyze_test_files(self):
        """Analyze test files and their structure"""
        print("\n📋 Analyzing Test Files...")
        
        if not self.test_dir.exists():
            print("  ❌ Tests directory not found")
            return
        
        test_files = list(self.test_dir.glob("test_*.py"))
        
        for test_file in test_files:
            file_info = {
                "path": str(test_file),
                "size": test_file.stat().st_size,
                "classes": [],
                "functions": [],
                "imports": []
            }
            
            try:
                with open(test_file, 'r') as f:
                    content = f.read()
                    
                # Count test classes and functions
                lines = content.split('\n')
                for line in lines:
                    line = line.strip()
                    if line.startswith('class Test'):
                        file_info["classes"].append(line.split('(')[0].replace('class ', ''))
                    elif line.startswith('def test_'):
                        file_info["functions"].append(line.split('(')[0].replace('def ', ''))
                    elif line.startswith('from ') or line.startswith('import '):
                        file_info["imports"].append(line)
                
                self.results["test_files"][test_file.name] = file_info
                print(f"  ✅ {test_file.name}: {len(file_info['classes'])} classes, {len(file_info['functions'])} functions")
                
            except Exception as e:
                print(f"  ❌ {test_file.name}: Error reading file - {e}")
                self.results["test_files"][test_file.name] = {"error": str(e)}
    
    def run_syntax_validation(self):
        """Validate Python syntax of test files"""
        print("\n🔧 Validating Test File Syntax...")
        
        test_files = list(self.test_dir.glob("test_*.py"))
        
        for test_file in test_files:
            try:
                with open(test_file, 'r') as f:
                    content = f.read()
                
                # Compile to check syntax
                compile(content, str(test_file), 'exec')
                print(f"  ✅ {test_file.name}: Syntax valid")
                
                if test_file.name in self.results["test_files"]:
                    self.results["test_files"][test_file.name]["syntax"] = "valid"
                
            except SyntaxError as e:
                print(f"  ❌ {test_file.name}: Syntax error - {e}")
                if test_file.name in self.results["test_files"]:
                    self.results["test_files"][test_file.name]["syntax"] = f"error: {e}"
            except Exception as e:
                print(f"  ⚠️  {test_file.name}: Other error - {e}")
    
    def attempt_test_execution(self):
        """Attempt to run tests with available tools"""
        print("\n🚀 Attempting Test Execution...")
        
        # Try different test execution methods
        execution_methods = [
            ("pytest", ["python3", "-m", "pytest", "--collect-only", "-q"]),
            ("unittest", ["python3", "-m", "unittest", "discover", "-s", "fs_agt_clean/tests", "-p", "test_*.py", "--verbose"]),
            ("direct", ["python3", "-c", "import sys; sys.path.append('.'); import fs_agt_clean.tests.test_auth_system"])
        ]
        
        for method_name, command in execution_methods:
            try:
                print(f"  🔄 Trying {method_name}...")
                
                if method_name == "pytest":
                    # Check if pytest is available
                    result = subprocess.run(
                        ["python3", "-c", "import pytest; print('pytest available')"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode != 0:
                        print(f"    ❌ pytest not available")
                        continue
                
                result = subprocess.run(
                    command, 
                    cwd=self.project_root,
                    capture_output=True, 
                    text=True, 
                    timeout=30
                )
                
                self.results["execution_results"][method_name] = {
                    "return_code": result.returncode,
                    "stdout": result.stdout[:500],  # Limit output
                    "stderr": result.stderr[:500]
                }
                
                if result.returncode == 0:
                    print(f"    ✅ {method_name}: Success")
                else:
                    print(f"    ❌ {method_name}: Failed (code {result.returncode})")
                    
            except subprocess.TimeoutExpired:
                print(f"    ⏰ {method_name}: Timeout")
                self.results["execution_results"][method_name] = {"error": "timeout"}
            except Exception as e:
                print(f"    ❌ {method_name}: Error - {e}")
                self.results["execution_results"][method_name] = {"error": str(e)}
    
    def generate_recommendations(self):
        """Generate recommendations based on validation results"""
        print("\n💡 Generating Recommendations...")
        
        recommendations = []
        
        # Check missing dependencies
        missing_deps = [pkg for pkg, status in self.results["dependencies"].items() if status == "missing"]
        if missing_deps:
            recommendations.append({
                "priority": "high",
                "category": "dependencies",
                "issue": f"Missing dependencies: {', '.join(missing_deps)}",
                "solution": f"Install missing packages: pip install {' '.join(missing_deps)}"
            })
        
        # Check test file issues
        test_files_with_errors = [
            name for name, info in self.results["test_files"].items() 
            if isinstance(info, dict) and ("error" in info or info.get("syntax") != "valid")
        ]
        if test_files_with_errors:
            recommendations.append({
                "priority": "medium",
                "category": "test_files",
                "issue": f"Test files with issues: {', '.join(test_files_with_errors)}",
                "solution": "Review and fix syntax errors in test files"
            })
        
        # Check execution results
        successful_methods = [
            method for method, result in self.results["execution_results"].items()
            if isinstance(result, dict) and result.get("return_code") == 0
        ]
        if not successful_methods:
            recommendations.append({
                "priority": "high",
                "category": "execution",
                "issue": "No test execution method succeeded",
                "solution": "Install pytest and required dependencies, then run: python3 -m pytest fs_agt_clean/tests/ -v"
            })
        
        self.results["recommendations"] = recommendations
        
        for rec in recommendations:
            priority_icon = "🔴" if rec["priority"] == "high" else "🟡"
            print(f"  {priority_icon} {rec['category'].upper()}: {rec['issue']}")
            print(f"    💡 Solution: {rec['solution']}")
    
    def save_results(self):
        """Save validation results to file"""
        results_file = self.project_root / "test_validation_results.json"
        
        with open(results_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        print(f"\n📄 Results saved to: {results_file}")
    
    def run_validation(self):
        """Run complete validation process"""
        print("🎯 FlipSync Test Infrastructure Validation")
        print("=" * 60)
        
        self.validate_environment()
        self.check_dependencies()
        self.analyze_test_files()
        self.run_syntax_validation()
        self.attempt_test_execution()
        self.generate_recommendations()
        self.save_results()
        
        print("\n" + "=" * 60)
        print("✅ Validation Complete!")
        
        # Summary
        total_tests = sum(
            len(info.get("functions", [])) 
            for info in self.results["test_files"].values() 
            if isinstance(info, dict) and "functions" in info
        )
        print(f"📊 Summary: {len(self.results['test_files'])} test files, {total_tests} test functions")


if __name__ == "__main__":
    # AGENT_CONTEXT: Standalone validation execution
    validator = FlipSyncTestValidator()
    validator.run_validation()
