#!/usr/bin/env python3
"""
FlipSync Interactive Documentation Generator
Generates up-to-date documentation for the sophisticated architecture
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

class DocumentationGenerator:
    """Generate interactive documentation for FlipSync architecture"""
    
    def __init__(self):
        self.root_dir = Path(".")
        self.agents_dir = Path("fs_agt_clean/agents")
        self.services_dir = Path("fs_agt_clean/services")
        
    def generate_agent_inventory(self) -> Dict[str, Any]:
        """Generate comprehensive agent inventory"""
        inventory = {
            "generated_at": datetime.now().isoformat(),
            "total_agents": 0,
            "categories": {}
        }
        
        categories = ["executive", "market", "content", "logistics", "automation", "conversational"]
        
        for category in categories:
            category_path = self.agents_dir / category
            agents = []
            
            if category_path.exists():
                for agent_file in category_path.glob("*agent*.py"):
                    if not agent_file.name.startswith("test_"):
                        agent_info = self._analyze_agent_file(agent_file)
                        agents.append(agent_info)
            
            inventory["categories"][category] = {
                "count": len(agents),
                "agents": agents
            }
            inventory["total_agents"] += len(agents)
        
        return inventory
    
    def _analyze_agent_file(self, agent_file: Path) -> Dict[str, Any]:
        """Analyze individual agent file"""
        try:
            with open(agent_file, 'r') as f:
                content = f.read()
            
            info = {
                "name": agent_file.name,
                "path": str(agent_file),
                "size_lines": len(content.split('\n')),
                "classes": [],
                "key_methods": [],
                "description": ""
            }
            
            # Extract docstring as description
            lines = content.split('\n')
            in_docstring = False
            docstring_lines = []
            
            for line in lines:
                line = line.strip()
                if '"""' in line and not in_docstring:
                    in_docstring = True
                    if line.count('"""') == 2:  # Single line docstring
                        info["description"] = line.replace('"""', '').strip()
                        break
                    else:
                        docstring_lines.append(line.replace('"""', ''))
                elif in_docstring:
                    if '"""' in line:
                        docstring_lines.append(line.replace('"""', ''))
                        info["description"] = ' '.join(docstring_lines).strip()
                        break
                    else:
                        docstring_lines.append(line)
                elif line.startswith('class '):
                    class_name = line.split('(')[0].replace('class ', '').strip(':')
                    info["classes"].append(class_name)
                elif line.startswith('def ') and not line.startswith('def __'):
                    method_name = line.split('(')[0].replace('def ', '')
                    if method_name not in ['__init__', '__str__', '__repr__']:
                        info["key_methods"].append(method_name)
            
            return info
            
        except Exception as e:
            return {
                "name": agent_file.name,
                "path": str(agent_file),
                "error": str(e)
            }
    
    def generate_service_inventory(self) -> Dict[str, Any]:
        """Generate comprehensive service inventory"""
        inventory = {
            "generated_at": datetime.now().isoformat(),
            "total_services": 0,
            "categories": {}
        }
        
        for category_dir in self.services_dir.iterdir():
            if category_dir.is_dir() and not category_dir.name.startswith('.'):
                services = []
                
                for service_file in category_dir.rglob("*.py"):
                    if (not service_file.name.startswith("test_") and 
                        service_file.name != "__init__.py"):
                        service_info = {
                            "name": service_file.name,
                            "path": str(service_file.relative_to(self.root_dir)),
                            "category": category_dir.name
                        }
                        services.append(service_info)
                
                inventory["categories"][category_dir.name] = {
                    "count": len(services),
                    "services": services
                }
                inventory["total_services"] += len(services)
        
        return inventory
    
    def generate_architecture_summary(self) -> str:
        """Generate architecture summary document"""
        agent_inventory = self.generate_agent_inventory()
        service_inventory = self.generate_service_inventory()
        
        summary = f"""# FlipSync Architecture Summary
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Overview
FlipSync is an enterprise-grade e-commerce automation platform with sophisticated 
multi-agent architecture designed for large-scale marketplace operations.

## Current Architecture Metrics
- **Total Agents**: {agent_inventory['total_agents']}
- **Total Services**: {service_inventory['total_services']}
- **Agent Categories**: {len(agent_inventory['categories'])}
- **Service Categories**: {len(service_inventory['categories'])}

## Agent Architecture Breakdown
"""
        
        for category, data in agent_inventory['categories'].items():
            summary += f"\n### {category.title()} Agents ({data['count']})\n"
            for agent in data['agents']:
                summary += f"- **{agent['name']}**: {agent.get('description', 'No description')}\n"
        
        summary += f"\n## Service Architecture Breakdown\n"
        
        for category, data in service_inventory['categories'].items():
            summary += f"\n### {category.replace('_', ' ').title()} ({data['count']} services)\n"
            summary += f"Services in `fs_agt_clean/services/{category}/`\n"
        
        summary += f"""
## Architecture Complexity Justification

The sophisticated architecture with {agent_inventory['total_agents']} agents and {service_inventory['total_services']} services 
is INTENTIONAL and serves legitimate enterprise e-commerce automation requirements:

1. **Multi-Agent Coordination**: Each agent specializes in specific business functions
2. **Microservices Design**: Services enable independent scaling and maintenance
3. **Enterprise Scale**: Supports complex marketplace operations and integrations
4. **Extensibility**: Architecture allows for easy addition of new capabilities

This complexity is NOT over-engineering but rather a necessary foundation for 
comprehensive e-commerce automation at enterprise scale.
"""
        
        return summary
    
    def save_documentation(self, filename: str, content: str):
        """Save documentation to file"""
        with open(filename, 'w') as f:
            f.write(content)
        print(f"✅ Documentation saved to {filename}")
    
    def generate_all_docs(self):
        """Generate all documentation files"""
        print("🔄 Generating FlipSync architecture documentation...")
        
        # Generate architecture summary
        summary = self.generate_architecture_summary()
        self.save_documentation("ARCHITECTURE_SUMMARY.md", summary)
        
        # Generate agent inventory JSON
        agent_inventory = self.generate_agent_inventory()
        with open("agent_inventory.json", 'w') as f:
            json.dump(agent_inventory, f, indent=2)
        print("✅ Agent inventory saved to agent_inventory.json")
        
        # Generate service inventory JSON
        service_inventory = self.generate_service_inventory()
        with open("service_inventory.json", 'w') as f:
            json.dump(service_inventory, f, indent=2)
        print("✅ Service inventory saved to service_inventory.json")
        
        print("\n🎉 Documentation generation complete!")
        print("\nGenerated files:")
        print("- ARCHITECTURE_SUMMARY.md")
        print("- agent_inventory.json")
        print("- service_inventory.json")

def main():
    """Main function for CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description="FlipSync Documentation Generator")
    parser.add_argument("--generate", action="store_true", help="Generate all documentation")
    parser.add_argument("--agents", action="store_true", help="Generate agent inventory only")
    parser.add_argument("--services", action="store_true", help="Generate service inventory only")
    parser.add_argument("--summary", action="store_true", help="Generate architecture summary only")
    
    args = parser.parse_args()
    generator = DocumentationGenerator()
    
    if args.generate:
        generator.generate_all_docs()
    elif args.agents:
        inventory = generator.generate_agent_inventory()
        print(json.dumps(inventory, indent=2))
    elif args.services:
        inventory = generator.generate_service_inventory()
        print(json.dumps(inventory, indent=2))
    elif args.summary:
        summary = generator.generate_architecture_summary()
        print(summary)
    else:
        generator.generate_all_docs()

if __name__ == "__main__":
    main()
