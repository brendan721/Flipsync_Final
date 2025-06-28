#!/bin/bash
echo "=== Baseline Validation ==="

# Check architecture documentation exists
if [ -f "FLIPSYNC_ARCHITECTURE_BASELINE.md" ]; then
    echo "✅ Architecture baseline documented"
else
    echo "❌ Missing architecture baseline"
    exit 1
fi

# Check tool configurations exist
if [ -f "pyproject.toml" ] && [ -f ".vulture" ] && [ -f ".flake8" ]; then
    echo "✅ All tool configurations created"
else
    echo "❌ Missing tool configurations"
    exit 1
fi

# Check baseline metrics collected
if [ -f "BASELINE_METRICS.txt" ]; then
    echo "✅ Baseline metrics collected"
else
    echo "❌ Missing baseline metrics"
    exit 1
fi

# Check Python linting tools are installed
if command -v black &> /dev/null && command -v flake8 &> /dev/null && command -v vulture &> /dev/null; then
    echo "✅ Python linting tools installed"
else
    echo "❌ Missing Python linting tools"
    exit 1
fi

echo "✅ Phase 0 Complete - Ready for cleanup phases"
