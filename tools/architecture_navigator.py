#!/usr/bin/env python3
"""
FlipSync Architecture Navigator
Interactive tool for exploring the sophisticated 35+ agent architecture
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

class ArchitectureNavigator:
    """Interactive navigator for FlipSync's complex architecture"""
    
    def __init__(self):
        self.root_dir = Path(".")
        self.agents_dir = Path("fs_agt_clean/agents")
        self.services_dir = Path("fs_agt_clean/services")
        self.api_dir = Path("fs_agt_clean/api")
        self.db_dir = Path("fs_agt_clean/database")
        
    def show_main_menu(self):
        """Display the main navigation menu"""
        print("\n" + "="*60)
        print("🏗️  FlipSync Architecture Navigator")
        print("="*60)
        print("Explore the sophisticated enterprise-grade architecture")
        print("")
        print("1. 🤖 Agent Architecture (35+ Specialized Agents)")
        print("2. ⚙️  Service Layer (225+ Microservices)")
        print("3. 🗄️  Database Models (30+ Tables)")
        print("4. 🌐 API Routes (37+ Endpoints)")
        print("5. 📱 Mobile Architecture")
        print("6. 📊 Architecture Statistics")
        print("7. 🔍 Search Components")
        print("8. 📖 Documentation")
        print("9. ❌ Exit")
        print("")
        
    def explore_agents(self):
        """Explore the agent architecture"""
        print("\n🤖 Agent Architecture Explorer")
        print("-" * 40)
        
        categories = {
            "executive": "Strategic decision making and orchestration",
            "market": "Marketplace intelligence and operations", 
            "content": "Content generation and optimization",
            "logistics": "Shipping and warehouse management",
            "automation": "Automated business processes",
            "conversational": "Communication and interaction"
        }
        
        for i, (category, description) in enumerate(categories.items(), 1):
            category_path = self.agents_dir / category
            if category_path.exists():
                agent_count = len([f for f in category_path.glob("*agent*.py") 
                                if not f.name.startswith("test_")])
                print(f"{i}. {category.title()} ({agent_count} agents)")
                print(f"   {description}")
            else:
                print(f"{i}. {category.title()} (0 agents)")
                print(f"   {description}")
        
        print("\nEnter category number to explore (or 0 to return):")
        
    def explore_services(self):
        """Explore the service architecture"""
        print("\n⚙️  Service Architecture Explorer")
        print("-" * 40)
        
        service_categories = []
        for item in self.services_dir.iterdir():
            if item.is_dir() and not item.name.startswith('.'):
                service_count = len([f for f in item.rglob("*.py") 
                                   if not f.name.startswith("test_") and f.name != "__init__.py"])
                service_categories.append((item.name, service_count))
        
        service_categories.sort(key=lambda x: x[1], reverse=True)
        
        for i, (category, count) in enumerate(service_categories, 1):
            print(f"{i:2d}. {category.replace('_', ' ').title():<30} ({count:3d} services)")
        
        total_services = sum(count for _, count in service_categories)
        print(f"\nTotal Services: {total_services}")
        print("\nEnter category number to explore (or 0 to return):")
        
    def show_statistics(self):
        """Show architecture statistics"""
        print("\n📊 Architecture Statistics")
        print("-" * 40)
        
        # Count agents
        agent_count = 0
        for category_dir in self.agents_dir.iterdir():
            if category_dir.is_dir():
                agent_count += len([f for f in category_dir.glob("*agent*.py") 
                                  if not f.name.startswith("test_")])
        
        # Count services
        service_count = len([f for f in self.services_dir.rglob("*.py") 
                           if not f.name.startswith("test_") and f.name != "__init__.py"])
        
        # Count database models
        db_models = 0
        if self.db_dir.exists():
            models_dir = self.db_dir / "models"
            if models_dir.exists():
                db_models = len([f for f in models_dir.glob("*.py") 
                               if not f.name.startswith("test_") and f.name != "__init__.py"])
        
        # Count API routes
        api_routes = 0
        if self.api_dir.exists():
            routes_dir = self.api_dir / "routes"
            if routes_dir.exists():
                api_routes = len([f for f in routes_dir.rglob("*.py") 
                                if not f.name.startswith("test_") and f.name != "__init__.py"])
        
        # Count mobile files
        mobile_files = 0
        mobile_dir = Path("mobile")
        if mobile_dir.exists():
            mobile_files = len(list(mobile_dir.rglob("*.dart")))
        
        print(f"🤖 Specialized Agents:     {agent_count:3d}")
        print(f"⚙️  Microservices:         {service_count:3d}")
        print(f"🗄️  Database Models:       {db_models:3d}")
        print(f"🌐 API Route Modules:     {api_routes:3d}")
        print(f"📱 Mobile Dart Files:     {mobile_files:3d}")
        print("")
        print("This complexity is INTENTIONAL and serves legitimate")
        print("enterprise e-commerce automation requirements.")
        
    def search_components(self):
        """Search for specific components"""
        print("\n🔍 Component Search")
        print("-" * 40)
        search_term = input("Enter search term: ").strip().lower()
        
        if not search_term:
            return
            
        results = []
        
        # Search in agents
        for agent_file in self.agents_dir.rglob("*.py"):
            if search_term in agent_file.name.lower():
                results.append(("Agent", str(agent_file)))
        
        # Search in services
        for service_file in self.services_dir.rglob("*.py"):
            if search_term in service_file.name.lower():
                results.append(("Service", str(service_file)))
        
        if results:
            print(f"\nFound {len(results)} matches:")
            for i, (component_type, path) in enumerate(results, 1):
                print(f"{i:2d}. {component_type:<8} {path}")
        else:
            print(f"\nNo components found matching '{search_term}'")
        
    def show_documentation(self):
        """Show available documentation"""
        print("\n📖 Architecture Documentation")
        print("-" * 40)
        
        docs = [
            ("COMPREHENSIVE_ARCHITECTURE_GUIDE.md", "Complete architecture overview"),
            ("SERVICE_INTERDEPENDENCY_MAP.md", "Service relationships and dependencies"),
            ("AGENT_WRAPPER_PATTERN_GUIDE.md", "AI wrapper pattern explanation"),
            ("DEVELOPER_ARCHITECTURE_PRIMER.md", "Developer onboarding guide"),
            ("FLIPSYNC_ARCHITECTURE_BASELINE.md", "Architecture preservation reference")
        ]
        
        for i, (doc, description) in enumerate(docs, 1):
            if Path(doc).exists():
                print(f"{i}. ✅ {doc}")
                print(f"   {description}")
            else:
                print(f"{i}. ❌ {doc} (missing)")
                print(f"   {description}")
        
    def run(self):
        """Run the interactive navigator"""
        while True:
            self.show_main_menu()
            try:
                choice = input("Select option (1-9): ").strip()
                
                if choice == "1":
                    self.explore_agents()
                elif choice == "2":
                    self.explore_services()
                elif choice == "3":
                    print("\n🗄️  Database Models - See fs_agt_clean/database/models/")
                elif choice == "4":
                    print("\n🌐 API Routes - See fs_agt_clean/api/routes/")
                elif choice == "5":
                    print("\n📱 Mobile Architecture - See mobile/ directory")
                elif choice == "6":
                    self.show_statistics()
                elif choice == "7":
                    self.search_components()
                elif choice == "8":
                    self.show_documentation()
                elif choice == "9":
                    print("\nExiting FlipSync Architecture Navigator")
                    break
                else:
                    print("\nInvalid choice. Please select 1-9.")
                    
                if choice in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                    input("\nPress Enter to continue...")
                    
            except KeyboardInterrupt:
                print("\n\nExiting FlipSync Architecture Navigator")
                break
            except Exception as e:
                print(f"\nError: {e}")
                input("Press Enter to continue...")

if __name__ == "__main__":
    navigator = ArchitectureNavigator()
    navigator.run()
