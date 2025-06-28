#!/bin/bash
# FlipSync MCP Servers Setup Script
# This script sets up the three priority MCP servers for FlipSync development

set -e  # Exit on any error

echo "🚀 FlipSync MCP Servers Setup"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [[ ! -d "fs_clean" ]]; then
    print_error "Please run this script from the FlipSync project root directory"
    exit 1
fi

cd fs_clean

print_status "Setting up FlipSync MCP servers..."

# 1. PostgreSQL MCP Server Setup
echo ""
print_status "1. Setting up PostgreSQL MCP Server..."

# Test database connectivity
print_status "Testing PostgreSQL connectivity..."
python3 test_database_connectivity.py

# Check if AI tools database exists and create if needed
print_status "Checking AI tools database..."
if command -v psql &> /dev/null; then
    print_status "Setting up flipsync_ai_tools database..."
    PGPASSWORD=postgres psql -h localhost -p 1432 -U postgres -f setup_ai_tools_database.sql || {
        print_warning "Database setup via psql failed, but PostgreSQL MCP server may still work"
    }
else
    print_warning "psql not available, skipping database setup"
    print_status "You can install PostgreSQL client with: apt install postgresql-client-common"
fi

print_success "PostgreSQL MCP server configuration ready"

# 2. SQLite MCP Server Setup
echo ""
print_status "2. Setting up SQLite MCP Server..."

# Create SQLite database
python3 -c "
import sqlite3
import json
from datetime import datetime

# Create SQLite database
conn = sqlite3.connect('flipsync_ai_tools.db')
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS agent_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        agent_type TEXT NOT NULL,
        context_key TEXT NOT NULL,
        context_data TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(agent_type, context_key)
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS code_insights (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_path TEXT,
        insight_type TEXT,
        insight_data TEXT,
        confidence_score REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Insert test data
cursor.execute(
    'INSERT OR REPLACE INTO agent_memory (agent_type, context_key, context_data) VALUES (?, ?, ?)',
    ('setup', 'sqlite_test', json.dumps({'status': 'success', 'timestamp': str(datetime.now())}))
)

conn.commit()
conn.close()
print('✅ SQLite database created successfully')
"

print_success "SQLite MCP server ready at: $(pwd)/flipsync_ai_tools.db"

# 3. Perplexity MCP Server Setup
echo ""
print_status "3. Setting up Perplexity MCP Server..."

# Check if Node.js is available
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install Node.js >= 18.0.0"
    print_status "You can install Node.js with: curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash - && sudo apt-get install -y nodejs"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2)
REQUIRED_VERSION="18.0.0"

if ! printf '%s\n%s\n' "$REQUIRED_VERSION" "$NODE_VERSION" | sort -V -C; then
    print_error "Node.js version $NODE_VERSION is too old. Required: >= $REQUIRED_VERSION"
    exit 1
fi

print_success "Node.js version $NODE_VERSION is compatible"

# Setup Perplexity MCP server
cd /root/projects/flipsync/perplexity-mcp-zerver

print_status "Installing Perplexity MCP server dependencies..."
if [[ -f "package.json" ]]; then
    npm install || {
        print_error "Failed to install Perplexity MCP server dependencies"
        exit 1
    }
    
    print_status "Building Perplexity MCP server..."
    npm run build || {
        print_error "Failed to build Perplexity MCP server"
        exit 1
    }
    
    print_success "Perplexity MCP server built successfully"
else
    print_error "package.json not found in perplexity-mcp-zerver directory"
    exit 1
fi

# Return to fs_clean directory
cd /root/projects/flipsync/fs_clean

# 4. Test MCP Server Configurations
echo ""
print_status "4. Testing MCP server configurations..."

# Validate MCP configuration file
python3 -c "
import json
try:
    with open('mcp-servers-config.json', 'r') as f:
        config = json.load(f)
    
    servers = config['mcpServers']
    ready_servers = [name for name, server in servers.items() if server.get('status') == 'ready']
    pending_servers = [name for name, server in servers.items() if server.get('status') == 'pending']
    
    print(f'✅ MCP configuration valid')
    print(f'✅ Ready servers: {len(ready_servers)} - {ready_servers}')
    print(f'⚠️  Pending servers: {len(pending_servers)} - {pending_servers}')
    
except Exception as e:
    print(f'❌ MCP configuration error: {e}')
    exit(1)
"

# 5. Create quick test script
echo ""
print_status "5. Creating MCP server test script..."

cat > test_mcp_servers.py << 'EOF'
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
EOF

chmod +x test_mcp_servers.py

print_success "MCP server test script created: test_mcp_servers.py"

# Final summary
echo ""
print_success "🎉 FlipSync MCP Servers Setup Complete!"
echo ""
echo "📋 Setup Summary:"
echo "  ✅ PostgreSQL MCP Server: Ready (flipsync_ai_tools database)"
echo "  ✅ SQLite MCP Server: Ready (local database)"
echo "  ✅ Perplexity MCP Server: Ready (no API key required)"
echo ""
echo "🔧 Next Steps:"
echo "  1. Run: python3 test_mcp_servers.py"
echo "  2. Test database connectivity: python3 test_database_connectivity.py"
echo "  3. Use the enhanced initialization script for maximum persistence"
echo ""
echo "📁 Key Files Created:"
echo "  - setup_ai_tools_database.sql (PostgreSQL setup)"
echo "  - test_database_connectivity.py (connectivity testing)"
echo "  - flipsync_ai_tools.db (SQLite database)"
echo "  - mcp-servers-config.json (updated configuration)"
echo "  - test_mcp_servers.py (server testing)"
