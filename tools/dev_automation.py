#!/usr/bin/env python3
"""
FlipSync Development Automation
Automates common development tasks for the sophisticated architecture
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

class DevAutomation:
    """Automation tools for FlipSync development"""
    
    def __init__(self):
        self.root_dir = Path(".")
        
    def run_linting(self):
        """Run comprehensive code linting"""
        print("🔍 Running comprehensive code linting...")
        
        commands = [
            ("Black formatting", ["black", "fs_agt_clean/"]),
            ("Import sorting", ["isort", "fs_agt_clean/"]),
            ("Flake8 style check", ["flake8", "fs_agt_clean/", "--max-line-length=88"]),
            ("MyPy type check", ["mypy", "fs_agt_clean/", "--ignore-missing-imports"]),
            ("Bandit security check", ["bandit", "-r", "fs_agt_clean/", "--skip=B101,B601"])
        ]
        
        results = []
        for name, cmd in commands:
            print(f"  Running {name}...")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    results.append(f"✅ {name}: PASSED")
                else:
                    results.append(f"❌ {name}: FAILED")
                    if result.stdout:
                        print(f"    Output: {result.stdout[:200]}...")
                    if result.stderr:
                        print(f"    Error: {result.stderr[:200]}...")
            except FileNotFoundError:
                results.append(f"⚠️  {name}: TOOL NOT FOUND")
        
        print("\n📊 Linting Results:")
        for result in results:
            print(f"  {result}")
        
        return results
    
    def validate_architecture(self):
        """Validate architecture preservation"""
        print("🏗️  Validating architecture preservation...")
        
        try:
            result = subprocess.run(
                ["python", "validate_architecture_preservation.py"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("✅ Architecture preservation validated")
                return True
            else:
                print("❌ Architecture preservation FAILED")
                print(result.stdout)
                return False
                
        except Exception as e:
            print(f"❌ Error validating architecture: {e}")
            return False
    
    def run_tests(self):
        """Run test suite"""
        print("🧪 Running test suite...")
        
        test_commands = [
            ("Python unit tests", ["python", "-m", "pytest", "fs_agt_clean/tests/", "-v"]),
            ("Agent tests", ["python", "-m", "pytest", "fs_agt_clean/agents/", "-k", "test_", "-v"]),
            ("Service tests", ["python", "-m", "pytest", "fs_agt_clean/services/", "-k", "test_", "-v"])
        ]
        
        results = []
        for name, cmd in test_commands:
            print(f"  Running {name}...")
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                if result.returncode == 0:
                    results.append(f"✅ {name}: PASSED")
                else:
                    results.append(f"❌ {name}: FAILED")
                    print(f"    Error output: {result.stdout[-300:]}")
            except FileNotFoundError:
                results.append(f"⚠️  {name}: PYTEST NOT FOUND")
        
        print("\n📊 Test Results:")
        for result in results:
            print(f"  {result}")
        
        return results
    
    def generate_docs(self):
        """Generate documentation"""
        print("📚 Generating documentation...")
        
        try:
            result = subprocess.run(
                ["python", "tools/doc_generator.py", "--generate"],
                capture_output=True, text=True
            )
            
            if result.returncode == 0:
                print("✅ Documentation generated successfully")
                print(result.stdout)
                return True
            else:
                print("❌ Documentation generation failed")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Error generating documentation: {e}")
            return False
    
    def check_dependencies(self):
        """Check development dependencies"""
        print("📦 Checking development dependencies...")
        
        required_tools = [
            "python3", "pip", "black", "isort", "flake8", "mypy", "bandit", "vulture"
        ]
        
        missing_tools = []
        for tool in required_tools:
            try:
                subprocess.run([tool, "--version"], capture_output=True, check=True)
                print(f"  ✅ {tool}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"  ❌ {tool}")
                missing_tools.append(tool)
        
        if missing_tools:
            print(f"\n⚠️  Missing tools: {', '.join(missing_tools)}")
            print("Run: pip install " + " ".join(missing_tools))
            return False
        else:
            print("\n✅ All development dependencies available")
            return True
    
    def full_check(self):
        """Run full development check"""
        print("🚀 Running full FlipSync development check...")
        print("=" * 60)
        
        checks = [
            ("Dependencies", self.check_dependencies),
            ("Architecture", self.validate_architecture),
            ("Linting", self.run_linting),
            ("Documentation", self.generate_docs),
            ("Tests", self.run_tests)
        ]
        
        results = []
        for name, check_func in checks:
            print(f"\n{name} Check:")
            print("-" * 20)
            success = check_func()
            results.append((name, success))
        
        print("\n" + "=" * 60)
        print("📊 FULL CHECK SUMMARY")
        print("=" * 60)
        
        all_passed = True
        for name, success in results:
            status = "✅ PASSED" if success else "❌ FAILED"
            print(f"{name:<15} {status}")
            if not success:
                all_passed = False
        
        print("\n" + "=" * 60)
        if all_passed:
            print("🎉 ALL CHECKS PASSED - FlipSync development environment ready!")
        else:
            print("⚠️  SOME CHECKS FAILED - Please review and fix issues")
        print("=" * 60)
        
        return all_passed
    
    def quick_setup(self):
        """Quick development environment setup"""
        print("⚡ Quick FlipSync development setup...")
        
        setup_commands = [
            ("Installing dev tools", ["pip", "install", "black", "isort", "flake8", "mypy", "bandit", "vulture"]),
            ("Setting up pre-commit", ["pre-commit", "install"]),
            ("Making tools executable", ["chmod", "+x", "tools/*.py"])
        ]
        
        for name, cmd in setup_commands:
            print(f"  {name}...")
            try:
                subprocess.run(cmd, check=True, capture_output=True)
                print(f"  ✅ {name} completed")
            except subprocess.CalledProcessError as e:
                print(f"  ❌ {name} failed: {e}")
            except FileNotFoundError:
                print(f"  ⚠️  {name} skipped (tool not found)")

def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(description="FlipSync Development Automation")
    parser.add_argument("--lint", action="store_true", help="Run code linting")
    parser.add_argument("--test", action="store_true", help="Run test suite")
    parser.add_argument("--docs", action="store_true", help="Generate documentation")
    parser.add_argument("--check", action="store_true", help="Run full development check")
    parser.add_argument("--setup", action="store_true", help="Quick development setup")
    parser.add_argument("--validate", action="store_true", help="Validate architecture")
    
    args = parser.parse_args()
    automation = DevAutomation()
    
    if args.lint:
        automation.run_linting()
    elif args.test:
        automation.run_tests()
    elif args.docs:
        automation.generate_docs()
    elif args.check:
        automation.full_check()
    elif args.setup:
        automation.quick_setup()
    elif args.validate:
        automation.validate_architecture()
    else:
        automation.full_check()

if __name__ == "__main__":
    main()
