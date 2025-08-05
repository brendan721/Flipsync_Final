#!/usr/bin/env python3
"""
Test Agent Import Issues
========================

This script tests the specific import issues with autonomous agents.
"""

import sys
import os

# Add the current directory to Python path
sys.path.insert(0, '/home/brend/Flipsync_Final')

def test_agent_imports():
    """Test importing each autonomous agent class."""
    
    print("🔍 TESTING AGENT IMPORTS")
    print("=" * 50)
    
    agents_to_test = [
        ("Market", "fs_agt_clean.agents.market.market_agent", "MarketAutonomousAgent"),
        ("Content", "fs_agt_clean.agents.content.content_agent", "ContentAutonomousAgent"),
        ("Executive", "fs_agt_clean.agents.executive.executive_agent", "ExecutiveAutonomousAgent"),
        ("Logistics", "fs_agt_clean.agents.logistics.logistics_agent", "LogisticsAutonomousAgent"),
    ]
    
    successful_imports = []
    failed_imports = []
    
    for agent_name, module_path, class_name in agents_to_test:
        print(f"\n🤖 Testing {agent_name} Agent import...")
        print(f"   Module: {module_path}")
        print(f"   Class: {class_name}")
        
        try:
            # Test module import
            print(f"   📦 Importing module...")
            module = __import__(module_path, fromlist=[class_name])
            print(f"   ✅ Module imported successfully")
            
            # Test class import
            print(f"   🏗️ Getting class...")
            agent_class = getattr(module, class_name)
            print(f"   ✅ Class imported successfully: {agent_class}")
            
            # Test class inspection
            print(f"   🔍 Inspecting class...")
            print(f"      Base classes: {[base.__name__ for base in agent_class.__bases__]}")
            print(f"      Has __init__: {hasattr(agent_class, '__init__')}")
            print(f"      Has create: {hasattr(agent_class, 'create')}")
            
            successful_imports.append(agent_name)
            
        except ImportError as e:
            print(f"   ❌ Import failed: {e}")
            failed_imports.append((agent_name, f"ImportError: {e}"))
            
        except AttributeError as e:
            print(f"   ❌ Class not found: {e}")
            failed_imports.append((agent_name, f"AttributeError: {e}"))
            
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
            failed_imports.append((agent_name, f"Unexpected: {e}"))
    
    # Summary
    print(f"\n🎯 IMPORT TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Successful imports: {len(successful_imports)}")
    for agent in successful_imports:
        print(f"   - {agent}")
    
    print(f"❌ Failed imports: {len(failed_imports)}")
    for agent, error in failed_imports:
        print(f"   - {agent}: {error}")
    
    return len(failed_imports) == 0

def test_base_agent_import():
    """Test importing the base autonomous agent."""
    
    print(f"\n🔍 TESTING BASE AGENT IMPORT")
    print("=" * 50)
    
    try:
        from fs_agt_clean.agents.base_autonomous_agent import BaseAutonomousAgent
        print("✅ BaseAutonomousAgent imported successfully")
        print(f"   Class: {BaseAutonomousAgent}")
        print(f"   Has create: {hasattr(BaseAutonomousAgent, 'create')}")
        return True
    except Exception as e:
        print(f"❌ BaseAutonomousAgent import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_python_path():
    """Test Python path and module discovery."""
    
    print(f"\n🔍 TESTING PYTHON PATH")
    print("=" * 50)
    
    print("📊 Python path:")
    for i, path in enumerate(sys.path):
        print(f"   {i}: {path}")
    
    print(f"\n📊 Current working directory: {os.getcwd()}")
    
    # Test if fs_agt_clean is discoverable
    try:
        import fs_agt_clean
        print(f"✅ fs_agt_clean module found at: {fs_agt_clean.__file__}")
    except ImportError as e:
        print(f"❌ fs_agt_clean module not found: {e}")
        return False
    
    # Test if agents submodule is discoverable
    try:
        import fs_agt_clean.agents
        print(f"✅ fs_agt_clean.agents module found")
    except ImportError as e:
        print(f"❌ fs_agt_clean.agents module not found: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚨 INVESTIGATING AGENT IMPORT PROBLEMS")
    print("=" * 80)
    
    # Test Python path
    path_ok = test_python_path()
    
    if not path_ok:
        print("❌ Python path issues detected - cannot proceed")
        sys.exit(1)
    
    # Test base agent import
    base_ok = test_base_agent_import()
    
    if not base_ok:
        print("❌ Base agent import failed - cannot proceed")
        sys.exit(1)
    
    # Test individual agent imports
    imports_ok = test_agent_imports()
    
    if imports_ok:
        print("\n🎉 ALL AGENT IMPORTS SUCCESSFUL!")
        print("The import issue is resolved - agents should initialize properly")
    else:
        print("\n❌ AGENT IMPORT ISSUES REMAIN")
        print("Need to fix the remaining import problems")
    
    sys.exit(0 if imports_ok else 1)
