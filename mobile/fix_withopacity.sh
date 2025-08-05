#!/bin/bash

# FlipSync withOpacity to withValues Migration Script
# This script replaces all instances of .withOpacity(x) with .withValues(alpha: x)

echo "🔧 Starting withOpacity to withValues migration..."

# Count total instances before replacement
TOTAL_BEFORE=$(find lib -name "*.dart" -exec grep -l "\.withOpacity(" {} \; | wc -l)
INSTANCES_BEFORE=$(find lib -name "*.dart" -exec grep -o "\.withOpacity(" {} \; | wc -l)

echo "📊 Found $INSTANCES_BEFORE withOpacity instances in $TOTAL_BEFORE files"

# Create backup directory
BACKUP_DIR="backup_withopacity_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "💾 Creating backup in $BACKUP_DIR..."

# Function to process a single file
process_file() {
    local file="$1"
    local backup_file="$BACKUP_DIR/$(basename "$file")"
    
    # Create backup
    cp "$file" "$backup_file"
    
    # Replace .withOpacity(value) with .withValues(alpha: value)
    # Handle various whitespace patterns
    sed -i 's/\.withOpacity(\([^)]*\))/\.withValues(alpha: \1)/g' "$file"
    
    # Count changes in this file
    local changes=$(diff "$backup_file" "$file" | grep -c "^<\|^>")
    if [ "$changes" -gt 0 ]; then
        echo "  ✅ $file: $((changes/2)) replacements"
    fi
}

# Export function for parallel processing
export -f process_file
export BACKUP_DIR

# Find all Dart files with withOpacity and process them
echo "🔄 Processing files..."
find lib -name "*.dart" -exec grep -l "\.withOpacity(" {} \; | while read -r file; do
    process_file "$file"
done

# Count instances after replacement
TOTAL_AFTER=$(find lib -name "*.dart" -exec grep -l "\.withOpacity(" {} \; | wc -l)
INSTANCES_AFTER=$(find lib -name "*.dart" -exec grep -o "\.withOpacity(" {} \; | wc -l)

echo ""
echo "📈 Migration Results:"
echo "  Before: $INSTANCES_BEFORE instances in $TOTAL_BEFORE files"
echo "  After:  $INSTANCES_AFTER instances in $TOTAL_AFTER files"
echo "  Fixed:  $((INSTANCES_BEFORE - INSTANCES_AFTER)) instances"

if [ "$INSTANCES_AFTER" -eq 0 ]; then
    echo "🎉 All withOpacity instances successfully migrated!"
else
    echo "⚠️  $INSTANCES_AFTER instances remain (may need manual review)"
    echo "📋 Remaining instances:"
    find lib -name "*.dart" -exec grep -Hn "\.withOpacity(" {} \;
fi

echo ""
echo "💾 Backup created in: $BACKUP_DIR"
echo "🔧 Migration complete!"

# Verify syntax by running a quick analysis
echo ""
echo "🔍 Running quick syntax check..."
if flutter analyze --no-pub lib/ > /dev/null 2>&1; then
    echo "✅ Syntax check passed - no compilation errors introduced"
else
    echo "⚠️  Syntax issues detected - please review changes"
    echo "💡 You can restore from backup if needed: cp $BACKUP_DIR/* lib/"
fi
