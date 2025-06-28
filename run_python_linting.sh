#!/bin/bash
echo "=== FlipSync Python Code Organization Phase ==="
echo "Date: $(date)"
echo ""

# Create linting results directory
mkdir -p linting_results

echo "=== Running Black (Code Formatting) ==="
black fs_agt_clean/ --check --diff > linting_results/black_report.txt 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Black formatting check passed"
else
    echo "⚠️  Black formatting issues found - see linting_results/black_report.txt"
    echo "Running Black auto-fix..."
    black fs_agt_clean/
    echo "✅ Black formatting applied"
fi

echo "=== Running isort (Import Organization) ==="
isort fs_agt_clean/ --check-only --diff > linting_results/isort_report.txt 2>&1
if [ $? -eq 0 ]; then
    echo "✅ Import organization check passed"
else
    echo "⚠️  Import organization issues found - see linting_results/isort_report.txt"
    echo "Running isort auto-fix..."
    isort fs_agt_clean/
    echo "✅ Import organization applied"
fi

echo "=== Running Flake8 (Style Guide Enforcement) ==="
flake8 fs_agt_clean/ > linting_results/flake8_report.txt 2>&1
flake8_issues=$(wc -l < linting_results/flake8_report.txt)
echo "Flake8 issues found: $flake8_issues"

echo "=== Running MyPy (Type Checking) ==="
mypy fs_agt_clean/ > linting_results/mypy_report.txt 2>&1
mypy_issues=$(grep -c "error:" linting_results/mypy_report.txt || echo "0")
echo "MyPy type errors found: $mypy_issues"

echo "=== Running Bandit (Security Analysis) ==="
bandit -r fs_agt_clean/ -f json -o linting_results/bandit_report.json > /dev/null 2>&1
bandit_issues=$(jq '.results | length' linting_results/bandit_report.json 2>/dev/null || echo "0")
echo "Bandit security issues found: $bandit_issues"

echo "=== Running Vulture (Dead Code Detection) ==="
vulture fs_agt_clean/ --min-confidence 80 > linting_results/vulture_report.txt 2>&1
vulture_issues=$(wc -l < linting_results/vulture_report.txt)
echo "Vulture dead code items found: $vulture_issues"

echo ""
echo "=== Python Linting Summary ==="
echo "Flake8 style issues: $flake8_issues"
echo "MyPy type errors: $mypy_issues"
echo "Bandit security issues: $bandit_issues"
echo "Vulture dead code items: $vulture_issues"
echo ""
echo "Detailed reports available in linting_results/ directory"
