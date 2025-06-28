#!/bin/bash
echo "=== FlipSync Baseline Metrics Collection ==="
echo "Date: $(date)"
echo ""

echo "=== Python Codebase Analysis ==="
echo "Total Python files:"
find fs_agt_clean/ -name "*.py" | wc -l

echo "Lines of Python code:"
find fs_agt_clean/ -name "*.py" -exec wc -l {} + | tail -1

echo "=== Agent Architecture Verification ==="
echo "Agent files found:"
find fs_agt_clean/agents/ -name "*agent*.py" | wc -l

echo "Detailed agent count by category:"
echo "Executive agents:"
find fs_agt_clean/agents/executive/ -name "*agent*.py" | wc -l

echo "Market agents:"
find fs_agt_clean/agents/market/ -name "*agent*.py" | wc -l

echo "Content agents:"
find fs_agt_clean/agents/content/ -name "*agent*.py" | wc -l

echo "Logistics agents:"
find fs_agt_clean/agents/logistics/ -name "*agent*.py" | wc -l

echo "Automation agents:"
find fs_agt_clean/agents/automation/ -name "*agent*.py" | wc -l

echo "Conversational agents:"
find fs_agt_clean/agents/conversational/ -name "*agent*.py" | wc -l

echo "Service files found:"
find fs_agt_clean/services/ -name "*.py" | grep -v __init__ | wc -l

echo "Database models found:"
find fs_agt_clean/database/models/ -name "*.py" 2>/dev/null | grep -v __init__ | wc -l || echo "0"

echo "API route modules found:"
find fs_agt_clean/api/routes/ -name "*.py" 2>/dev/null | grep -v __init__ | wc -l || echo "0"

echo "=== Flutter/Dart Codebase Analysis ==="
echo "Total Dart files:"
find mobile/ -name "*.dart" 2>/dev/null | wc -l || echo "0"

echo "Lines of Dart code:"
find mobile/ -name "*.dart" -exec wc -l {} + 2>/dev/null | tail -1 || echo "0 total"

echo ""
echo "=== Baseline Collection Complete ==="
