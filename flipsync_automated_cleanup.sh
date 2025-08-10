#!/bin/bash
# FlipSync Automated Root Directory Cleanup Script
# Organizes 327 files scattered in root directory

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Count files before cleanup
count_files() {
    find . -maxdepth 1 -type f | wc -l
}

log "🧹 Starting FlipSync Root Directory Cleanup..."
log "📊 Current root directory files: $(count_files)"

# Create proper directory structure
log "📁 Creating proper directory structure..."
mkdir -p {tests,scripts,docs,logs,archive,temp}
mkdir -p tests/{unit,integration,e2e}
mkdir -p scripts/{deployment,database,utilities}
mkdir -p docs/{reports,plans,guides}
mkdir -p logs/{test-results,validation,monitoring}

success "Directory structure created"

# Phase 1: Move test files
log "🧪 Phase 1: Moving test files..."
moved_tests=0

# Move test_*.py files
for file in test_*.py; do
    if [ -f "$file" ]; then
        mv "$file" tests/
        ((moved_tests++))
    fi
done

# Move *_test*.py files
for file in *_test*.py; do
    if [ -f "$file" ]; then
        mv "$file" tests/
        ((moved_tests++))
    fi
done

# Move comprehensive test files
for file in comprehensive_*test*.py; do
    if [ -f "$file" ]; then
        mv "$file" tests/integration/
        ((moved_tests++))
    fi
done

# Move specific test files
test_files=(
    "comprehensive_agentic_system_test.py"
    "comprehensive_backend_test.py"
    "comprehensive_backend_validation.py"
    "comprehensive_frontend_audit.py"
    "comprehensive_user_journey_validation.py"
)

for file in "${test_files[@]}"; do
    if [ -f "$file" ]; then
        mv "$file" tests/integration/
        ((moved_tests++))
    fi
done

success "Moved $moved_tests test files to tests/"

# Phase 2: Move documentation
log "📚 Phase 2: Moving documentation..."
moved_docs=0

# Move report files
for file in *REPORT*.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/reports/
        ((moved_docs++))
    fi
done

# Move plan files
for file in *PLAN*.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/plans/
        ((moved_docs++))
    fi
done

# Move guide files
for file in *GUIDE*.md *DOCUMENTATION*.md; do
    if [ -f "$file" ]; then
        mv "$file" docs/guides/
        ((moved_docs++))
    fi
done

# Move other documentation
doc_patterns=(
    "*AUDIT*.md"
    "*ANALYSIS*.md"
    "*ASSESSMENT*.md"
    "*COMPLETION*.md"
    "*VALIDATION*.md"
    "*INSTRUCTIONS*.md"
)

for pattern in "${doc_patterns[@]}"; do
    for file in $pattern; do
        if [ -f "$file" ]; then
            mv "$file" docs/reports/
            ((moved_docs++))
        fi
    done
done

success "Moved $moved_docs documentation files to docs/"

# Phase 3: Move scripts
log "🔧 Phase 3: Moving scripts..."
moved_scripts=0

# Move deployment scripts
for file in deploy_*.sh; do
    if [ -f "$file" ]; then
        mv "$file" scripts/deployment/
        ((moved_scripts++))
    fi
done

# Move other shell scripts (except this cleanup script)
for file in *.sh; do
    if [ -f "$file" ] && [ "$file" != "flipsync_automated_cleanup.sh" ]; then
        mv "$file" scripts/utilities/
        ((moved_scripts++))
    fi
done

# Move database scripts
for file in database_*.py create_*.py fix_*.py; do
    if [ -f "$file" ]; then
        mv "$file" scripts/database/
        ((moved_scripts++))
    fi
done

# Move utility scripts
utility_patterns=(
    "*_optimization.py"
    "debug_*.py"
    "cleanup_*.py"
    "configuration_*.py"
    "current_*.py"
    "alerting_*.py"
    "api_security_*.py"
    "application_metrics_*.py"
)

