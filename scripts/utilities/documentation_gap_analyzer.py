#!/usr/bin/env python3
"""
FlipSync Documentation Gap Analyzer
Comprehensive analysis of documentation coverage, consistency, and quality
across the FlipSync codebase for Proxmox migration preparation.
"""

import ast
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple


class DocumentationGapAnalyzer:
    """Comprehensive documentation gap analysis tool."""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "documentation_gap_analysis",
            "base_path": str(self.base_path),
            "summary": {},
            "detailed_findings": {},
        }

        # Documentation file patterns
        self.doc_patterns = {
            "readme_files": [r"README\.md", r"readme\.md", r"README\.txt"],
            "api_docs": [r"API.*\.md", r"api.*\.md", r"swagger.*", r"openapi.*"],
            "architecture_docs": [r"ARCHITECTURE.*\.md", r"architecture.*\.md"],
            "setup_docs": [
                r"SETUP.*\.md",
                r"INSTALL.*\.md",
                r"setup.*\.md",
                r"install.*\.md",
            ],
            "changelog": [r"CHANGELOG.*\.md", r"changelog.*\.md", r"CHANGES.*\.md"],
            "contributing": [r"CONTRIBUTING.*\.md", r"contributing.*\.md"],
            "license": [r"LICENSE.*", r"license.*"],
        }

        # Code documentation patterns
        self.code_doc_patterns = {
            "docstrings": r'""".*?"""',
            "single_line_comments": r"#.*",
            "type_hints": r":\s*[A-Za-z_][A-Za-z0-9_\[\],\s]*\s*=",
            "function_docs": r"def\s+\w+.*?:",
            "class_docs": r"class\s+\w+.*?:",
        }

        # Required documentation sections
        self.required_sections = {
            "README": ["installation", "usage", "api", "architecture", "contributing"],
            "API": ["endpoints", "authentication", "examples", "errors"],
            "ARCHITECTURE": ["overview", "components", "data flow", "deployment"],
        }

    def analyze_documentation(self) -> Dict:
        """Run comprehensive documentation analysis."""
        print(f"🔍 Starting documentation gap analysis of {self.base_path}")

        # Collect all files
        files_to_analyze = self._collect_files()
        print(
            f"📁 Found {sum(len(files) for files in files_to_analyze.values())} files to analyze"
        )

        # Analyze different aspects of documentation
        self._analyze_documentation_files(files_to_analyze)
        self._analyze_code_documentation(files_to_analyze)
        self._analyze_api_documentation(files_to_analyze)
        self._analyze_architecture_documentation(files_to_analyze)
        self._identify_documentation_gaps()

        # Generate improvement recommendations
        self._generate_documentation_plan()

        print("✅ Documentation gap analysis completed")
        return self.results

    def _collect_files(self) -> Dict[str, List[Path]]:
        """Collect files categorized by type."""
        files = {"documentation": [], "python": [], "config": [], "other": []}

        doc_extensions = {".md", ".rst", ".txt", ".adoc"}
        code_extensions = {".py"}
        config_extensions = {".yaml", ".yml", ".json", ".env", ".conf", ".ini", ".toml"}

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
                file_path = Path(root) / filename

                if file_path.suffix in doc_extensions or filename.upper() in [
                    "README",
                    "LICENSE",
                    "CHANGELOG",
                ]:
                    files["documentation"].append(file_path)
                elif file_path.suffix in code_extensions:
                    files["python"].append(file_path)
                elif file_path.suffix in config_extensions:
                    files["config"].append(file_path)
                else:
                    files["other"].append(file_path)

        return files

    def _analyze_documentation_files(self, files: Dict[str, List[Path]]):
        """Analyze dedicated documentation files."""
        print("📚 Analyzing documentation files...")

        doc_findings = {
            "found_docs": defaultdict(list),
            "missing_docs": [],
            "doc_quality": [],
            "doc_consistency": [],
        }

        # Check for required documentation types
        for doc_type, patterns in self.doc_patterns.items():
            found = False
            for file_path in files["documentation"]:
                for pattern in patterns:
                    if re.search(pattern, file_path.name, re.IGNORECASE):
                        doc_findings["found_docs"][doc_type].append(
                            {
                                "file": str(file_path),
                                "size_bytes": (
                                    file_path.stat().st_size
                                    if file_path.exists()
                                    else 0
                                ),
                                "last_modified": (
                                    file_path.stat().st_mtime
                                    if file_path.exists()
                                    else 0
                                ),
                            }
                        )
                        found = True

            if not found:
                doc_findings["missing_docs"].append(doc_type)

        # Analyze documentation quality
        for file_path in files["documentation"]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                quality_metrics = self._assess_doc_quality(file_path, content)
                doc_findings["doc_quality"].append(quality_metrics)

            except Exception as e:
                doc_findings["doc_quality"].append(
                    {"file": str(file_path), "error": str(e), "quality_score": 0}
                )

        self.results["detailed_findings"]["documentation_files"] = doc_findings

    def _assess_doc_quality(self, file_path: Path, content: str) -> Dict:
        """Assess the quality of a documentation file."""
        quality_metrics = {
            "file": str(file_path),
            "word_count": len(content.split()),
            "line_count": len(content.split("\n")),
            "has_headers": bool(re.search(r"^#+\s", content, re.MULTILINE)),
            "has_code_blocks": bool(re.search(r"```", content)),
            "has_links": bool(re.search(r"\[.*\]\(.*\)", content)),
            "has_images": bool(re.search(r"!\[.*\]\(.*\)", content)),
            "quality_score": 0,
        }

        # Calculate quality score
        score = 0
        if quality_metrics["word_count"] > 100:
            score += 20
        if quality_metrics["has_headers"]:
            score += 20
        if quality_metrics["has_code_blocks"]:
            score += 20
        if quality_metrics["has_links"]:
            score += 20
        if quality_metrics["has_images"]:
            score += 20

        quality_metrics["quality_score"] = score
        return quality_metrics

    def _analyze_code_documentation(self, files: Dict[str, List[Path]]):
        """Analyze code documentation coverage."""
        print("🐍 Analyzing code documentation...")

        code_doc_findings = {
            "docstring_coverage": [],
            "comment_density": [],
            "type_hint_coverage": [],
            "undocumented_functions": [],
            "undocumented_classes": [],
        }

        for file_path in files["python"]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)
                    file_metrics = self._analyze_python_file_docs(
                        file_path, tree, content
                    )

                    code_doc_findings["docstring_coverage"].append(
                        file_metrics["docstring_coverage"]
                    )
                    code_doc_findings["comment_density"].append(
                        file_metrics["comment_density"]
                    )
                    code_doc_findings["type_hint_coverage"].append(
                        file_metrics["type_hint_coverage"]
                    )
                    code_doc_findings["undocumented_functions"].extend(
                        file_metrics["undocumented_functions"]
                    )
                    code_doc_findings["undocumented_classes"].extend(
                        file_metrics["undocumented_classes"]
                    )

                except SyntaxError:
                    continue

            except Exception:
                continue

        self.results["detailed_findings"]["code_documentation"] = code_doc_findings

    def _analyze_python_file_docs(
        self, file_path: Path, tree: ast.AST, content: str
    ) -> Dict:
        """Analyze documentation in a Python file."""
        functions = []
        classes = []
        documented_functions = 0
        documented_classes = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node)
                if ast.get_docstring(node):
                    documented_functions += 1
            elif isinstance(node, ast.ClassDef):
                classes.append(node)
                if ast.get_docstring(node):
                    documented_classes += 1

        # Count comments
        comment_lines = len(re.findall(r"^\s*#", content, re.MULTILINE))
        total_lines = len(content.split("\n"))

        return {
            "docstring_coverage": {
                "file": str(file_path),
                "functions_total": len(functions),
                "functions_documented": documented_functions,
                "classes_total": len(classes),
                "classes_documented": documented_classes,
                "function_coverage": (
                    documented_functions / len(functions) if functions else 1.0
                ),
                "class_coverage": documented_classes / len(classes) if classes else 1.0,
            },
            "comment_density": {
                "file": str(file_path),
                "comment_lines": comment_lines,
                "total_lines": total_lines,
                "density": comment_lines / total_lines if total_lines else 0,
            },
            "type_hint_coverage": {
                "file": str(file_path),
                "has_type_hints": bool(re.search(r":\s*[A-Za-z_]", content)),
            },
            "undocumented_functions": [
                {"file": str(file_path), "function": func.name, "line": func.lineno}
                for func in functions
                if not ast.get_docstring(func)
            ],
            "undocumented_classes": [
                {"file": str(file_path), "class": cls.name, "line": cls.lineno}
                for cls in classes
                if not ast.get_docstring(cls)
            ],
        }

    def _analyze_api_documentation(self, files: Dict[str, List[Path]]):
        """Analyze API documentation coverage."""
        print("🔌 Analyzing API documentation...")

        api_findings = {
            "api_endpoints": [],
            "documented_endpoints": [],
            "missing_api_docs": [],
        }

        # Look for API endpoint definitions in Python files
        for file_path in files["python"]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                # Find FastAPI/Flask route decorators
                routes = re.findall(
                    r'@app\.(get|post|put|delete|patch)\(["\']([^"\']+)["\']', content
                )
                for method, endpoint in routes:
                    api_findings["api_endpoints"].append(
                        {
                            "file": str(file_path),
                            "method": method.upper(),
                            "endpoint": endpoint,
                        }
                    )

            except Exception:
                continue

        self.results["detailed_findings"]["api_documentation"] = api_findings

    def _analyze_architecture_documentation(self, files: Dict[str, List[Path]]):
        """Analyze architecture documentation coverage."""
        print("🏗️ Analyzing architecture documentation...")

        arch_findings = {
            "architecture_files": [],
            "component_coverage": [],
            "diagram_coverage": [],
        }

        # Look for architecture-related files
        for file_path in files["documentation"]:
            if (
                "architecture" in file_path.name.lower()
                or "arch" in file_path.name.lower()
            ):
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    arch_findings["architecture_files"].append(
                        {
                            "file": str(file_path),
                            "size": len(content),
                            "has_diagrams": bool(
                                re.search(
                                    r"!\[.*\]\(.*\.(png|jpg|svg|mermaid)\)", content
                                )
                            ),
                            "mentions_agents": bool(
                                re.search(r"agent", content, re.IGNORECASE)
                            ),
                            "mentions_services": bool(
                                re.search(r"service", content, re.IGNORECASE)
                            ),
                        }
                    )

                except Exception:
                    continue

        self.results["detailed_findings"]["architecture_documentation"] = arch_findings

    def _identify_documentation_gaps(self):
        """Identify gaps in documentation coverage."""
        print("🔍 Identifying documentation gaps...")

        gaps = {
            "critical_gaps": [],
            "missing_sections": [],
            "quality_issues": [],
            "consistency_issues": [],
        }

        findings = self.results["detailed_findings"]

        # Check for missing critical documentation
        if "documentation_files" in findings:
            missing_docs = findings["documentation_files"].get("missing_docs", [])
            for missing in missing_docs:
                if missing in ["readme_files", "api_docs", "architecture_docs"]:
                    gaps["critical_gaps"].append(
                        {
                            "type": missing,
                            "severity": "HIGH",
                            "description": f"Missing {missing} documentation",
                        }
                    )

        # Check code documentation coverage
        if "code_documentation" in findings:
            docstring_coverage = findings["code_documentation"].get(
                "docstring_coverage", []
            )
            for coverage in docstring_coverage:
                if coverage.get("function_coverage", 1.0) < 0.5:
                    gaps["quality_issues"].append(
                        {
                            "file": coverage["file"],
                            "issue": "Low function documentation coverage",
                            "coverage": coverage["function_coverage"],
                        }
                    )

        self.results["detailed_findings"]["documentation_gaps"] = gaps

    def _generate_documentation_plan(self):
        """Generate documentation improvement plan."""
        print("📋 Generating documentation improvement plan...")

        plan = {
            "immediate_actions": [],
            "short_term_goals": [],
            "long_term_goals": [],
            "implementation_timeline": {
                "week_1": "Address critical documentation gaps",
                "week_2": "Improve code documentation coverage",
                "week_3": "Standardize documentation format",
                "week_4": "Create comprehensive API documentation",
            },
        }

        findings = self.results["detailed_findings"]

        # Generate immediate actions based on gaps
        if "documentation_gaps" in findings:
            for gap in findings["documentation_gaps"].get("critical_gaps", []):
                plan["immediate_actions"].append(
                    {
                        "action": f"Create {gap['type']} documentation",
                        "priority": gap["severity"],
                        "estimated_hours": 8,
                    }
                )

        # Generate short-term goals
        plan["short_term_goals"].extend(
            [
                "Achieve 80%+ function documentation coverage",
                "Create comprehensive API documentation",
                "Standardize documentation templates",
                "Add architecture diagrams",
            ]
        )

        # Generate long-term goals
        plan["long_term_goals"].extend(
            [
                "Implement automated documentation generation",
                "Create interactive API documentation",
                "Establish documentation review process",
                "Integrate documentation into CI/CD pipeline",
            ]
        )

        self.results["documentation_plan"] = plan

    def save_results(self, filename: str = None) -> str:
        """Save analysis results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"documentation_gap_analysis_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"📄 Results saved to {filename}")
        return filename


def main():
    """Main execution function."""
    analyzer = DocumentationGapAnalyzer()

    try:
        # Run analysis
        results = analyzer.analyze_documentation()

        # Save results
        filename = analyzer.save_results()

        # Print summary
        print("\n" + "=" * 70)
        print("FLIPSYNC DOCUMENTATION GAP ANALYSIS SUMMARY")
        print("=" * 70)

        findings = results["detailed_findings"]

        # Documentation files summary
        if "documentation_files" in findings:
            found_docs = findings["documentation_files"]["found_docs"]
            missing_docs = findings["documentation_files"]["missing_docs"]

            print(
                f"Documentation files found: {sum(len(docs) for docs in found_docs.values())}"
            )
            print(f"Missing documentation types: {len(missing_docs)}")

            if missing_docs:
                print("Missing documentation:")
                for missing in missing_docs:
                    print(f"  - {missing}")

        # Code documentation summary
        if "code_documentation" in findings:
            docstring_coverage = findings["code_documentation"]["docstring_coverage"]
            if docstring_coverage:
                avg_function_coverage = sum(
                    d.get("function_coverage", 0) for d in docstring_coverage
                ) / len(docstring_coverage)
                avg_class_coverage = sum(
                    d.get("class_coverage", 0) for d in docstring_coverage
                ) / len(docstring_coverage)
                print(
                    f"\nAverage function documentation coverage: {avg_function_coverage:.1%}"
                )
                print(f"Average class documentation coverage: {avg_class_coverage:.1%}")

        # Documentation gaps summary
        if "documentation_gaps" in findings:
            gaps = findings["documentation_gaps"]
            print(f"\nCritical gaps: {len(gaps.get('critical_gaps', []))}")
            print(f"Quality issues: {len(gaps.get('quality_issues', []))}")

        print("\n" + "=" * 70)
        print("Documentation gap analysis completed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
