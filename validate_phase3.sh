#!/bin/bash
echo "=== Phase 3 Development Experience Improvements Validation ==="

# Check agent debugging tools
if [ -f "tools/agent_debugger.py" ] && [ -x "tools/agent_debugger.py" ]; then
    echo "✅ Agent debugging tool created and executable"
    # Test the tool
    python tools/agent_debugger.py --map > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Agent debugger functional"
    else
        echo "❌ Agent debugger not functional"
        exit 1
    fi
else
    echo "❌ Missing agent debugging tool"
    exit 1
fi

# Check development environment setup script
if [ -f "tools/dev_setup.sh" ] && [ -x "tools/dev_setup.sh" ]; then
    echo "✅ Development environment setup script created"
else
    echo "❌ Missing development environment setup script"
    exit 1
fi

# Check architecture navigation tool
if [ -f "tools/architecture_navigator.py" ] && [ -x "tools/architecture_navigator.py" ]; then
    echo "✅ Architecture navigation tool created and executable"
else
    echo "❌ Missing architecture navigation tool"
    exit 1
fi

# Check interactive documentation
if [ -f "tools/doc_generator.py" ] && [ -x "tools/doc_generator.py" ]; then
    echo "✅ Interactive documentation generator created"
    # Test documentation generation
    python tools/doc_generator.py --agents > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Documentation generator functional"
    else
        echo "❌ Documentation generator not functional"
        exit 1
    fi
else
    echo "❌ Missing interactive documentation generator"
    exit 1
fi

# Check development automation
if [ -f "tools/dev_automation.py" ] && [ -x "tools/dev_automation.py" ]; then
    echo "✅ Development automation tool created and executable"
    # Test validation function
    python tools/dev_automation.py --validate > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Development automation functional"
    else
        echo "❌ Development automation not functional"
        exit 1
    fi
else
    echo "❌ Missing development automation tool"
    exit 1
fi

# Check generated documentation files
if [ -f "ARCHITECTURE_SUMMARY.md" ]; then
    echo "✅ Architecture summary documentation generated"
else
    echo "❌ Missing architecture summary documentation"
    exit 1
fi

if [ -f "agent_inventory.json" ] && [ -f "service_inventory.json" ]; then
    echo "✅ Architecture inventory files generated"
else
    echo "❌ Missing architecture inventory files"
    exit 1
fi

# Verify architecture preservation
python validate_architecture_preservation.py > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Architecture preservation maintained throughout Phase 3"
else
    echo "❌ Architecture preservation compromised in Phase 3"
    exit 1
fi

echo ""
echo "=== Phase 3 Validation Summary ==="
echo "✅ Agent debugging tools implemented"
echo "✅ Development environment automation created"
echo "✅ Architecture navigation tools built"
echo "✅ Interactive documentation generated"
echo "✅ Development automation implemented"
echo "✅ Architecture complexity preserved"
echo "✅ Phase 3 Complete - All development experience improvements ready"
