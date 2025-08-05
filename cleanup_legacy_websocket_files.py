#!/usr/bin/env python3
"""
Legacy WebSocket Cleanup Script
===============================

This script identifies and optionally removes legacy WebSocket files that have been
replaced by the unified WebSocket system at /ws/flipsync.

SAFETY: This script only identifies files by default. Use --remove flag to actually delete.
"""

import os
import sys
from pathlib import Path
from typing import List, Dict

def find_legacy_websocket_files() -> Dict[str, List[str]]:
    """Find all legacy WebSocket files that can be safely removed."""
    
    legacy_files = {
        "deprecated_routes": [],
        "unused_clients": [],
        "legacy_handlers": [],
        "test_files": []
    }
    
    # Define patterns for legacy files
    legacy_patterns = {
        "deprecated_routes": [
            "fs_agt_clean/api/routes/websocket/enhanced_websocket_routes.py",
            "fs_agt_clean/api/routes/websocket_basic.py",
            "fs_agt_clean/api/routes/websocket_chat.py",
        ],
        "unused_clients": [
            "fs_agt_clean/core/websocket/enhanced_websocket_client.py",
            "fs_agt_clean/core/websocket/phase4_enhanced_websocket.py",
        ],
        "legacy_handlers": [
            "fs_agt_clean/core/websocket/legacy_handlers.py",
            "fs_agt_clean/core/websocket/deprecated_manager.py",
        ],
        "test_files": [
            "tests/websocket/test_legacy_websocket.py",
            "tests/websocket/test_enhanced_websocket_routes.py",
        ]
    }
    
    # Check which files actually exist
    for category, file_list in legacy_patterns.items():
        for file_path in file_list:
            if os.path.exists(file_path):
                legacy_files[category].append(file_path)
    
    return legacy_files

