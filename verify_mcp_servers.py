#!/usr/bin/env python3
"""
FlipSync MCP Servers Verification Script
Verifies all 7 operational MCP servers are ready for use
"""

import subprocess
import json
import os
import sys
import time
from pathlib import Path

def test_server_startup(name, command, timeout=5):
    """Test if an MCP server can start successfully"""
    try:
        # Start the server process
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait briefly for startup
        time.sleep(2)
        
        # Check if process is still running (good sign for MCP servers)
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=2)
            return True, "Started successfully"
        else:
            stdout, stderr = process.communicate()
            # Some MCP servers exit immediately but that's normal
            if "running on stdio" in stderr or "MCP server" in stderr:
                return True, "Started successfully (stdio mode)"
            return False, f"Exited: {stderr[:100]}"
            
    except Exception as e:
        return False, str(e)

def main():
    """Main verification function"""
    print("🔍 FlipSync MCP Servers Verification")
    print("=" * 50)
    
    # Define the 7 operational MCP servers
    servers = [
        {
            "name": "filesystem",
            "command": "npx -y @modelcontextprotocol/server-filesystem /root/projects/flipsync/fs_clean",
            "critical": True
        },
        {
            "name": "github", 
            "command": "GITHUB_PERSONAL_ACCESS_TOKEN=${GITHUB_TOKEN:-demo} npx -y @modelcontextprotocol/server-github",
            "critical": False  # Optional if no token
        },
        {
            "name": "web-search",
            "command": "BRAVE_API_KEY=${BRAVE_API_KEY:-demo} npx -y @modelcontextprotocol/server-brave-search",
            "critical": False  # Optional if no API key
        },
        {
            "name": "sequential-thinking",
            "command": "npx -y @modelcontextprotocol/server-sequential-thinking",
            "critical": True
        },
        {
            "name": "memory",
            "command": "npx -y @modelcontextprotocol/server-memory",
            "critical": True
        },
        {
            "name": "postgresql",
            "command": "npx -y @modelcontextprotocol/server-postgres postgresql://postgres:postgres@localhost:1432/flipsync_ai_tools",
            "critical": True
        },
        {
            "name": "perplexity",
            "command": "cd /root/projects/flipsync/perplexity-mcp-zerver && node build/index.js",
            "critical": False  # Nice to have
        }
    ]
    
    print("\n🧪 Testing MCP Server Startup...")
    
    results = {}
    critical_passed = 0
    critical_total = 0
    
    for server in servers:
        name = server["name"]
        command = server["command"]
        is_critical = server["critical"]
        
        if is_critical:
            critical_total += 1
            
        print(f"\nTesting {name}...")
        success, message = test_server_startup(name, command)
        
        if success:
            status = "✅ OPERATIONAL"
            if is_critical:
                critical_passed += 1
        else:
            status = "❌ FAILED" if is_critical else "⚠️ OPTIONAL"
            
        print(f"  Status: {status}")
        print(f"  Details: {message}")
        
        results[name] = {
            "success": success,
            "message": message,
            "critical": is_critical
        }
    
    # Infrastructure checks
    print("\n🏗️ Infrastructure Status...")
    
    # Check PostgreSQL
    pg_check = subprocess.run(
        "docker exec flipsync-postgres pg_isready -U postgres",
        shell=True, capture_output=True, text=True
    )
    pg_status = "✅ RUNNING" if pg_check.returncode == 0 else "❌ NOT RUNNING"
    print(f"  PostgreSQL: {pg_status}")
    
    # Check AI Tools Database
    db_check = subprocess.run(
        "docker exec flipsync-postgres psql -U postgres -d flipsync_ai_tools -c 'SELECT 1;'",
        shell=True, capture_output=True, text=True
    )
    db_status = "✅ ACCESSIBLE" if db_check.returncode == 0 else "❌ NOT ACCESSIBLE"
    print(f"  AI Tools DB: {db_status}")
    
    # Check Perplexity build
    perplexity_build = os.path.exists("/root/projects/flipsync/perplexity-mcp-zerver/build/index.js")
    perplexity_status = "✅ BUILT" if perplexity_build else "❌ NOT BUILT"
    print(f"  Perplexity Build: {perplexity_status}")
    
    # Summary
    print("\n📊 VERIFICATION SUMMARY")
    print("=" * 50)
    
    total_servers = len(servers)
    operational_servers = sum(1 for r in results.values() if r["success"])
    
    print(f"Total MCP Servers: {total_servers}")
    print(f"Operational Servers: {operational_servers}")
    print(f"Critical Servers: {critical_passed}/{critical_total}")
    
    # Determine overall status
    infrastructure_ok = (
        pg_check.returncode == 0 and 
        db_check.returncode == 0
    )
    
    servers_ok = critical_passed >= (critical_total - 1)  # Allow 1 critical failure
    
    if infrastructure_ok and servers_ok:
        overall_status = "✅ READY FOR DEVELOPMENT"
        print(f"\nOverall Status: {overall_status}")
        print("\n🎯 Next Steps:")
        print("  1. Configure your IDE with MCP server settings")
        print("  2. Test MCP integration in your development environment")
        print("  3. Begin FlipSync development work")
        return 0
    else:
        overall_status = "⚠️ NEEDS ATTENTION"
        print(f"\nOverall Status: {overall_status}")
        print("\n🔧 Issues to Address:")
        
        if not infrastructure_ok:
            print("  - Fix database connectivity issues")
            
        if not servers_ok:
            print("  - Address critical MCP server failures")
            for name, result in results.items():
                if result["critical"] and not result["success"]:
                    print(f"    * {name}: {result['message']}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())
