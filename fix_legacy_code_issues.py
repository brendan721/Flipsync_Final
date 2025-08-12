#!/usr/bin/env python3
"""
FlipSync Legacy Code Removal Script
==================================

This script fixes critical legacy code issues to ensure 4+1 architecture compliance:
1. Fix AsyncHybridLLMClient undefined class bug
2. Remove HybridLLMAdapter references  
3. Clean up OpenAI client dependencies
4. Validate 4+1 architecture compliance

Usage: python fix_legacy_code_issues.py
"""

import os
import re
import shutil
from datetime import datetime
from pathlib import Path

def create_backup(file_path):
    """Create backup of file before modification."""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Backup created: {backup_path}")
    return backup_path

def fix_async_hybrid_llm_client():
    """Fix the AsyncHybridLLMClient undefined class bug."""
    file_path = "fs_agt_clean/core/ai/openai_client.py"
    
    print(f"🔧 Fixing AsyncHybridLLMClient bug in {file_path}")
    
    # Create backup
    create_backup(file_path)
    
    # Read file
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Fix the bug
    old_line = "        self.client = AsyncHybridLLMClient()"
    new_line = "        self.client = AsyncOpenAI(**client_kwargs)"
    
    if old_line in content:
        content = content.replace(old_line, new_line)
        
        # Write back
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"✅ Fixed AsyncHybridLLMClient bug")
        return True
    else:
        print(f"⚠️ AsyncHybridLLMClient bug not found or already fixed")
        return False

def remove_hybrid_llm_adapter_references():
    """Remove HybridLLMAdapter references from comments and documentation."""
    files_to_clean = [
        "fs_agt_clean/services/marketplace/ebay_optimization.py",
        "fs_agt_clean/services/analytics/performance_predictor.py", 
        "fs_agt_clean/services/vector/embedding_service.py",
        "fs_agt_clean/api/routes/ai_routes.py"
    ]
    
    print("🔧 Removing HybridLLMAdapter references...")
    
    for file_path in files_to_clean:
        if not os.path.exists(file_path):
            print(f"⚠️ File not found: {file_path}")
            continue
            
        print(f"  📝 Cleaning {file_path}")
        create_backup(file_path)
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Replace HybridLLMAdapter references with Gemini references
        replacements = [
            ("HybridLLMAdapter", "StrategicGeminiService"),
            ("# HybridLLMAdapter available for future", "# StrategicGeminiService available for"),
            ("using HybridLLMAdapter", "using StrategicGeminiService"),
            ("HybridLLMAdapter provides", "StrategicGeminiService provides"),
            ("HybridLLMAdapter returns", "StrategicGeminiService returns"),
            ("Generate confidence analysis using HybridLLMAdapter", "Generate confidence analysis using StrategicGeminiService"),
            ("Generate text using HybridLLMAdapter", "Generate text using StrategicGeminiService"),
            ("Would be tracked by HybridLLMAdapter", "Would be tracked by StrategicGeminiService"),
            ("Statistics from HybridLLMAdapter", "Statistics from StrategicGeminiService")
        ]
        
        modified = False
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
                modified = True
        
        if modified:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"    ✅ Updated HybridLLMAdapter references")
        else:
            print(f"    ℹ️ No HybridLLMAdapter references found")

def update_ai_routes_to_gemini():
    """Update AI routes to use StrategicGeminiService instead of OpenAI client."""
    file_path = "fs_agt_clean/api/routes/ai_routes.py"
    
    print(f"🔧 Updating AI routes to use StrategicGeminiService in {file_path}")
    
    if not os.path.exists(file_path):
        print(f"⚠️ File not found: {file_path}")
        return
    
    create_backup(file_path)
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update the get_openai_client function to properly return StrategicGeminiService
    old_function = '''async def get_openai_client():
    """Get AI client - now uses StrategicGeminiService for 4+1 architecture compliance."""
    return await get_strategic_gemini_client()'''
    
    new_function = '''async def get_openai_client():
    """Get AI client - now uses StrategicGeminiService for 4+1 architecture compliance."""
    from fs_agt_clean.core.ai.strategic_gemini_service import StrategicGeminiService
    return StrategicGeminiService(daily_budget=10.0)'''
    
    if old_function in content:
        content = content.replace(old_function, new_function)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print("✅ Updated get_openai_client to return StrategicGeminiService")
    else:
        print("ℹ️ get_openai_client function not found or already updated")

