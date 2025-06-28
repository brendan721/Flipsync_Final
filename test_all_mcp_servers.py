#!/usr/bin/env python3
"""
FlipSync MCP Servers Test Script
Tests all 8 MCP servers to verify operational status
"""

import subprocess
import json
import os
import sys
import time
from pathlib import Path

def run_command(cmd, timeout=10):
    """Run a command with timeout and return result"""
    try:
        result = subprocess.run(
            cmd, 
            shell=True, 
            capture_output=True, 
            text=True, 
            timeout=timeout
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout.strip(),
            'stderr': result.stderr.strip(),
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Command timed out after {timeout} seconds',
            'returncode': -1
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1
        }

def test_docker_services():
    """Test Docker services are running"""
    print("🐳 Testing Docker Services...")
    
    # Check PostgreSQL
    pg_result = run_command("docker exec flipsync-postgres pg_isready -U postgres")
    pg_status = "✅ RUNNING" if pg_result['success'] else "❌ NOT RUNNING"
    print(f"  PostgreSQL: {pg_status}")
    
    # Check Redis
    redis_result = run_command("docker exec flipsync-redis redis-cli ping")
    redis_status = "✅ RUNNING" if redis_result['success'] and "PONG" in redis_result['stdout'] else "❌ NOT RUNNING"
    print(f"  Redis: {redis_status}")
    
    return pg_result['success'] and redis_result['success']

def test_database_connectivity():
    """Test database connectivity"""
    print("\n🗄️ Testing Database Connectivity...")
    
    # Test FlipSync main database
    flipsync_result = run_command(
        "docker exec flipsync-postgres psql -U postgres -d flipsync -c 'SELECT 1;'"
    )
    flipsync_status = "✅ ACCESSIBLE" if flipsync_result['success'] else "❌ NOT ACCESSIBLE"
    print(f"  FlipSync Database: {flipsync_status}")
    
    # Test AI tools database
    ai_tools_result = run_command(
        "docker exec flipsync-postgres psql -U postgres -d flipsync_ai_tools -c 'SELECT COUNT(*) FROM agent_memory;'"
    )
    ai_tools_status = "✅ ACCESSIBLE" if ai_tools_result['success'] else "❌ NOT ACCESSIBLE"
    print(f"  AI Tools Database: {ai_tools_status}")
    
    # Test SQLite database
    sqlite_path = "/root/projects/flipsync/fs_clean/flipsync_ai_tools.db"
    sqlite_exists = os.path.exists(sqlite_path)
    sqlite_status = "✅ EXISTS" if sqlite_exists else "❌ NOT FOUND"
    print(f"  SQLite Database: {sqlite_status}")
    
    return flipsync_result['success'] and ai_tools_result['success'] and sqlite_exists

def test_node_dependencies():
    """Test Node.js and npm dependencies"""
    print("\n📦 Testing Node.js Dependencies...")
    
    # Check Node.js version
    node_result = run_command("node --version")
    node_status = "✅ AVAILABLE" if node_result['success'] else "❌ NOT AVAILABLE"
    print(f"  Node.js: {node_status} ({node_result['stdout'] if node_result['success'] else 'N/A'})")
    
    # Check npm version
    npm_result = run_command("npm --version")
    npm_status = "✅ AVAILABLE" if npm_result['success'] else "❌ NOT AVAILABLE"
    print(f"  npm: {npm_status} ({npm_result['stdout'] if npm_result['success'] else 'N/A'})")
    
    # Check npx availability
    npx_result = run_command("npx --version")
    npx_status = "✅ AVAILABLE" if npx_result['success'] else "❌ NOT AVAILABLE"
    print(f"  npx: {npx_status} ({npx_result['stdout'] if npx_result['success'] else 'N/A'})")
    
    return node_result['success'] and npm_result['success'] and npx_result['success']

def test_perplexity_server():
    """Test Perplexity MCP server build"""
    print("\n🔬 Testing Perplexity MCP Server...")
    
    perplexity_path = "/root/projects/flipsync/perplexity-mcp-zerver"
    build_path = f"{perplexity_path}/build/index.js"
    
    # Check if build exists
    build_exists = os.path.exists(build_path)
    build_status = "✅ BUILT" if build_exists else "❌ NOT BUILT"
    print(f"  Build Status: {build_status}")
    
    # Check package.json
    package_json_path = f"{perplexity_path}/package.json"
    package_exists = os.path.exists(package_json_path)
    package_status = "✅ EXISTS" if package_exists else "❌ NOT FOUND"
    print(f"  Package.json: {package_status}")
    
    # Check node_modules
    node_modules_path = f"{perplexity_path}/node_modules"
    modules_exist = os.path.exists(node_modules_path)
    modules_status = "✅ INSTALLED" if modules_exist else "❌ NOT INSTALLED"
    print(f"  Dependencies: {modules_status}")
    
    return build_exists and package_exists and modules_exist

