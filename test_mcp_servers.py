#!/usr/bin/env python3
"""Quick test script for MCP servers."""

import subprocess
import json
import os

def test_mcp_server(server_name, config):
    """Test if an MCP server can be started."""
    print(f"Testing {server_name}...")
    
    if config.get('status') != 'ready':
        print(f"  ⚠️  {server_name} is not marked as ready")
        return False
    
    command = config.get('command')
    args = config.get('args', [])
    cwd = config.get('cwd', '.')
    
    if not command:
        print(f"  ❌ No command specified for {server_name}")
        return False
    
    try:
        # Test if command exists
        if command == 'node':
            subprocess.run(['node', '--version'], check=True, capture_output=True)
        elif command == 'python':
            subprocess.run(['python3', '--version'], check=True, capture_output=True)
        elif command == 'npx':
            subprocess.run(['npx', '--version'], check=True, capture_output=True)
        
        print(f"  ✅ {server_name} command available")
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print(f"  ❌ {server_name} command not available")
        return False

def main():
    """Test all MCP servers."""
    try:
        with open('mcp-servers-config.json', 'r') as f:
            config = json.load(f)
        
        servers = config['mcpServers']
        ready_count = 0
        
        for name, server_config in servers.items():
            if test_mcp_server(name, server_config):
                ready_count += 1
        
        print(f"\n📊 Summary: {ready_count}/{len(servers)} servers ready")
        
    except Exception as e:
        print(f"❌ Error testing MCP servers: {e}")

if __name__ == "__main__":
    main()