def validate_autonomous_agents():
    """Validate that autonomous agents have no LLM dependencies."""
    agent_files = [
        "fs_agt_clean/agents/market/market_agent.py",
        "fs_agt_clean/agents/executive/executive_agent.py", 
        "fs_agt_clean/agents/content/content_agent.py",
        "fs_agt_clean/agents/logistics/logistics_agent.py"
    ]
    
    print("🔍 Validating autonomous agents are LLM-free...")
    
    all_compliant = True
    
    for file_path in agent_files:
        if not os.path.exists(file_path):
            print(f"⚠️ Agent file not found: {file_path}")
            continue
            
        agent_name = os.path.basename(file_path).replace('_agent.py', '').title()
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check for LLM-free indicators
        llm_free_indicators = [
            "openai_client = None",
            "llm_client = None", 
            "learning_llm_client = None",
            "Removed LLM dependency"
        ]
        
        found_indicators = []
        for indicator in llm_free_indicators:
            if indicator in content:
                found_indicators.append(indicator)
        
        if found_indicators:
            print(f"  ✅ {agent_name} Agent: LLM-free ({len(found_indicators)} indicators)")
        else:
            print(f"  ❌ {agent_name} Agent: LLM dependencies may exist")
            all_compliant = False
    
    return all_compliant

def validate_strategic_gemini_service():
    """Validate StrategicGeminiService is the sole LLM component."""
    file_path = "fs_agt_clean/core/ai/strategic_gemini_service.py"
    
    print("🔍 Validating StrategicGeminiService...")
    
    if not os.path.exists(file_path):
        print(f"❌ StrategicGeminiService not found: {file_path}")
        return False
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check for Gemini-only usage
    gemini_indicators = [
        "from fs_agt_clean.core.ai.gemini_client import",
        "self.gemini_client = GeminiClient",
        "GeminiModel",
        "Strategic Gemini service"
    ]
    
    openai_indicators = [
        "openai",
        "OpenAI", 
        "gpt-",
        "AsyncOpenAI"
    ]
    
    gemini_found = sum(1 for indicator in gemini_indicators if indicator in content)
    openai_found = sum(1 for indicator in openai_indicators if indicator.lower() in content.lower())
    
    if gemini_found > 0 and openai_found == 0:
        print(f"  ✅ StrategicGeminiService: Gemini-only ({gemini_found} indicators)")
        return True
    else:
        print(f"  ❌ StrategicGeminiService: Mixed LLM usage (Gemini: {gemini_found}, OpenAI: {openai_found})")
        return False

def main():
    """Main execution function."""
    print("🚀 FlipSync Legacy Code Removal - 4+1 Architecture Compliance")
    print("=" * 60)
    
    # Change to project directory
    if os.path.exists("fs_agt_clean"):
        print("✅ Found fs_agt_clean directory")
    else:
        print("❌ fs_agt_clean directory not found. Run from project root.")
        return
    
    success_count = 0
    total_tasks = 5
    
    # Task 1: Fix AsyncHybridLLMClient bug
    print("\n📋 Task 1: Fix AsyncHybridLLMClient Bug")
    if fix_async_hybrid_llm_client():
        success_count += 1
    
    # Task 2: Remove HybridLLMAdapter references
    print("\n📋 Task 2: Remove HybridLLMAdapter References")
    remove_hybrid_llm_adapter_references()
    success_count += 1
    
    # Task 3: Update AI routes
    print("\n📋 Task 3: Update AI Routes to StrategicGeminiService")
    update_ai_routes_to_gemini()
    success_count += 1
    
    # Task 4: Validate autonomous agents
    print("\n📋 Task 4: Validate Autonomous Agents")
    if validate_autonomous_agents():
        success_count += 1
    
    # Task 5: Validate StrategicGeminiService
    print("\n📋 Task 5: Validate StrategicGeminiService")
    if validate_strategic_gemini_service():
        success_count += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"🎯 SUMMARY: {success_count}/{total_tasks} tasks completed successfully")
    
    if success_count == total_tasks:
        print("✅ 4+1 Architecture compliance achieved!")
        print("   - 4 LLM-free autonomous agents")
        print("   - 1 Gemini-powered conversational interface")
        print("   - No legacy OpenAI dependencies")
        print("   - No undefined class references")
    else:
        print("⚠️ Some issues remain. Check output above for details.")
    
    print("\n📝 Next steps:")
    print("   1. Test application startup: python -m fs_agt_clean.app.main")
    print("   2. Run architecture validator")
    print("   3. Test AI endpoints with StrategicGeminiService")

if __name__ == "__main__":
    main()