def analyze_file_dependencies(file_path: str) -> List[str]:
    """Analyze a file to find what imports it."""
    dependencies = []
    
    # Search for imports of this file in the codebase
    file_name = os.path.basename(file_path).replace('.py', '')
    module_path = file_path.replace('/', '.').replace('.py', '')
    
    # Search patterns
    search_patterns = [
        f"from {module_path} import",
        f"import {module_path}",
        f"from {file_name} import",
        f"import {file_name}",
    ]
    
    # Search in all Python files
    for root, dirs, files in os.walk('.'):
        # Skip certain directories
        if any(skip in root for skip in ['.git', '__pycache__', '.pytest_cache', 'node_modules']):
            continue
            
        for file in files:
            if file.endswith('.py'):
                file_full_path = os.path.join(root, file)
                if file_full_path == file_path:
                    continue  # Skip the file itself
                    
                try:
                    with open(file_full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        for pattern in search_patterns:
                            if pattern in content:
                                dependencies.append(file_full_path)
                                break
                except (UnicodeDecodeError, PermissionError):
                    continue
    
    return dependencies

def create_deprecation_notice(file_path: str) -> str:
    """Create a deprecation notice for a legacy file."""
    file_name = os.path.basename(file_path)
    
    return f'''"""
DEPRECATED: {file_name}
{'=' * (len(file_name) + 12)}

⚠️ DEPRECATION NOTICE: This file has been replaced by the unified WebSocket system
at /ws/flipsync (websocket_unified.py).

All WebSocket functionality has been consolidated into the unified endpoint for:
- Better performance and reliability
- Simplified connection management
- Unified authentication
- Consistent message routing

This file will be removed in a future version.

For migration guidance, see: WEBSOCKET_TECHNICAL_AUDIT_REPORT.md
"""

# Prevent accidental imports
raise ImportError(
    f"{{__name__}} has been deprecated. "
    "Use the unified WebSocket system at /ws/flipsync instead."
)
'''

def generate_cleanup_report(legacy_files: Dict[str, List[str]]) -> str:
    """Generate a comprehensive cleanup report."""
    
    report = []
    report.append("# Legacy WebSocket Cleanup Report")
    report.append("=" * 40)
    report.append("")
    
    total_files = sum(len(files) for files in legacy_files.values())
    report.append(f"**Total Legacy Files Found**: {total_files}")
    report.append("")
    
    for category, files in legacy_files.items():
        if files:
            report.append(f"## {category.replace('_', ' ').title()}")
            report.append("")
            
            for file_path in files:
                report.append(f"### {file_path}")
                
                # Check if file exists and get size
                if os.path.exists(file_path):
                    size = os.path.getsize(file_path)
                    report.append(f"- **Size**: {size} bytes")
                    
                    # Check dependencies
                    deps = analyze_file_dependencies(file_path)
                    if deps:
                        report.append(f"- **Dependencies**: {len(deps)} files import this")
                        for dep in deps[:3]:  # Show first 3 dependencies
                            report.append(f"  - {dep}")
                        if len(deps) > 3:
                            report.append(f"  - ... and {len(deps) - 3} more")
                    else:
                        report.append("- **Dependencies**: None found (safe to remove)")
                else:
                    report.append("- **Status**: File not found")
                
                report.append("")
    
    # Add recommendations
    report.append("## Recommendations")
    report.append("")
    
    safe_to_remove = []
    needs_migration = []
    
    for category, files in legacy_files.items():
        for file_path in files:
            if os.path.exists(file_path):
                deps = analyze_file_dependencies(file_path)
                if not deps:
                    safe_to_remove.append(file_path)
                else:
                    needs_migration.append((file_path, len(deps)))
    
    if safe_to_remove:
        report.append("### Safe to Remove (No Dependencies)")
        for file_path in safe_to_remove:
            report.append(f"- {file_path}")
        report.append("")
    
    if needs_migration:
        report.append("### Requires Migration (Has Dependencies)")
        for file_path, dep_count in needs_migration:
            report.append(f"- {file_path} ({dep_count} dependencies)")
        report.append("")
    
    report.append("### Next Steps")
    report.append("1. Review dependencies for files that need migration")
    report.append("2. Update imports to use unified WebSocket system")
    report.append("3. Add deprecation notices to files before removal")
    report.append("4. Remove files that are safe to delete")
    report.append("")
    
    return "\n".join(report)

def main():
    """Main cleanup function."""
    print("🔍 FlipSync Legacy WebSocket Cleanup")
    print("=" * 40)
    
    # Find legacy files
    print("Scanning for legacy WebSocket files...")
    legacy_files = find_legacy_websocket_files()
    
    total_files = sum(len(files) for files in legacy_files.values())
    print(f"Found {total_files} legacy WebSocket files")
    
    if total_files == 0:
        print("✅ No legacy WebSocket files found - cleanup already complete!")
        return
    
    # Generate report
    print("\nGenerating cleanup report...")
    report = generate_cleanup_report(legacy_files)
    
    # Save report
    report_file = "LEGACY_WEBSOCKET_CLEANUP_REPORT.md"
    with open(report_file, 'w') as f:
        f.write(report)
    
    print(f"📄 Cleanup report saved to: {report_file}")
    
    # Show summary
    print("\n📊 Summary:")
    for category, files in legacy_files.items():
        if files:
            print(f"  {category.replace('_', ' ').title()}: {len(files)} files")
    
    # Check for --remove flag
    if "--remove" in sys.argv:
        print("\n⚠️  REMOVAL MODE ENABLED")
        print("This will add deprecation notices to legacy files...")
        
        confirm = input("Continue? (y/N): ").lower().strip()
        if confirm == 'y':
            for category, files in legacy_files.items():
                for file_path in files:
                    if os.path.exists(file_path):
                        # Check if file has dependencies
                        deps = analyze_file_dependencies(file_path)
                        if not deps:
                            print(f"🗑️  Adding deprecation notice to: {file_path}")
                            
                            # Backup original file
                            backup_path = f"{file_path}.backup"
                            os.rename(file_path, backup_path)
                            
                            # Create deprecation notice
                            with open(file_path, 'w') as f:
                                f.write(create_deprecation_notice(file_path))
                            
                            print(f"   Original backed up to: {backup_path}")
                        else:
                            print(f"⚠️  Skipping {file_path} (has {len(deps)} dependencies)")
            
            print("\n✅ Deprecation notices added to safe files")
            print("📝 Review the cleanup report for files that need migration")
        else:
            print("❌ Removal cancelled")
    else:
        print(f"\n📋 Review the report: {report_file}")
        print("💡 Run with --remove flag to add deprecation notices")

if __name__ == "__main__":
    main()
