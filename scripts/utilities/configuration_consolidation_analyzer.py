#!/usr/bin/env python3
"""
FlipSync Configuration Consolidation Analyzer
Comprehensive analysis of configuration management patterns, hardcoded values,
and environment variable usage across the fs_agt_clean/ directory.
"""

import ast
import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple


class ConfigurationConsolidationAnalyzer:
    """Comprehensive configuration consolidation analysis tool."""

    def __init__(self, base_path: str = "fs_agt_clean"):
        self.base_path = Path(base_path)
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "analysis_type": "configuration_consolidation",
            "base_path": str(self.base_path),
            "summary": {},
            "detailed_findings": {},
        }

        # Configuration patterns to detect
        self.config_patterns = {
            "hardcoded_credentials": [
                r"password\s*=\s*['\"]([^'\"]+)['\"]",
                r"api_key\s*=\s*['\"]([^'\"]+)['\"]",
                r"secret\s*=\s*['\"]([^'\"]+)['\"]",
                r"token\s*=\s*['\"]([^'\"]+)['\"]",
            ],
            "hardcoded_urls": [
                r"https?://[^\s'\"]+",
                r"ws://[^\s'\"]+",
                r"wss://[^\s'\"]+",
            ],
            "hardcoded_ips": [
                r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",
                r"localhost",
                r"127\.0\.0\.1",
            ],
            "hardcoded_ports": [
                r":\d{4,5}",
                r"port\s*=\s*\d+",
            ],
            "database_configs": [
                r"DATABASE_URL",
                r"DB_HOST",
                r"DB_PASSWORD",
                r"DB_USER",
                r"DB_NAME",
                r"connection_string",
            ],
            "service_configs": [
                r"REDIS_HOST",
                r"REDIS_PASSWORD",
                r"GEMINI_API_KEY",
                r"EBAY_APP_ID",
                r"QDRANT_URL",
                r"WEBSOCKET_URL",
            ],
        }

        # Environment variable patterns
        self.env_patterns = [
            r"os\.environ\.get\(['\"]([^'\"]+)['\"]",
            r"os\.getenv\(['\"]([^'\"]+)['\"]",
            r"getenv\(['\"]([^'\"]+)['\"]",
            r"env\.[A-Z_]+",
        ]

        # Configuration file extensions
        self.config_extensions = {
            ".yaml",
            ".yml",
            ".json",
            ".env",
            ".conf",
            ".ini",
            ".toml",
        }

    def analyze_configuration(self) -> Dict:
        """Run comprehensive configuration analysis."""
        print(f"🔍 Starting configuration consolidation analysis of {self.base_path}")

        # Collect all files
        files_to_analyze = self._collect_files()
        print(
            f"📁 Found {sum(len(files) for files in files_to_analyze.values())} files to analyze"
        )

        # Analyze different aspects of configuration
        self._analyze_hardcoded_values(files_to_analyze)
        self._analyze_environment_variables(files_to_analyze)
        self._analyze_configuration_files(files_to_analyze)
        self._analyze_config_classes(files_to_analyze)
        self._identify_configuration_inconsistencies()

        # Generate consolidation recommendations
        self._generate_consolidation_plan()

        print("✅ Configuration consolidation analysis completed")
        return self.results

    def _collect_files(self) -> Dict[str, List[Path]]:
        """Collect files categorized by type."""
        files = {"python": [], "config": [], "other": []}

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

                if filename.endswith(".py"):
                    files["python"].append(file_path)
                elif file_path.suffix in self.config_extensions:
                    files["config"].append(file_path)
                else:
                    files["other"].append(file_path)

        return files

    def _analyze_hardcoded_values(self, files: Dict[str, List[Path]]):
        """Analyze hardcoded configuration values."""
        print("🔒 Analyzing hardcoded values...")

        hardcoded_findings = defaultdict(list)

        # Analyze Python files
        for file_path in files["python"]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                for category, patterns in self.config_patterns.items():
                    for pattern in patterns:
                        for line_num, line in enumerate(lines, 1):
                            matches = re.findall(pattern, line, re.IGNORECASE)
                            if matches:
                                hardcoded_findings[category].append(
                                    {
                                        "file": str(file_path),
                                        "line": line_num,
                                        "content": line.strip(),
                                        "pattern": pattern,
                                        "matches": matches,
                                        "severity": self._assess_severity(
                                            category, line
                                        ),
                                    }
                                )

            except Exception as e:
                hardcoded_findings["file_errors"].append(
                    {"file": str(file_path), "error": str(e)}
                )

        # Analyze configuration files
        for file_path in files["config"]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                for line_num, line in enumerate(lines, 1):
                    # Look for hardcoded values in config files
                    if any(
                        pattern in line.lower()
                        for pattern in ["password", "secret", "key", "token"]
                    ):
                        if not line.strip().startswith("#") and "=" in line:
                            hardcoded_findings["config_file_secrets"].append(
                                {
                                    "file": str(file_path),
                                    "line": line_num,
                                    "content": line.strip(),
                                    "severity": "HIGH",
                                }
                            )

            except Exception as e:
                hardcoded_findings["config_file_errors"].append(
                    {"file": str(file_path), "error": str(e)}
                )

        self.results["detailed_findings"]["hardcoded_values"] = dict(hardcoded_findings)

    def _assess_severity(self, category: str, line: str) -> str:
        """Assess the severity of hardcoded values."""
        high_severity_indicators = ["password", "secret", "key", "token", "credential"]

        medium_severity_indicators = ["host", "url", "endpoint", "database"]

        line_lower = line.lower()

        if any(indicator in line_lower for indicator in high_severity_indicators):
            return "HIGH"
        elif any(indicator in line_lower for indicator in medium_severity_indicators):
            return "MEDIUM"
        else:
            return "LOW"

    def _analyze_environment_variables(self, files: Dict[str, List[Path]]):
        """Analyze environment variable usage patterns."""
        print("🌍 Analyzing environment variables...")

        env_findings = defaultdict(list)
        env_variables = set()

        for file_path in files["python"]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    lines = content.split("\n")

                for pattern in self.env_patterns:
                    for line_num, line in enumerate(lines, 1):
                        matches = re.findall(pattern, line)
                        if matches:
                            for match in matches:
                                env_variables.add(match)
                                env_findings["env_usage"].append(
                                    {
                                        "file": str(file_path),
                                        "line": line_num,
                                        "content": line.strip(),
                                        "env_var": match,
                                        "pattern": pattern,
                                    }
                                )

            except Exception as e:
                env_findings["env_errors"].append(
                    {"file": str(file_path), "error": str(e)}
                )

        env_findings["unique_env_vars"] = sorted(list(env_variables))
        self.results["detailed_findings"]["environment_variables"] = dict(env_findings)

    def _analyze_configuration_files(self, files: Dict[str, List[Path]]):
        """Analyze dedicated configuration files."""
        print("📄 Analyzing configuration files...")

        config_findings = defaultdict(list)

        for file_path in files["config"]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                file_info = {
                    "file": str(file_path),
                    "extension": file_path.suffix,
                    "size_bytes": len(content),
                    "line_count": len(content.split("\n")),
                    "config_entries": [],
                }

                # Parse different config file types
                if file_path.suffix == ".json":
                    try:
                        config_data = json.loads(content)
                        file_info["config_entries"] = self._extract_json_config(
                            config_data
                        )
                        file_info["valid_json"] = True
                    except json.JSONDecodeError as e:
                        file_info["json_error"] = str(e)
                        file_info["valid_json"] = False

                elif file_path.suffix in [".yaml", ".yml"]:
                    try:
                        import yaml

                        config_data = yaml.safe_load(content)
                        file_info["config_entries"] = self._extract_yaml_config(
                            config_data
                        )
                        file_info["valid_yaml"] = True
                    except Exception as e:
                        file_info["yaml_error"] = str(e)
                        file_info["valid_yaml"] = False

                elif file_path.suffix == ".env":
                    file_info["config_entries"] = self._extract_env_config(content)

                config_findings["config_files"].append(file_info)

            except Exception as e:
                config_findings["config_file_errors"].append(
                    {"file": str(file_path), "error": str(e)}
                )

        self.results["detailed_findings"]["configuration_files"] = dict(config_findings)

    def _extract_json_config(self, data, prefix="") -> List[Dict]:
        """Extract configuration entries from JSON data."""
        entries = []

        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    entries.extend(self._extract_json_config(value, full_key))
                else:
                    entries.append(
                        {
                            "key": full_key,
                            "value": str(value),
                            "type": type(value).__name__,
                        }
                    )
        elif isinstance(data, list):
            for i, item in enumerate(data):
                full_key = f"{prefix}[{i}]"
                if isinstance(item, (dict, list)):
                    entries.extend(self._extract_json_config(item, full_key))
                else:
                    entries.append(
                        {
                            "key": full_key,
                            "value": str(item),
                            "type": type(item).__name__,
                        }
                    )

        return entries

    def _extract_yaml_config(self, data, prefix="") -> List[Dict]:
        """Extract configuration entries from YAML data."""
        return self._extract_json_config(data, prefix)  # Same logic as JSON

    def _extract_env_config(self, content: str) -> List[Dict]:
        """Extract configuration entries from .env files."""
        entries = []
        lines = content.split("\n")

        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                entries.append(
                    {"key": key.strip(), "value": value.strip(), "line": line_num}
                )

        return entries

    def _analyze_config_classes(self, files: Dict[str, List[Path]]):
        """Analyze configuration classes and their patterns."""
        print("🏗️ Analyzing configuration classes...")

        config_class_findings = defaultdict(list)

        for file_path in files["python"]:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                try:
                    tree = ast.parse(content)

                    for node in ast.walk(tree):
                        if isinstance(node, ast.ClassDef):
                            # Look for configuration-related classes
                            if any(
                                keyword in node.name.lower()
                                for keyword in ["config", "settings", "env"]
                            ):
                                class_info = {
                                    "file": str(file_path),
                                    "name": node.name,
                                    "line": node.lineno,
                                    "attributes": [],
                                    "methods": [],
                                }

                                for item in node.body:
                                    if isinstance(item, ast.Assign):
                                        for target in item.targets:
                                            if isinstance(target, ast.Name):
                                                class_info["attributes"].append(
                                                    target.id
                                                )
                                    elif isinstance(item, ast.FunctionDef):
                                        class_info["methods"].append(item.name)

                                config_class_findings["config_classes"].append(
                                    class_info
                                )

                except SyntaxError:
                    continue

            except Exception as e:
                config_class_findings["config_class_errors"].append(
                    {"file": str(file_path), "error": str(e)}
                )

        self.results["detailed_findings"]["config_classes"] = dict(
            config_class_findings
        )

    def _identify_configuration_inconsistencies(self):
        """Identify inconsistencies in configuration management."""
        print("🔍 Identifying configuration inconsistencies...")

        inconsistencies = {
            "hardcoded_vs_env": [],
            "duplicate_configs": [],
            "missing_env_vars": [],
            "security_issues": [],
        }

        # Analyze hardcoded values vs environment variables
        hardcoded = self.results["detailed_findings"].get("hardcoded_values", {})
        env_vars = self.results["detailed_findings"].get("environment_variables", {})

        # Find hardcoded values that should be environment variables
        for category, findings in hardcoded.items():
            if category in ["hardcoded_credentials", "hardcoded_urls", "hardcoded_ips"]:
                for finding in findings:
                    if finding.get("severity") in ["HIGH", "MEDIUM"]:
                        inconsistencies["hardcoded_vs_env"].append(
                            {
                                "file": finding["file"],
                                "line": finding["line"],
                                "content": finding["content"],
                                "category": category,
                                "severity": finding["severity"],
                                "recommendation": "Move to environment variable",
                            }
                        )

        # Find security issues
        for category, findings in hardcoded.items():
            if "credential" in category or "secret" in category:
                for finding in findings:
                    inconsistencies["security_issues"].append(
                        {
                            "file": finding["file"],
                            "line": finding["line"],
                            "content": finding["content"],
                            "issue": "Hardcoded sensitive information",
                            "severity": "CRITICAL",
                        }
                    )

        self.results["detailed_findings"]["inconsistencies"] = inconsistencies

    def _generate_consolidation_plan(self):
        """Generate comprehensive consolidation recommendations."""
        print("📋 Generating consolidation plan...")

        consolidation_plan = {
            "priority_actions": [],
            "environment_variables": {
                "required": [],
                "recommended": [],
                "migration_plan": [],
            },
            "configuration_files": {"standardization": [], "consolidation": []},
            "code_changes": {
                "high_priority": [],
                "medium_priority": [],
                "low_priority": [],
            },
            "implementation_timeline": {
                "phase_1": "Critical security fixes (1-2 days)",
                "phase_2": "Environment variable migration (3-5 days)",
                "phase_3": "Configuration file standardization (2-3 days)",
                "phase_4": "Code cleanup and optimization (3-5 days)",
            },
        }

        # Generate priority actions based on findings
        findings = self.results["detailed_findings"]

        # Critical security issues
        if "inconsistencies" in findings:
            for issue in findings["inconsistencies"].get("security_issues", []):
                consolidation_plan["priority_actions"].append(
                    {
                        "action": "Remove hardcoded sensitive information",
                        "file": issue["file"],
                        "line": issue["line"],
                        "priority": "CRITICAL",
                        "timeline": "Immediate",
                    }
                )

        # Environment variable recommendations
        if "hardcoded_values" in findings:
            for category, items in findings["hardcoded_values"].items():
                if category in ["hardcoded_urls", "hardcoded_ips", "service_configs"]:
                    for item in items:
                        if item.get("severity") in ["HIGH", "MEDIUM"]:
                            consolidation_plan["environment_variables"][
                                "required"
                            ].append(
                                {
                                    "current_value": item["content"],
                                    "suggested_env_var": self._suggest_env_var_name(
                                        item["content"]
                                    ),
                                    "file": item["file"],
                                    "line": item["line"],
                                }
                            )

        # Configuration file standardization
        if "configuration_files" in findings:
            config_files = findings["configuration_files"].get("config_files", [])
            if len(config_files) > 1:
                consolidation_plan["configuration_files"]["consolidation"].append(
                    {
                        "recommendation": "Consolidate multiple config files into single .env file",
                        "current_files": [f["file"] for f in config_files],
                        "suggested_approach": "Create centralized .env file with environment-specific overrides",
                    }
                )

        self.results["consolidation_plan"] = consolidation_plan

    def _suggest_env_var_name(self, content: str) -> str:
        """Suggest environment variable name based on content."""
        content_lower = content.lower()

        if "192.168.110.71" in content:
            return "FLIPSYNC_SERVER_HOST"
        elif "localhost" in content_lower:
            return "FLIPSYNC_LOCAL_HOST"
        elif "redis" in content_lower:
            return "REDIS_HOST" if "host" in content_lower else "REDIS_URL"
        elif "database" in content_lower or "db" in content_lower:
            return "DATABASE_URL"
        elif "gemini" in content_lower:
            return "GEMINI_API_KEY"
        elif "ebay" in content_lower:
            return "EBAY_API_CREDENTIALS"
        elif "qdrant" in content_lower:
            return "QDRANT_URL"
        elif "websocket" in content_lower:
            return "WEBSOCKET_URL"
        else:
            return "CONFIG_VALUE"

    def save_results(self, filename: str = None) -> str:
        """Save analysis results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"configuration_consolidation_{timestamp}.json"

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.results, f, indent=2, default=str)

        print(f"📄 Results saved to {filename}")
        return filename


def main():
    """Main execution function."""
    analyzer = ConfigurationConsolidationAnalyzer()

    try:
        # Run analysis
        results = analyzer.analyze_configuration()

        # Save results
        filename = analyzer.save_results()

        # Print summary
        print("\n" + "=" * 70)
        print("FLIPSYNC CONFIGURATION CONSOLIDATION ANALYSIS SUMMARY")
        print("=" * 70)

        findings = results["detailed_findings"]

        # Hardcoded values summary
        if "hardcoded_values" in findings:
            total_hardcoded = sum(
                len(items) for items in findings["hardcoded_values"].values()
            )
            print(f"Hardcoded values found: {total_hardcoded}")

            for category, items in findings["hardcoded_values"].items():
                if items and category != "file_errors":
                    high_severity = sum(
                        1 for item in items if item.get("severity") == "HIGH"
                    )
                    print(
                        f"  - {category}: {len(items)} ({high_severity} high severity)"
                    )

        # Environment variables summary
        if "environment_variables" in findings:
            env_vars = findings["environment_variables"].get("unique_env_vars", [])
            print(f"\nEnvironment variables in use: {len(env_vars)}")

        # Configuration files summary
        if "configuration_files" in findings:
            config_files = findings["configuration_files"].get("config_files", [])
            print(f"Configuration files found: {len(config_files)}")

        # Consolidation plan summary
        if "consolidation_plan" in results:
            plan = results["consolidation_plan"]
            print(f"\nPriority actions: {len(plan['priority_actions'])}")
            print(
                f"Required environment variables: {len(plan['environment_variables']['required'])}"
            )

        print("\n" + "=" * 70)
        print("Configuration consolidation analysis completed successfully!")
        print("=" * 70)

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
