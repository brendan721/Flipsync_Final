#!/usr/bin/env python3
"""
FlipSync Redundancy Detection Tool
Comprehensive analysis of duplicate code, redundant configurations, and overlapping functionality
across the fs_agt_clean/ directory for Proxmox migration preparation.
"""

import ast
import hashlib
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

import json


class RedundancyDetector:
    """Comprehensive redundancy detection and analysis tool."""

    def __init__(self, base_path: str = "fs_agt_clean"):
        self.base_path = Path(base_path)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "redundancy_detection",
            "base_path": str(self.base_path),
            "summary": {},
            "detailed_findings": {},
        }

        # Patterns for detecting redundant configurations
        self.config_patterns = {
            "database_configs": [
                r"DATABASE_URL.*=.*",
                r"DB_HOST.*=.*",
                r"DB_PASSWORD.*=.*",
                r"connection_string.*=.*",
            ],
            "redis_configs": [
                r"REDIS_HOST.*=.*",
                r"REDIS_PASSWORD.*=.*",
                r"redis_host.*=.*",
                r"redis_password.*=.*",
            ],
            "api_configs": [
                r"API_BASE_URL.*=.*",
                r"WEBSOCKET_URL.*=.*",
                r"api_base.*=.*",
                r"websocket_url.*=.*",
            ],
            "service_configs": [
                r"GEMINI_API_KEY.*=.*",
                r"EBAY_APP_ID.*=.*",
                r"QDRANT_URL.*=.*",
            ],
        }

        # Common code patterns that might be duplicated
        self.code_patterns = {
            "initialization_patterns": [
                r"def __init__\(self.*\):",
                r"super\(\).__init__\(",
                r"self\.logger = logging\.getLogger",
            ],
            "database_patterns": [
                r"async with.*get_session\(\)",
                r"await.*session\.execute",
                r"session\.add\(",
                r"await session\.commit\(\)",
            ],
            "error_handling": [
                r"try:",
                r"except.*Exception.*as.*:",
                r"logger\.error\(",
                r"raise.*Error\(",
            ],
            "async_patterns": [
                r"async def.*\(",
                r"await.*\(",
                r"asyncio\.run\(",
                r"asyncio\.create_task\(",
            ],
        }

    def analyze_redundancy(self) -> Dict:
        """Run comprehensive redundancy analysis."""
        print(f"🔍 Starting redundancy analysis of {self.base_path}")

        # Collect all files
        files_to_analyze = self._collect_files()
        print(f"📁 Found {len(files_to_analyze)} files to analyze")

        # Analyze different types of redundancy
        self._analyze_duplicate_functions(files_to_analyze)
        self._analyze_similar_classes(files_to_analyze)
        self._analyze_configuration_redundancy(files_to_analyze)
        self._analyze_import_redundancy(files_to_analyze)

        # Generate summary
        self._generate_summary()

        print("✅ Redundancy analysis completed")
        return self.results

    def _collect_files(self) -> List[Path]:
        """Collect all Python files for analysis."""
        files = []

        for root, dirs, filenames in os.walk(self.base_path):
            # Skip common directories
            dirs[:] = [
                d
                for d in dirs
                if not d.startswith(".")
                and d
                not in {
                    "__pycache__",
                    "node_modules",
                    "venv",
                    "env",
                    ".git",
                    "logs",
                    "venv_agentic",
                    "flipsync_agentic_venv",
                    ".venv",
                    "build",
                    "dist",
                    "tmp",
                    "temp",
                    ".mypy_cache",
                    ".pytest_cache",
                }
                and not any(
                    keyword in d.lower() for keyword in ["backup", "bak", "cache"]
                )
            ]

            for filename in filenames:
                if filename.endswith(".py"):
                    files.append(Path(root) / filename)

        return files

    def _analyze_duplicate_functions(self, files: List[Path]):
        """Analyze for duplicate or very similar functions."""
        print("🔄 Analyzing duplicate functions...")

        function_signatures = defaultdict(list)
        function_bodies = defaultdict(list)

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            # Create signature hash
                            signature = f"{node.name}({len(node.args.args)})"
                            function_signatures[signature].append(
                                {
                                    "file": str(file_path),
                                    "name": node.name,
                                    "line": node.lineno,
                                    "args_count": len(node.args.args),
                                }
                            )

                            # Create body hash for similarity detection
                            body_lines = []
                            for stmt in node.body:
                                if isinstance(stmt, ast.Expr) and isinstance(
                                    stmt.value, ast.Constant
                                ):
                                    continue  # Skip docstrings
                                body_lines.append(ast.dump(stmt))

                            body_hash = hashlib.md5(
                                "\n".join(body_lines).encode()
                            ).hexdigest()
                            function_bodies[body_hash].append(
                                {
                                    "file": str(file_path),
                                    "name": node.name,
                                    "line": node.lineno,
                                    "signature": signature,
                                }
                            )

                except SyntaxError:
                    continue

            except Exception:
                continue

        # Find duplicates
        duplicate_signatures = {
            k: v for k, v in function_signatures.items() if len(v) > 1
        }
        duplicate_bodies = {k: v for k, v in function_bodies.items() if len(v) > 1}

        self.results["detailed_findings"]["duplicate_functions"] = {
            "duplicate_signatures": duplicate_signatures,
            "duplicate_bodies": duplicate_bodies,
            "total_signature_duplicates": sum(
                len(v) for v in duplicate_signatures.values()
            ),
            "total_body_duplicates": sum(len(v) for v in duplicate_bodies.values()),
        }

    def _analyze_similar_classes(self, files: List[Path]):
        """Analyze for similar class definitions."""
        print("🏗️ Analyzing similar classes...")

        class_definitions = defaultdict(list)

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            # Analyze class structure
                            methods = []
                            attributes = []

                            for item in node.body:
                                if isinstance(item, ast.FunctionDef):
                                    methods.append(item.name)
                                elif isinstance(item, ast.Assign):
                                    for target in item.targets:
                                        if isinstance(target, ast.Name):
                                            attributes.append(target.id)

                            class_info = {
                                "file": str(file_path),
                                "name": node.name,
                                "line": node.lineno,
                                "methods": sorted(methods),
                                "attributes": sorted(attributes),
                                "method_count": len(methods),
                                "attribute_count": len(attributes),
                                "bases": [
                                    base.id if isinstance(base, ast.Name) else str(base)
                                    for base in node.bases
                                ],
                            }

                            # Create similarity key based on methods and structure
                            similarity_key = (
                                f"{len(methods)}_{len(attributes)}_{sorted(methods)}"
                            )
                            class_definitions[similarity_key].append(class_info)

                except SyntaxError:
                    continue

            except Exception:
                continue

        # Find similar classes
        similar_classes = {k: v for k, v in class_definitions.items() if len(v) > 1}

        self.results["detailed_findings"]["similar_classes"] = {
            "similar_classes": similar_classes,
            "total_similar_classes": sum(len(v) for v in similar_classes.values()),
        }

    def _analyze_configuration_redundancy(self, files: List[Path]):
        """Analyze for redundant configuration patterns."""
        print("⚙️ Analyzing configuration redundancy...")

        config_occurrences = defaultdict(list)

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                for category, patterns in self.config_patterns.items():
                    for pattern in patterns:
                        for line_num, line in enumerate(lines, 1):
                            matches = re.findall(pattern, line, re.IGNORECASE)
                            if matches:
                                config_occurrences[category].append(
                                    {
                                        "file": str(file_path),
                                        "line": line_num,
                                        "content": line.strip(),
                                        "pattern": pattern,
                                        "matches": matches,
                                    }
                                )

            except Exception:
                continue

        # Identify redundant configurations
        redundant_configs = {}
        for category, occurrences in config_occurrences.items():
            if len(occurrences) > 1:
                redundant_configs[category] = occurrences

        self.results["detailed_findings"]["configuration_redundancy"] = {
            "redundant_configs": redundant_configs,
            "total_redundant_configs": sum(len(v) for v in redundant_configs.values()),
        }

    def _analyze_import_redundancy(self, files: List[Path]):
        """Analyze for redundant import patterns."""
        print("📦 Analyzing import redundancy...")

        import_usage = defaultdict(list)

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                import_usage[alias.name].append(
                                    {
                                        "file": str(file_path),
                                        "line": node.lineno,
                                        "type": "import",
                                        "module": alias.name,
                                        "alias": alias.asname,
                                    }
                                )
                        elif isinstance(node, ast.ImportFrom):
                            for alias in node.names:
                                module_name = (
                                    f"{node.module}.{alias.name}"
                                    if node.module
                                    else alias.name
                                )
                                import_usage[module_name].append(
                                    {
                                        "file": str(file_path),
                                        "line": node.lineno,
                                        "type": "from_import",
                                        "module": module_name,
                                        "from_module": node.module,
                                        "alias": alias.asname,
                                    }
                                )

                except SyntaxError:
                    continue

            except Exception:
                continue

        # Find commonly imported modules
        common_imports = {k: v for k, v in import_usage.items() if len(v) > 5}

        self.results["detailed_findings"]["import_redundancy"] = {
            "common_imports": common_imports,
            "total_import_occurrences": sum(len(v) for v in import_usage.values()),
            "unique_imports": len(import_usage),
        }

    def _generate_summary(self):
        """Generate summary of redundancy findings."""
        summary = {
            "total_files_analyzed": 0,
            "redundancy_categories": {},
            "high_priority_redundancies": [],
            "recommendations": [],
        }

        findings = self.results["detailed_findings"]

        # Count files analyzed
        if "duplicate_functions" in findings:
            summary["redundancy_categories"]["duplicate_functions"] = {
                "signature_duplicates": findings["duplicate_functions"][
                    "total_signature_duplicates"
                ],
                "body_duplicates": findings["duplicate_functions"][
                    "total_body_duplicates"
                ],
            }

        if "similar_classes" in findings:
            summary["redundancy_categories"]["similar_classes"] = {
                "total_similar": findings["similar_classes"]["total_similar_classes"]
            }

        if "configuration_redundancy" in findings:
            summary["redundancy_categories"]["configuration_redundancy"] = {
                "total_redundant": findings["configuration_redundancy"][
                    "total_redundant_configs"
                ]
            }

        if "import_redundancy" in findings:
            summary["redundancy_categories"]["import_redundancy"] = {
                "unique_imports": findings["import_redundancy"]["unique_imports"],
                "total_occurrences": findings["import_redundancy"][
                    "total_import_occurrences"
                ],
            }

        # Generate recommendations
        if (
            summary["redundancy_categories"]
            .get("duplicate_functions", {})
            .get("body_duplicates", 0)
            > 0
        ):
            summary["recommendations"].append(
                "Consolidate duplicate function implementations into shared utility modules"
            )

        if (
            summary["redundancy_categories"]
            .get("configuration_redundancy", {})
            .get("total_redundant", 0)
            > 0
        ):
            summary["recommendations"].append(
                "Centralize configuration management to eliminate redundant config definitions"
            )

        if (
            summary["redundancy_categories"]
            .get("similar_classes", {})
            .get("total_similar", 0)
            > 0
        ):
            summary["recommendations"].append(
                "Consider creating base classes or mixins for similar class structures"
            )

        self.results["summary"] = summary

    def save_results(self, filename: str = None) -> str:
        """Save analysis results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"redundancy_analysis_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"📄 Results saved to {filename}")
        return filename


def main():
    """Main execution function."""
    detector = RedundancyDetector()

    try:
        # Run analysis
        results = detector.analyze_redundancy()

        # Save results
        filename = detector.save_results()

        # Print summary
        print("\n" + "=" * 60)
        print("FLIPSYNC REDUNDANCY ANALYSIS SUMMARY")
        print("=" * 60)

        summary = results["summary"]

        print("Redundancy categories found:")
        for category, data in summary["redundancy_categories"].items():
            print(f"  - {category}:")
            for key, value in data.items():
                print(f"    - {key}: {value}")

        print(f"\nRecommendations:")
        for i, rec in enumerate(summary["recommendations"], 1):
            print(f"  {i}. {rec}")

        print("\n" + "=" * 60)
        print("Redundancy analysis completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