for pattern in "${utility_patterns[@]}"; do
    for file in $pattern; do
        if [ -f "$file" ]; then
            mv "$file" scripts/utilities/
            ((moved_scripts++))
        fi
    done
done

success "Moved $moved_scripts script files to scripts/"

# Phase 4: Move logs and results
log "📊 Phase 4: Moving logs and results..."
moved_logs=0

# Move JSON result files
for file in *results*.json *_report_*.json backend_validation_report_*.json; do
    if [ -f "$file" ]; then
        mv "$file" logs/test-results/
        ((moved_logs++))
    fi
done

# Move log files
for file in *.log; do
    if [ -f "$file" ]; then
        mv "$file" logs/monitoring/
        ((moved_logs++))
    fi
done

success "Moved $moved_logs log/result files to logs/"

# Phase 5: Archive old backups and temporary files
log "🗄️ Phase 5: Archiving backups and cleaning temporary files..."
archived=0

# Move backup directories
for dir in cleanup_backup_* *_backup_*; do
    if [ -d "$dir" ]; then
        mv "$dir" archive/
        ((archived++))
    fi
done

# Move backup files
for file in *backup*.sql *.tar.gz; do
    if [ -f "$file" ]; then
        mv "$file" archive/
        ((archived++))
    fi
done

success "Archived $archived backup items"

# Phase 6: Clean up temporary and cache files
log "🗑️ Phase 6: Removing temporary files..."
cleaned=0

# Remove Python cache files
find . -maxdepth 1 -name "*.pyc" -delete 2>/dev/null && ((cleaned++)) || true
find . -maxdepth 1 -name "*.pyo" -delete 2>/dev/null && ((cleaned++)) || true
find . -maxdepth 1 -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null && ((cleaned++)) || true

# Remove other temporary files
for file in .DS_Store Thumbs.db *.tmp *.temp; do
    if [ -f "$file" ]; then
        rm "$file"
        ((cleaned++))
    fi
done

success "Cleaned $cleaned temporary files"

# Final count and summary
final_count=$(count_files)
total_moved=$((moved_tests + moved_docs + moved_scripts + moved_logs + archived))

log "✅ Cleanup completed successfully!"
echo ""
echo "📊 CLEANUP SUMMARY:"
echo "==================="
echo "🧪 Test files moved:        $moved_tests → tests/"
echo "📚 Documentation moved:     $moved_docs → docs/"
echo "🔧 Scripts moved:           $moved_scripts → scripts/"
echo "📊 Logs/results moved:      $moved_logs → logs/"
echo "🗄️ Items archived:          $archived → archive/"
echo "🗑️ Temporary files cleaned: $cleaned"
echo ""
echo "📈 BEFORE: 327 files in root directory"
echo "📉 AFTER:  $final_count files in root directory"
echo "🎯 MOVED:  $total_moved files organized"
echo ""

if [ $final_count -lt 20 ]; then
    success "Root directory cleanup: EXCELLENT (target: <20 files)"
elif [ $final_count -lt 50 ]; then
    warning "Root directory cleanup: GOOD (target: <20 files)"
else
    warning "Root directory cleanup: NEEDS MORE WORK (target: <20 files)"
fi

echo ""
echo "📁 NEW DIRECTORY STRUCTURE:"
echo "├── tests/"
echo "│   ├── unit/"
echo "│   ├── integration/"
echo "│   └── e2e/"
echo "├── scripts/"
echo "│   ├── deployment/"
echo "│   ├── database/"
echo "│   └── utilities/"
echo "├── docs/"
echo "│   ├── reports/"
echo "│   ├── plans/"
echo "│   └── guides/"
echo "├── logs/"
echo "│   ├── test-results/"
echo "│   ├── validation/"
echo "│   └── monitoring/"
echo "└── archive/"
echo ""

log "🚀 Ready for Proxmox migration!"
