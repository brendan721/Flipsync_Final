#!/usr/bin/env python3
"""
FlipSync Frontend Integration Validator
Comprehensive validation of Flutter mobile and React testing frontend integration
with the production backend for Proxmox migration assessment.
"""

import json
import os
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import requests

# import websocket  # Optional dependency
from collections import defaultdict


class FrontendIntegrationValidator:
    """Comprehensive frontend integration validation tool."""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.backend_url = "http://174.138.77.110:8000"
        self.backend_ws_url = "ws://174.138.77.110:8000"
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "frontend_integration_validation",
            "base_path": str(self.base_path),
            "backend_url": self.backend_url,
            "summary": {},
            "detailed_findings": {},
        }

    def validate_integration(self) -> Dict:
        """Run comprehensive frontend integration validation."""
        print(f"🔍 Starting frontend integration validation")
        print(f"🎯 Backend URL: {self.backend_url}")

        # Validate backend connectivity first
        self._validate_backend_connectivity()

        # Analyze Flutter mobile frontend
        self._analyze_flutter_frontend()

        # Analyze React testing frontend
        self._analyze_react_frontend()

        # Test WebSocket connectivity
        self._test_websocket_connectivity()

        # Validate API integration
        self._validate_api_integration()

        # Generate integration assessment
        self._generate_integration_assessment()

        print("✅ Frontend integration validation completed")
        return self.results

    def _validate_backend_connectivity(self):
        """Validate backend API connectivity and performance."""
        print("🔌 Validating backend connectivity...")

        backend_tests = {
            "health": "/api/v1/health",
            "agents_4plus1": "/api/v1/agents/4plus1/",
            "decisions_4plus1": "/api/v1/decisions/4plus1/",
            "mobile_api": "/api/v1/mobile",
            "auth_status": "/api/v1/auth/status",
            "ebay_oauth": "/api/v1/ebay/oauth/authorize",
        }

        connectivity_results = {}

        for test_name, endpoint in backend_tests.items():
            try:
                start_time = time.time()
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=10)
                response_time = (time.time() - start_time) * 1000

                connectivity_results[test_name] = {
                    "status": "SUCCESS",
                    "status_code": response.status_code,
                    "response_time_ms": round(response_time, 2),
                    "response_size": len(response.content),
                    "meets_500ms_target": response_time < 500,
                }

                if response.status_code == 200:
                    try:
                        data = response.json()
                        connectivity_results[test_name]["has_json_response"] = True
                        connectivity_results[test_name]["response_keys"] = (
                            list(data.keys()) if isinstance(data, dict) else []
                        )
                    except:
                        connectivity_results[test_name]["has_json_response"] = False

            except Exception as e:
                connectivity_results[test_name] = {
                    "status": "FAILED",
                    "error": str(e),
                    "meets_500ms_target": False,
                }

        self.results["detailed_findings"]["backend_connectivity"] = connectivity_results

    def _analyze_flutter_frontend(self):
        """Analyze Flutter mobile frontend structure and integration."""
        print("📱 Analyzing Flutter mobile frontend...")

        flutter_path = self.base_path / "flipsync_mobile"
        flutter_findings = {
            "structure_analysis": {},
            "build_status": {},
            "dependency_analysis": {},
            "integration_points": {},
            "configuration_analysis": {},
        }

        if not flutter_path.exists():
            flutter_findings["error"] = "Flutter mobile directory not found"
            self.results["detailed_findings"]["flutter_frontend"] = flutter_findings
            return

        # Analyze Flutter project structure
        flutter_findings["structure_analysis"] = self._analyze_flutter_structure(
            flutter_path
        )

        # Check Flutter build status
        flutter_findings["build_status"] = self._check_flutter_build_status(
            flutter_path
        )

        # Analyze dependencies
        flutter_findings["dependency_analysis"] = self._analyze_flutter_dependencies(
            flutter_path
        )

        # Check integration points
        flutter_findings["integration_points"] = self._analyze_flutter_integration(
            flutter_path
        )

        self.results["detailed_findings"]["flutter_frontend"] = flutter_findings

    def _analyze_flutter_structure(self, flutter_path: Path) -> Dict:
        """Analyze Flutter project structure."""
        structure = {
            "has_pubspec": (flutter_path / "pubspec.yaml").exists(),
            "has_main_dart": (flutter_path / "lib" / "main.dart").exists(),
            "has_core_directory": (flutter_path / "lib" / "core").exists(),
            "has_presentation_directory": (
                flutter_path / "lib" / "presentation"
            ).exists(),
            "has_test_directory": (flutter_path / "test").exists(),
            "has_web_support": (flutter_path / "web").exists(),
            "has_android_support": (flutter_path / "android").exists(),
            "has_ios_support": (flutter_path / "ios").exists(),
        }

        # Count Dart files
        dart_files = list(flutter_path.rglob("*.dart"))
        structure["total_dart_files"] = len(dart_files)
        structure["lib_dart_files"] = len(list((flutter_path / "lib").rglob("*.dart")))
        structure["test_dart_files"] = len(
            list((flutter_path / "test").rglob("*.dart"))
        )

        return structure

    def _check_flutter_build_status(self, flutter_path: Path) -> Dict:
        """Check Flutter build status and compilation."""
        build_status = {}

        try:
            # Run flutter analyze
            result = subprocess.run(
                ["flutter", "analyze", "--no-pub"],
                cwd=flutter_path,
                capture_output=True,
                text=True,
                timeout=60,
            )

            build_status["analyze_exit_code"] = result.returncode
            build_status["analyze_output"] = result.stdout
            build_status["analyze_errors"] = result.stderr

            # Count issues
            if "issues found" in result.stdout:
                issues_line = [
                    line for line in result.stdout.split("\n") if "issues found" in line
                ]
                if issues_line:
                    issues_count = issues_line[0].split()[0]
                    build_status["total_issues"] = (
                        int(issues_count) if issues_count.isdigit() else 0
                    )

            # Check for compilation errors
            build_status["has_compilation_errors"] = "error •" in result.stdout
            build_status["compilation_ready"] = (
                result.returncode == 0 and not build_status["has_compilation_errors"]
            )

        except Exception as e:
            build_status["error"] = str(e)
            build_status["compilation_ready"] = False

        return build_status

    def _analyze_flutter_dependencies(self, flutter_path: Path) -> Dict:
        """Analyze Flutter dependencies and configuration."""
        deps_analysis = {}

        pubspec_path = flutter_path / "pubspec.yaml"
        if pubspec_path.exists():
            try:
                with open(pubspec_path, "r") as f:
                    pubspec_content = f.read()

                deps_analysis["has_pubspec"] = True
                deps_analysis["has_http_dependency"] = "http:" in pubspec_content
                deps_analysis["has_websocket_dependency"] = (
                    "web_socket_channel:" in pubspec_content
                )
                deps_analysis["has_dio_dependency"] = "dio:" in pubspec_content
                deps_analysis["has_bloc_dependency"] = (
                    "flutter_bloc:" in pubspec_content
                )

                # Count dependencies
                deps_section = False
                dep_count = 0
                for line in pubspec_content.split("\n"):
                    if line.strip() == "dependencies:":
                        deps_section = True
                    elif line.strip() == "dev_dependencies:":
                        deps_section = False
                    elif deps_section and line.strip() and not line.startswith(" "):
                        deps_section = False
                    elif deps_section and ":" in line:
                        dep_count += 1

                deps_analysis["dependency_count"] = dep_count

            except Exception as e:
                deps_analysis["pubspec_error"] = str(e)
        else:
            deps_analysis["has_pubspec"] = False

        return deps_analysis

    def _analyze_flutter_integration(self, flutter_path: Path) -> Dict:
        """Analyze Flutter backend integration points."""
        integration_points = {
            "api_service_files": [],
            "websocket_files": [],
            "auth_files": [],
            "backend_references": [],
        }

        # Find integration-related files
        for dart_file in (flutter_path / "lib").rglob("*.dart"):
            try:
                with open(dart_file, "r") as f:
                    content = f.read()

                # Check for API service patterns
                if any(
                    pattern in content.lower() for pattern in ["api", "http", "dio"]
                ):
                    integration_points["api_service_files"].append(
                        str(dart_file.relative_to(flutter_path))
                    )

                # Check for WebSocket patterns
                if any(
                    pattern in content.lower()
                    for pattern in ["websocket", "ws", "socket"]
                ):
                    integration_points["websocket_files"].append(
                        str(dart_file.relative_to(flutter_path))
                    )

                # Check for auth patterns
                if any(
                    pattern in content.lower() for pattern in ["auth", "token", "login"]
                ):
                    integration_points["auth_files"].append(
                        str(dart_file.relative_to(flutter_path))
                    )

                # Check for backend URL references
                if "174.138.77.110" in content or "flipsyncai.com" in content:
                    integration_points["backend_references"].append(
                        {
                            "file": str(dart_file.relative_to(flutter_path)),
                            "has_production_url": "174.138.77.110" in content
                            or "flipsyncai.com" in content,
                        }
                    )

            except Exception:
                continue

        return integration_points

    def _analyze_react_frontend(self):
        """Analyze React testing frontend structure and functionality."""
        print("⚛️ Analyzing React testing frontend...")

        react_path = self.base_path / "testing-frontend"
        react_findings = {
            "structure_analysis": {},
            "dependency_analysis": {},
            "test_coverage": {},
            "integration_points": {},
        }

        if not react_path.exists():
            react_findings["error"] = "React testing frontend directory not found"
            self.results["detailed_findings"]["react_frontend"] = react_findings
            return

        # Analyze React project structure
        react_findings["structure_analysis"] = self._analyze_react_structure(react_path)

        # Analyze dependencies
        react_findings["dependency_analysis"] = self._analyze_react_dependencies(
            react_path
        )

        # Analyze test coverage
        react_findings["test_coverage"] = self._analyze_react_test_coverage(react_path)

        # Check integration points
        react_findings["integration_points"] = self._analyze_react_integration(
            react_path
        )

        self.results["detailed_findings"]["react_frontend"] = react_findings

    def _analyze_react_structure(self, react_path: Path) -> Dict:
        """Analyze React project structure."""
        structure = {
            "has_package_json": (react_path / "package.json").exists(),
            "has_src_directory": (react_path / "src").exists(),
            "has_public_directory": (react_path / "public").exists(),
            "has_build_directory": (react_path / "build").exists(),
            "has_node_modules": (react_path / "node_modules").exists(),
        }

        # Count JavaScript/TypeScript files
        js_files = (
            list(react_path.rglob("*.js"))
            + list(react_path.rglob("*.jsx"))
            + list(react_path.rglob("*.ts"))
            + list(react_path.rglob("*.tsx"))
        )
        structure["total_js_files"] = len(js_files)

        # Count test files
        test_files = [f for f in js_files if "test" in str(f) or "spec" in str(f)]
        structure["test_files"] = len(test_files)

        return structure

    def _analyze_react_dependencies(self, react_path: Path) -> Dict:
        """Analyze React dependencies."""
        deps_analysis = {}

        package_json_path = react_path / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, "r") as f:
                    package_data = json.load(f)

                dependencies = package_data.get("dependencies", {})
                dev_dependencies = package_data.get("devDependencies", {})

                deps_analysis["total_dependencies"] = len(dependencies)
                deps_analysis["total_dev_dependencies"] = len(dev_dependencies)
                deps_analysis["has_react"] = "react" in dependencies
                deps_analysis["has_axios"] = "axios" in dependencies
                deps_analysis["has_websocket"] = any(
                    "socket" in dep for dep in dependencies.keys()
                )
                deps_analysis["has_testing_libs"] = any(
                    lib in dependencies or lib in dev_dependencies
                    for lib in ["jest", "testing-library", "cypress"]
                )

            except Exception as e:
                deps_analysis["package_json_error"] = str(e)
        else:
            deps_analysis["has_package_json"] = False

        return deps_analysis

    def _analyze_react_test_coverage(self, react_path: Path) -> Dict:
        """Analyze React test coverage and capabilities."""
        test_coverage = {
            "test_files": [],
            "api_test_files": [],
            "websocket_test_files": [],
            "oauth_test_files": [],
        }

        # Find test files
        for js_file in react_path.rglob("*.js"):
            if "test" in str(js_file) or "spec" in str(js_file):
                file_info = {
                    "file": str(js_file.relative_to(react_path)),
                    "size": js_file.stat().st_size,
                }

                try:
                    with open(js_file, "r") as f:
                        content = f.read()

                    file_info["has_api_tests"] = "api" in content.lower()
                    file_info["has_websocket_tests"] = (
                        "websocket" in content.lower() or "ws" in content.lower()
                    )
                    file_info["has_oauth_tests"] = "oauth" in content.lower()
                    file_info["has_backend_tests"] = (
                        "174.138.77.110" in content or "backend" in content.lower()
                    )

                    test_coverage["test_files"].append(file_info)

                    if file_info["has_api_tests"]:
                        test_coverage["api_test_files"].append(file_info["file"])
                    if file_info["has_websocket_tests"]:
                        test_coverage["websocket_test_files"].append(file_info["file"])
                    if file_info["has_oauth_tests"]:
                        test_coverage["oauth_test_files"].append(file_info["file"])

                except Exception:
                    continue

        return test_coverage

    def _analyze_react_integration(self, react_path: Path) -> Dict:
        """Analyze React backend integration points."""
        integration_points = {
            "api_configuration": {},
            "websocket_configuration": {},
            "auth_integration": {},
            "backend_references": [],
        }

        # Check main source files for integration patterns
        src_path = react_path / "src"
        if src_path.exists():
            for js_file in src_path.rglob("*.js"):
                try:
                    with open(js_file, "r") as f:
                        content = f.read()

                    # Check for backend URL configurations
                    if "174.138.77.110" in content or "flipsyncai.com" in content:
                        integration_points["backend_references"].append(
                            {
                                "file": str(js_file.relative_to(react_path)),
                                "has_production_url": True,
                            }
                        )

                    # Check for API service patterns
                    if "axios" in content or "fetch" in content:
                        if "api_configuration" not in integration_points:
                            integration_points["api_configuration"] = {}
                        integration_points["api_configuration"][
                            str(js_file.relative_to(react_path))
                        ] = {
                            "has_axios": "axios" in content,
                            "has_fetch": "fetch" in content,
                        }

                except Exception:
                    continue

        return integration_points

    def _test_websocket_connectivity(self):
        """Test WebSocket connectivity to backend."""
        print("🔌 Testing WebSocket connectivity...")

        websocket_tests = {
            "/ws/monitoring/test": "Monitoring WebSocket",
            "/ws/flipsync": "FlipSync WebSocket",
        }

        ws_results = {}

        for endpoint, description in websocket_tests.items():
            try:
                # Test WebSocket endpoint availability via HTTP upgrade request
                start_time = time.time()
                response = requests.get(
                    f"http://174.138.77.110:8000{endpoint}",
                    timeout=5,
                    headers={"Upgrade": "websocket", "Connection": "Upgrade"},
                )
                connection_time = (time.time() - start_time) * 1000

                # WebSocket endpoints typically return 426 (Upgrade Required) for HTTP requests
                ws_results[endpoint] = {
                    "status": (
                        "AVAILABLE" if response.status_code in [426, 101] else "UNKNOWN"
                    ),
                    "status_code": response.status_code,
                    "connection_time_ms": round(connection_time, 2),
                    "meets_100ms_target": connection_time < 100,
                    "description": description,
                    "websocket_ready": response.status_code == 426,
                }

            except Exception as e:
                ws_results[endpoint] = {
                    "status": "FAILED",
                    "error": str(e),
                    "meets_100ms_target": False,
                    "description": description,
                }

        self.results["detailed_findings"]["websocket_connectivity"] = ws_results

    def _validate_api_integration(self):
        """Validate API integration compatibility."""
        print("🔗 Validating API integration compatibility...")

        # Test key API endpoints that frontends should use
        api_integration_tests = {
            "4plus1_agents": "/api/v1/agents/4plus1/",
            "4plus1_decisions": "/api/v1/decisions/4plus1/",
            "mobile_dashboard": "/api/v1/mobile/dashboard",
            "auth_login": "/api/v1/auth/login",
            "ebay_status": "/api/v1/ebay/status",
        }

        integration_results = {}

        for test_name, endpoint in api_integration_tests.items():
            try:
                response = requests.get(f"{self.backend_url}{endpoint}", timeout=5)

                integration_results[test_name] = {
                    "status_code": response.status_code,
                    "frontend_compatible": response.status_code
                    in [200, 401, 403],  # 401/403 are expected for auth endpoints
                    "has_cors_headers": "Access-Control-Allow-Origin"
                    in response.headers,
                    "content_type": response.headers.get("Content-Type", ""),
                    "is_json": "application/json"
                    in response.headers.get("Content-Type", ""),
                }

            except Exception as e:
                integration_results[test_name] = {
                    "error": str(e),
                    "frontend_compatible": False,
                }

        self.results["detailed_findings"]["api_integration"] = integration_results

    def _generate_integration_assessment(self):
        """Generate comprehensive integration assessment."""
        print("📋 Generating integration assessment...")

        findings = self.results["detailed_findings"]

        assessment = {
            "overall_status": "UNKNOWN",
            "migration_readiness": {},
            "critical_issues": [],
            "recommendations": [],
            "performance_metrics": {},
            "compatibility_score": 0,
        }

        # Calculate compatibility score
        score = 0
        max_score = 100

        # Backend connectivity (40 points)
        if "backend_connectivity" in findings:
            backend_tests = findings["backend_connectivity"]
            successful_tests = sum(
                1 for test in backend_tests.values() if test.get("status") == "SUCCESS"
            )
            total_tests = len(backend_tests)
            if total_tests > 0:
                score += int((successful_tests / total_tests) * 40)

        # Flutter frontend (30 points)
        if "flutter_frontend" in findings:
            flutter = findings["flutter_frontend"]
            if flutter.get("build_status", {}).get("compilation_ready", False):
                score += 20
            if flutter.get("structure_analysis", {}).get("has_core_directory", False):
                score += 10

        # React frontend (30 points)
        if "react_frontend" in findings:
            react = findings["react_frontend"]
            if react.get("structure_analysis", {}).get("has_src_directory", False):
                score += 15
            if react.get("test_coverage", {}).get("test_files"):
                score += 15

        assessment["compatibility_score"] = score

        # Determine overall status
        if score >= 80:
            assessment["overall_status"] = "EXCELLENT"
        elif score >= 60:
            assessment["overall_status"] = "GOOD"
        elif score >= 40:
            assessment["overall_status"] = "FAIR"
        else:
            assessment["overall_status"] = "POOR"

        # Generate recommendations
        if score < 80:
            assessment["recommendations"].append("Address Flutter compilation errors")
        if "websocket_connectivity" in findings:
            ws_tests = findings["websocket_connectivity"]
            failed_ws = [
                ep
                for ep, result in ws_tests.items()
                if result.get("status") != "SUCCESS"
            ]
            if failed_ws:
                assessment["recommendations"].append(
                    f"Fix WebSocket connectivity for: {', '.join(failed_ws)}"
                )

        self.results["integration_assessment"] = assessment

    def save_results(self, filename: str = None) -> str:
        """Save validation results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"frontend_integration_validation_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"📄 Results saved to {filename}")
        return filename


def main():
    """Main execution function."""
    validator = FrontendIntegrationValidator()

    try:
        # Run validation
        results = validator.validate_integration()

        # Save results
        filename = validator.save_results()

        # Print summary
        print("\n" + "=" * 70)
        print("FLIPSYNC FRONTEND INTEGRATION VALIDATION SUMMARY")
        print("=" * 70)

        assessment = results.get("integration_assessment", {})
        print(f"Overall Status: {assessment.get('overall_status', 'UNKNOWN')}")
        print(f"Compatibility Score: {assessment.get('compatibility_score', 0)}/100")

        findings = results["detailed_findings"]

        # Backend connectivity summary
        if "backend_connectivity" in findings:
            backend_tests = findings["backend_connectivity"]
            successful = sum(
                1 for test in backend_tests.values() if test.get("status") == "SUCCESS"
            )
            print(
                f"\nBackend Connectivity: {successful}/{len(backend_tests)} endpoints working"
            )

        # Flutter frontend summary
        if "flutter_frontend" in findings:
            flutter = findings["flutter_frontend"]
            build_ready = flutter.get("build_status", {}).get(
                "compilation_ready", False
            )
            issues = flutter.get("build_status", {}).get("total_issues", 0)
            print(
                f"Flutter Frontend: {'✅ Ready' if build_ready else '❌ Issues'} ({issues} issues)"
            )

        # React frontend summary
        if "react_frontend" in findings:
            react = findings["react_frontend"]
            test_files = len(react.get("test_coverage", {}).get("test_files", []))
            print(f"React Testing Frontend: {test_files} test files found")

        # WebSocket connectivity summary
        if "websocket_connectivity" in findings:
            ws_tests = findings["websocket_connectivity"]
            successful_ws = sum(
                1 for test in ws_tests.values() if test.get("status") == "SUCCESS"
            )
            print(
                f"WebSocket Connectivity: {successful_ws}/{len(ws_tests)} endpoints working"
            )

        print("\n" + "=" * 70)
        print("Frontend integration validation completed!")
        print("=" * 70)

    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