def test_mcp_server_commands():
    """Test MCP server command availability"""
    print("\n🛠️ Testing MCP Server Commands...")
    
    servers_to_test = [
        ("filesystem", "npx -y @modelcontextprotocol/server-filesystem --help"),
        ("github", "npx -y @modelcontextprotocol/server-github --help"),
        ("web-search", "npx -y @modelcontextprotocol/server-web-search --help"),
        ("sequential-thinking", "npx -y @modelcontextprotocol/server-sequential-thinking --help"),
        ("memory", "npx -y @modelcontextprotocol/server-memory --help"),
        ("postgres", "npx -y @modelcontextprotocol/server-postgres --help"),
        ("sqlite", "npx -y @modelcontextprotocol/server-sqlite --help"),
    ]
    
    results = {}
    for server_name, command in servers_to_test:
        result = run_command(command, timeout=30)
        # For MCP servers, help command might return non-zero but still work
        # Check if stderr contains help info or if it's a known MCP server response
        is_available = (
            result['success'] or 
            "Usage:" in result['stderr'] or 
            "Options:" in result['stderr'] or
            "database URL" in result['stderr'] or  # postgres server specific
            "directory path" in result['stderr']    # filesystem server specific
        )
        
        status = "✅ AVAILABLE" if is_available else "❌ NOT AVAILABLE"
        print(f"  {server_name}: {status}")
        results[server_name] = is_available
    
    return results

def main():
    """Main test function"""
    print("🚀 FlipSync MCP Servers Test Suite")
    print("=" * 50)
    
    # Test results
    test_results = {}
    
    # Test Docker services
    test_results['docker'] = test_docker_services()
    
    # Test database connectivity
    test_results['databases'] = test_database_connectivity()
    
    # Test Node.js dependencies
    test_results['node'] = test_node_dependencies()
    
    # Test Perplexity server
    test_results['perplexity'] = test_perplexity_server()
    
    # Test MCP server commands
    mcp_results = test_mcp_server_commands()
    test_results['mcp_servers'] = mcp_results
    
    # Summary
    print("\n📊 TEST SUMMARY")
    print("=" * 50)
    
    docker_status = "✅ PASS" if test_results['docker'] else "❌ FAIL"
    print(f"Docker Services: {docker_status}")
    
    db_status = "✅ PASS" if test_results['databases'] else "❌ FAIL"
    print(f"Database Connectivity: {db_status}")
    
    node_status = "✅ PASS" if test_results['node'] else "❌ FAIL"
    print(f"Node.js Dependencies: {node_status}")
    
    perplexity_status = "✅ PASS" if test_results['perplexity'] else "❌ FAIL"
    print(f"Perplexity Server: {perplexity_status}")
    
    # MCP Servers summary
    mcp_passed = sum(1 for v in mcp_results.values() if v)
    mcp_total = len(mcp_results)
    mcp_status = f"✅ {mcp_passed}/{mcp_total} AVAILABLE" if mcp_passed == mcp_total else f"⚠️ {mcp_passed}/{mcp_total} AVAILABLE"
    print(f"MCP Servers: {mcp_status}")
    
    # Overall status
    all_critical_pass = (
        test_results['docker'] and 
        test_results['databases'] and 
        test_results['node'] and
        mcp_passed >= 5  # At least 5 out of 7 MCP servers should work
    )
    
    overall_status = "✅ READY FOR DEVELOPMENT" if all_critical_pass else "❌ NEEDS ATTENTION"
    print(f"\nOverall Status: {overall_status}")
    
    if not all_critical_pass:
        print("\n🔧 RECOMMENDED ACTIONS:")
        if not test_results['docker']:
            print("  - Start Docker containers: docker-compose up -d")
        if not test_results['databases']:
            print("  - Check database setup and connectivity")
        if not test_results['node']:
            print("  - Install Node.js and npm")
        if mcp_passed < 5:
            print("  - Check MCP server installations")
    
    return 0 if all_critical_pass else 1

if __name__ == "__main__":
    sys.exit(main())
