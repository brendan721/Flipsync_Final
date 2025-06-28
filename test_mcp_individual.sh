#!/bin/bash

# FlipSync MCP Servers Individual Test Script
# Tests each MCP server individually to verify they can start

echo "🚀 FlipSync MCP Servers Individual Test"
echo "========================================"

# Function to test MCP server startup
test_mcp_server() {
    local server_name="$1"
    local command="$2"
    local timeout=10
    
    echo -n "Testing $server_name: "
    
    # Start the server in background and capture PID
    timeout $timeout bash -c "$command" > /tmp/mcp_test_${server_name}.log 2>&1 &
    local pid=$!
    
    # Wait a moment for startup
    sleep 2
    
    # Check if process is still running
    if kill -0 $pid 2>/dev/null; then
        echo "✅ STARTED"
        kill $pid 2>/dev/null
        return 0
    else
        echo "❌ FAILED"
        echo "  Error log:"
        cat /tmp/mcp_test_${server_name}.log | head -3 | sed 's/^/    /'
        return 1
    fi
}

# Test each MCP server
echo ""
echo "🛠️ Testing MCP Server Startup..."

# 1. Filesystem Server
test_mcp_server "filesystem" "npx -y @modelcontextprotocol/server-filesystem /root/projects/flipsync/fs_clean"

# 2. GitHub Server (requires GITHUB_TOKEN)
if [ -n "$GITHUB_TOKEN" ]; then
    GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_TOKEN" test_mcp_server "github" "npx -y @modelcontextprotocol/server-github"
else
    echo "Testing github: ⚠️ SKIPPED (no GITHUB_TOKEN)"
fi

# 3. Web Search Server
test_mcp_server "web-search" "npx -y @modelcontextprotocol/server-web-search"

# 4. Sequential Thinking Server
test_mcp_server "sequential-thinking" "npx -y @modelcontextprotocol/server-sequential-thinking"

# 5. Memory Server
test_mcp_server "memory" "npx -y @modelcontextprotocol/server-memory"

# 6. PostgreSQL Server
test_mcp_server "postgresql" "npx -y @modelcontextprotocol/server-postgres postgresql://postgres:postgres@localhost:1432/flipsync_ai_tools"

# 7. SQLite Server
test_mcp_server "sqlite" "npx -y @modelcontextprotocol/server-sqlite /root/projects/flipsync/fs_clean/flipsync_ai_tools.db"

# 8. Perplexity Server
cd /root/projects/flipsync/perplexity-mcp-zerver
test_mcp_server "perplexity" "node build/index.js"
cd - > /dev/null

echo ""
echo "📊 Test Summary"
echo "==============="

# Count successful tests
success_count=0
total_count=8

# Check log files for success indicators
for server in filesystem github web-search sequential-thinking memory postgresql sqlite perplexity; do
    if [ -f "/tmp/mcp_test_${server}.log" ]; then
        # Check if the log indicates successful startup (no immediate errors)
        if ! grep -q "Error\|error\|ERROR\|Failed\|failed\|FAILED" /tmp/mcp_test_${server}.log 2>/dev/null; then
            ((success_count++))
        fi
    fi
done

echo "Servers tested: $total_count"
echo "Servers started successfully: $success_count"

if [ $success_count -ge 6 ]; then
    echo "✅ MCP Servers Status: READY FOR DEVELOPMENT"
    echo ""
    echo "🎯 Next Steps:"
    echo "  1. Configure your IDE to use the MCP servers"
    echo "  2. Test the servers with actual MCP client"
    echo "  3. Begin FlipSync development work"
else
    echo "⚠️ MCP Servers Status: NEEDS ATTENTION"
    echo ""
    echo "🔧 Troubleshooting:"
    echo "  - Check individual server logs in /tmp/mcp_test_*.log"
    echo "  - Verify all dependencies are installed"
    echo "  - Check database connectivity"
fi

# Cleanup
rm -f /tmp/mcp_test_*.log

echo ""
echo "🏁 Test Complete"
