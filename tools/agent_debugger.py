#!/usr/bin/env python3
"""
FlipSync Agent Debugging Tool
Provides debugging capabilities for the sophisticated 35+ agent architecture
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any


class AgentDebugger:
    """Debug tool for FlipSync's multi-agent architecture"""

    def __init__(self):
        self.agents_dir = Path("fs_agt_clean/agents")
        self.services_dir = Path("fs_agt_clean/services")

    def list_agents(self) -> Dict[str, List[str]]:
        """List all agents by category"""
        categories = {
            "executive": [],
            "market": [],
            "content": [],
            "logistics": [],
            "automation": [],
            "conversational": [],
        }

        for category in categories.keys():
            category_path = self.agents_dir / category
            if category_path.exists():
                for file in category_path.glob("*agent*.py"):
                    if not file.name.startswith("test_"):
                        categories[category].append(file.name)

        return categories

    def analyze_agent(self, agent_path: str) -> Dict[str, Any]:
        """Analyze a specific agent file"""
        try:
            with open(agent_path, "r") as f:
                content = f.read()

            analysis = {
                "file": agent_path,
                "lines": len(content.split("\n")),
                "classes": [],
                "methods": [],
                "imports": [],
            }

            # Simple parsing for classes and methods
            for line_num, line in enumerate(content.split("\n"), 1):
                line = line.strip()
                if line.startswith("class "):
                    class_name = line.split("(")[0].replace("class ", "").strip(":")
                    analysis["classes"].append({"name": class_name, "line": line_num})
                elif line.startswith("def "):
                    method_name = line.split("(")[0].replace("def ", "")
                    analysis["methods"].append({"name": method_name, "line": line_num})
                elif line.startswith("import ") or line.startswith("from "):
                    analysis["imports"].append(line)

            return analysis

        except Exception as e:
            return {"error": str(e)}

    def check_agent_dependencies(self, agent_name: str) -> Dict[str, Any]:
        """Check dependencies for a specific agent"""
        dependencies = {"services": [], "other_agents": [], "external_libs": []}

        # Find agent file
        agent_file = None
        for root, dirs, files in os.walk(self.agents_dir):
            for file in files:
                if agent_name.lower() in file.lower() and file.endswith(".py"):
                    agent_file = os.path.join(root, file)
                    break

        if not agent_file:
            return {"error": f"Agent {agent_name} not found"}

        try:
            with open(agent_file, "r") as f:
                content = f.read()

            # Analyze imports
            for line in content.split("\n"):
                line = line.strip()
                if line.startswith("from fs_agt_clean.services"):
                    service = line.split(".")[-1].split(" ")[0]
                    dependencies["services"].append(service)
                elif line.startswith("from fs_agt_clean.agents"):
                    agent = line.split(".")[-1].split(" ")[0]
                    dependencies["other_agents"].append(agent)
                elif line.startswith("import ") and "fs_agt_clean" not in line:
                    lib = line.replace("import ", "").split(".")[0]
                    dependencies["external_libs"].append(lib)

            return dependencies

        except Exception as e:
            return {"error": str(e)}

    def generate_agent_map(self) -> Dict[str, Any]:
        """Generate a map of all agents and their relationships"""
        agent_map = {"total_agents": 0, "categories": {}, "relationships": []}

        categories = self.list_agents()
        agent_map["categories"] = categories
        agent_map["total_agents"] = sum(len(agents) for agents in categories.values())

        return agent_map


def main():
    """Main CLI interface for agent debugging"""
    parser = argparse.ArgumentParser(description="FlipSync Agent Debugging Tool")
    parser.add_argument(
        "--list", action="store_true", help="List all agents by category"
    )
    parser.add_argument("--analyze", type=str, help="Analyze specific agent file")
    parser.add_argument("--deps", type=str, help="Check dependencies for agent")
    parser.add_argument(
        "--map", action="store_true", help="Generate agent relationship map"
    )
    parser.add_argument("--json", action="store_true", help="Output in JSON format")

    args = parser.parse_args()
    debugger = AgentDebugger()

    if args.list:
        categories = debugger.list_agents()
        if args.json:
            print(json.dumps(categories, indent=2))
        else:
            print("=== FlipSync Agent Architecture ===")
            total = 0
            for category, agents in categories.items():
                print(f"\n{category.title()} Agents ({len(agents)}):")
                for agent in agents:
                    print(f"  - {agent}")
                total += len(agents)
            print(f"\nTotal Agents: {total}")

    elif args.analyze:
        analysis = debugger.analyze_agent(args.analyze)
        if args.json:
            print(json.dumps(analysis, indent=2))
        else:
            if "error" in analysis:
                print(f"Error: {analysis['error']}")
            else:
                print(f"=== Analysis: {analysis['file']} ===")
                print(f"Lines: {analysis['lines']}")
                print(f"Classes: {len(analysis['classes'])}")
                print(f"Methods: {len(analysis['methods'])}")
                print(f"Imports: {len(analysis['imports'])}")

    elif args.deps:
        deps = debugger.check_agent_dependencies(args.deps)
        if args.json:
            print(json.dumps(deps, indent=2))
        else:
            if "error" in deps:
                print(f"Error: {deps['error']}")
            else:
                print(f"=== Dependencies for {args.deps} ===")
                print(f"Services: {len(deps['services'])}")
                print(f"Other Agents: {len(deps['other_agents'])}")
                print(f"External Libraries: {len(deps['external_libs'])}")

    elif args.map:
        agent_map = debugger.generate_agent_map()
        if args.json:
            print(json.dumps(agent_map, indent=2))
        else:
            print("=== FlipSync Agent Architecture Map ===")
            print(f"Total Agents: {agent_map['total_agents']}")
            for category, agents in agent_map["categories"].items():
                print(f"{category.title()}: {len(agents)} agents")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
