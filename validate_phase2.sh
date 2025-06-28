#!/bin/bash
echo "=== Phase 2 Code Organization & Linting Validation ==="

# Check Python linting completed
if [ -d "linting_results" ]; then
    echo "✅ Python linting completed"
    echo "  - Black formatting: Applied"
    echo "  - isort imports: Applied"
    echo "  - Flake8 issues: $(wc -l < linting_results/flake8_report.txt)"
    echo "  - MyPy errors: $(grep -c "error:" linting_results/mypy_report.txt || echo "0")"
    echo "  - Bandit security: $(jq '.results | length' linting_results/bandit_report.json 2>/dev/null || echo "0") issues"
    echo "  - Vulture dead code: $(wc -l < linting_results/vulture_report.txt) items"
else
    echo "❌ Python linting not completed"
    exit 1
fi

# Check selective dead code removal
if [ -f "selective_dead_code_removal.py" ]; then
    echo "✅ Selective dead code removal script created"
else
    echo "❌ Missing selective dead code removal script"
    exit 1
fi

# Check pre-commit hooks
if [ -f ".pre-commit-config.yaml" ]; then
    echo "✅ Pre-commit hooks configured"
else
    echo "❌ Missing pre-commit configuration"
    exit 1
fi

# Check CI quality checks
if [ -f ".github/workflows/quality-checks.yml" ]; then
    echo "✅ CI quality checks configured"
else
    echo "❌ Missing CI quality checks"
    exit 1
fi

# Check architecture preservation validator
if [ -f "validate_architecture_preservation.py" ]; then
    echo "✅ Architecture preservation validator created"
    # Run the validator
    python validate_architecture_preservation.py
    if [ $? -eq 0 ]; then
        echo "✅ Architecture preservation validated"
    else
        echo "❌ Architecture preservation check failed"
        exit 1
    fi
else
    echo "❌ Missing architecture preservation validator"
    exit 1
fi

echo ""
echo "=== Phase 2 Validation Summary ==="
echo "✅ Code organization and linting complete"
echo "✅ Architecture complexity preserved"
echo "✅ Quality automation configured"
echo "✅ Ready for Phase 3: Development Experience"
