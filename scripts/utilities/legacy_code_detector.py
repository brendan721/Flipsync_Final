#!/usr/bin/env python3
"""
FlipSync Legacy Code Detection Tool
Comprehensive analysis of outdated patterns, unused imports, and deprecated functions
across the fs_agt_clean/ directory for Proxmox migration preparation.
"""

import ast
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

import json


class LegacyCodeDetector:
    """Comprehensive legacy code detection and analysis tool."""

    def __init__(self, base_path: str = "fs_agt_clean"):
        self.base_path = Path(base_path)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "legacy_code_detection",
            "base_path": str(self.base_path),
            "summary": {},
            "detailed_findings": {},
        }

        # Define legacy patterns to detect
        self.legacy_patterns = {
            "deprecated_imports": [
                r"import.*openai",  # OpenAI in autonomous agents (should be LLM-free)
                r"from.*openai",
                r"import.*langchain",  # LangChain dependencies
                r"from.*langchain",
                r"import.*anthropic",  # Direct Anthropic imports (should use unified interface)
                r"from.*anthropic",
            ],
            "debug_code": [
                r"print\s*\(",  # Debug print statements
                r"pprint\s*\(",  # Pretty print debugging
                r"console\.log",  # JavaScript console.log in Python files
                r"debugger",  # Debugger statements
                r"breakpoint\s*\(",  # Python breakpoints
            ],
            "hardcoded_values": [
                r"174\.138\.77\.110",  # Production IP addresses
                r"localhost:\d+",  # Localhost references
                r"127\.0\.0\.1:\d+",  # Local IP references
                r"AIzaSyC-.*",  # Hardcoded API keys
                r"BrendanB-.*",  # Hardcoded eBay credentials
                r"FlipSync_.*_2024_.*",  # Hardcoded passwords
            ],
            "todo_fixme": [
                r"TODO.*",  # TODO comments
                r"FIXME.*",  # FIXME comments
                r"HACK.*",  # HACK comments
                r"XXX.*",  # XXX comments
                r"BUG.*",  # BUG comments
            ],
            "blocking_calls": [
                r"time\.sleep\s*\(",  # Blocking sleep calls
                r"requests\.get\s*\(",  # Synchronous HTTP requests
                r"requests\.post\s*\(",
                r"urllib\.request\.",  # Synchronous urllib
            ],
            "deprecated_functions": [
                r"os\.system\s*\(",  # Deprecated os.system calls
                r"subprocess\.call\s*\(",  # Deprecated subprocess.call
                r"imp\.load_source",  # Deprecated imp module
                r"distutils\.",  # Deprecated distutils
            ],
        }

        # File extensions to analyze
        self.python_extensions = {".py"}
        self.config_extensions = {".yaml", ".yml", ".json", ".env", ".conf", ".ini"}
        self.all_extensions = self.python_extensions | self.config_extensions

    def analyze_codebase(self) -> Dict:
        """Run comprehensive legacy code analysis."""
        print(f"🔍 Starting legacy code analysis of {self.base_path}")

        # Collect all files to analyze
        files_to_analyze = self._collect_files()
        print(f"📁 Found {len(files_to_analyze)} files to analyze")

        # Analyze Python files
        python_files = [
            f for f in files_to_analyze if f.suffix in self.python_extensions
        ]
        self._analyze_python_files(python_files)

        # Analyze configuration files
        config_files = [
            f for f in files_to_analyze if f.suffix in self.config_extensions
        ]
        self._analyze_config_files(config_files)

        # Generate summary
        self._generate_summary()

        print("✅ Legacy code analysis completed")
        return self.results

    def _collect_files(self) -> List[Path]:
        """Collect all files for analysis."""
        files = []

        for root, dirs, filenames in os.walk(self.base_path):
            # Skip common directories that don't need analysis
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
                file_path = Path(root) / filename
                if file_path.suffix in self.all_extensions:
                    files.append(file_path)

        return files

    def _analyze_python_files(self, python_files: List[Path]):
        """Analyze Python files for legacy patterns."""
        print(f"🐍 Analyzing {len(python_files)} Python files...")

        python_results = {
            "files_analyzed": len(python_files),
            "issues_found": defaultdict(list),
            "import_analysis": defaultdict(list),
            "ast_analysis": defaultdict(list),
        }

        for file_path in python_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Pattern-based analysis
                file_issues = self._analyze_file_patterns(file_path, content)
                for category, issues in file_issues.items():
                    python_results["issues_found"][category].extend(issues)

                # AST-based analysis for Python files
                try:
                    tree = ast.parse(content)
                    ast_issues = self._analyze_ast(file_path, tree)
                    for category, issues in ast_issues.items():
                        python_results["ast_analysis"][category].extend(issues)
                except SyntaxError as e:
                    python_results["ast_analysis"]["syntax_errors"].append(
                        {
                            "file": str(file_path),
                            "error": str(e),
                            "line": getattr(e, "lineno", "unknown"),
                        }
                    )

            except Exception as e:
                python_results["issues_found"]["file_read_errors"].append(
                    {"file": str(file_path), "error": str(e)}
                )

        self.results["detailed_findings"]["python_analysis"] = python_results

    def _analyze_config_files(self, config_files: List[Path]):
        """Analyze configuration files for legacy patterns."""
        print(f"⚙️ Analyzing {len(config_files)} configuration files...")

        config_results = {
            "files_analyzed": len(config_files),
            "issues_found": defaultdict(list),
        }

        for file_path in config_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Pattern-based analysis
                file_issues = self._analyze_file_patterns(file_path, content)
                for category, issues in file_issues.items():
                    config_results["issues_found"][category].extend(issues)

            except Exception as e:
                config_results["issues_found"]["file_read_errors"].append(
                    {"file": str(file_path), "error": str(e)}
                )

        self.results["detailed_findings"]["config_analysis"] = config_results

    def _analyze_file_patterns(self, file_path: Path, content: str) -> Dict[str, List]:
        """Analyze file content for legacy patterns."""
        issues = defaultdict(list)
        lines = content.split("\n")

        for category, patterns in self.legacy_patterns.items():
            for pattern in patterns:
                for line_num, line in enumerate(lines, 1):
                    matches = re.findall(pattern, line, re.IGNORECASE)
                    if matches:
                        issues[category].append(
                            {
                                "file": str(file_path),
                                "line": line_num,
                                "content": line.strip(),
                                "pattern": pattern,
                                "matches": matches,
                            }
                        )

        return issues

    def _analyze_ast(self, file_path: Path, tree: ast.AST) -> Dict[str, List]:
        """Analyze Python AST for structural issues."""
        issues = defaultdict(list)

        class ASTAnalyzer(ast.NodeVisitor):
            def __init__(self):
                self.imports = []
                self.unused_imports = []
                self.function_calls = []
                self.class_definitions = []

            def visit_Import(self, node):
                for alias in node.names:
                    self.imports.append(
                        {
                            "module": alias.name,
                            "alias": alias.asname,
                            "line": node.lineno,
                        }
                    )
                self.generic_visit(node)

            def visit_ImportFrom(self, node):
                for alias in node.names:
                    self.imports.append(
                        {
                            "module": (
                                f"{node.module}.{alias.name}"
                                if node.module
                                else alias.name
                            ),
                            "alias": alias.asname,
                            "line": node.lineno,
                            "from_module": node.module,
                        }
                    )
                self.generic_visit(node)

            def visit_Call(self, node):
                if isinstance(node.func, ast.Name):
                    self.function_calls.append(
                        {"function": node.func.id, "line": node.lineno}
                    )
                elif isinstance(node.func, ast.Attribute):
                    self.function_calls.append(
                        {"function": node.func.attr, "line": node.lineno}
                    )
                self.generic_visit(node)

            def visit_ClassDef(self, node):
                self.class_definitions.append(
                    {
                        "name": node.name,
                        "line": node.lineno,
                        "bases": [
                            base.id if isinstance(base, ast.Name) else str(base)
                            for base in node.bases
                        ],
                    }
                )
                self.generic_visit(node)

        analyzer = ASTAnalyzer()
        analyzer.visit(tree)

        # Store AST analysis results
        issues["imports"].append({"file": str(file_path), "imports": analyzer.imports})

        issues["function_calls"].append(
            {"file": str(file_path), "calls": analyzer.function_calls}
        )

        issues["class_definitions"].append(
            {"file": str(file_path), "classes": analyzer.class_definitions}
        )

        return issues

    def _generate_summary(self):
        """Generate summary of findings."""
        summary = {
            "total_files_analyzed": 0,
            "python_files": 0,
            "config_files": 0,
            "issues_by_category": defaultdict(int),
            "high_priority_issues": [],
            "recommendations": [],
        }

        # Count files
        if "python_analysis" in self.results["detailed_findings"]:
            summary["python_files"] = self.results["detailed_findings"][
                "python_analysis"
            ]["files_analyzed"]
            summary["total_files_analyzed"] += summary["python_files"]

            # Count Python issues
            for category, issues in self.results["detailed_findings"][
                "python_analysis"
            ]["issues_found"].items():
                summary["issues_by_category"][category] += len(issues)

        if "config_analysis" in self.results["detailed_findings"]:
            summary["config_files"] = self.results["detailed_findings"][
                "config_analysis"
            ]["files_analyzed"]
            summary["total_files_analyzed"] += summary["config_files"]

            # Count config issues
            for category, issues in self.results["detailed_findings"][
                "config_analysis"
            ]["issues_found"].items():
                summary["issues_by_category"][category] += len(issues)

        # Identify high priority issues
        high_priority_categories = [
            "deprecated_imports",
            "hardcoded_values",
            "blocking_calls",
        ]
        for category in high_priority_categories:
            if summary["issues_by_category"][category] > 0:
                summary["high_priority_issues"].append(
                    {
                        "category": category,
                        "count": summary["issues_by_category"][category],
                        "priority": "HIGH",
                    }
                )

        # Generate recommendations
        if summary["issues_by_category"]["deprecated_imports"] > 0:
            summary["recommendations"].append(
                "Remove deprecated imports (OpenAI, LangChain) from autonomous agents to maintain LLM-free architecture"
            )

        if summary["issues_by_category"]["hardcoded_values"] > 0:
            summary["recommendations"].append(
                "Replace hardcoded values with environment variables for better configuration management"
            )

        if summary["issues_by_category"]["debug_code"] > 0:
            summary["recommendations"].append(
                "Remove debug print statements and replace with proper logging"
            )

        if summary["issues_by_category"]["blocking_calls"] > 0:
            summary["recommendations"].append(
                "Replace blocking calls with async alternatives for better performance"
            )

        self.results["summary"] = summary

    def save_results(self, filename: str = None) -> str:
        """Save analysis results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"legacy_code_analysis_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"📄 Results saved to {filename}")
        return filename


def main():
    """Main execution function."""
    detector = LegacyCodeDetector()

    try:
        # Run analysis
        results = detector.analyze_codebase()

        # Save results
        filename = detector.save_results()

        # Print summary
        print("\n" + "=" * 60)
        print("FLIPSYNC LEGACY CODE ANALYSIS SUMMARY")
        print("=" * 60)

        summary = results["summary"]
        print(f"Total files analyzed: {summary['total_files_analyzed']}")
        print(f"Python files: {summary['python_files']}")
        print(f"Config files: {summary['config_files']}")

        print(f"\nIssues found by category:")
        for category, count in summary["issues_by_category"].items():
            if count > 0:
                print(f"  - {category}: {count}")

        print(f"\nHigh priority issues:")
        for issue in summary["high_priority_issues"]:
            print(f"  - {issue['category']}: {issue['count']} ({issue['priority']})")

        print(f"\nRecommendations:")
        for i, rec in enumerate(summary["recommendations"], 1):
            print(f"  {i}. {rec}")

        print("\n" + "=" * 60)
        print("Analysis completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
