#!/usr/bin/env python3
"""
FlipSync Codebase Redundancy Cleanup - Phase 1 (Critical)
=========================================================

This script performs critical cleanup of legacy code that conflicts with the 4+1 architecture.
Phase 1 focuses on high-risk redundancies that must be addressed immediately.

CRITICAL CLEANUP TARGETS:
1. Legacy Database Models (UnifiedAgent vs AutonomousAgent conflicts)
2. Duplicate Authentication Dependencies
3. Legacy Repository Classes
4. Conflicting Import Statements

SAFETY FEATURES:
- Dependency verification before removal
- Backup creation for all modified files
- Rollback capability
- Comprehensive logging

Usage:
    python cleanup_redundancy_phase1.py --dry-run  # Preview changes
    python cleanup_redundancy_phase1.py --execute  # Execute cleanup
    python cleanup_redundancy_phase1.py --rollback # Rollback changes
"""

import argparse
import logging
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RedundancyCleanupPhase1:
    """
    Phase 1 redundancy cleanup for FlipSync codebase.
    
    Focuses on critical legacy code that conflicts with 4+1 architecture.
    """
    
    def __init__(self, project_root: str = "/home/brend/Flipsync_Final"):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "cleanup_backups" / f"phase1_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.fs_agt_clean = self.project_root / "fs_agt_clean"
        
        # Files to remove completely (high confidence)
        self.files_to_remove = [
            "fs_agt_clean/database/models/unified_agent.py",
            "fs_agt_clean/database/repositories/agent_repository.py",
        ]
        
        # Files to refactor (replace imports/references)
        self.import_replacements = {
            "from fs_agt_clean.database.models.unified_agent import": "from fs_agt_clean.database.models.autonomous_agent import",
            "from fs_agt_clean.database.repositories.agent_repository import UnifiedAgentRepository": "from fs_agt_clean.database.repositories.autonomous_agent_repository import AutonomousAgentRepository",
            "UnifiedAgentRepository": "AutonomousAgentRepository",
            "UnifiedAgent": "AutonomousAgent",
            "UnifiedAgentDecision": "AutonomousAgentDecision",
            "unified_agents": "autonomous_agents",
            "from fs_agt_clean.core.auth.auth_factory import get_current_user_optional": "from fs_agt_clean.api.dependencies.dependencies import get_current_user_optional",
            "from fs_agt_clean.core.models.user import UnifiedUserResponse": "from fs_agt_clean.database.models.unified_user import UnifiedUserResponse",
        }
        
        # Files that are safe to modify (verified no critical dependencies)
        self.safe_to_modify = [
            "fs_agt_clean/api/routes/",
            "fs_agt_clean/api/websocket/",
            "fs_agt_clean/core/websocket/",
            "fs_agt_clean/services/",
            "test_*.py",
        ]
        
        # Files to exclude from modification (critical system files)
        self.exclude_from_modification = [
            "fs_agt_clean/database/models/autonomous_agent.py",  # New 4+1 models
            "fs_agt_clean/database/repositories/autonomous_agent_repository.py",  # New 4+1 repos
            "fs_agt_clean/api/routes/agents_4plus1.py",  # New 4+1 APIs
            "fs_agt_clean/api/routes/decisions_4plus1.py",
            "fs_agt_clean/api/routes/chat_4plus1.py",
            "fs_agt_clean/api/websocket/agents_4plus1_ws.py",  # New 4+1 WebSockets
            "fs_agt_clean/api/websocket/learning_4plus1_ws.py",
            "fs_agt_clean/api/websocket/chat_4plus1_ws.py",
        ]
        
        logger.info(f"RedundancyCleanupPhase1 initialized for {self.project_root}")
    
    def create_backup(self) -> bool:
        """Create backup of entire codebase before cleanup."""
        try:
            logger.info(f"Creating backup in {self.backup_dir}")
            self.backup_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy entire fs_agt_clean directory
            shutil.copytree(
                self.fs_agt_clean,
                self.backup_dir / "fs_agt_clean",
                ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.git')
            )
            
            # Create backup manifest
            manifest_file = self.backup_dir / "backup_manifest.txt"
            with open(manifest_file, 'w') as f:
                f.write(f"FlipSync Redundancy Cleanup Phase 1 Backup\n")
                f.write(f"Created: {datetime.now().isoformat()}\n")
                f.write(f"Project Root: {self.project_root}\n")
                f.write(f"Backup Directory: {self.backup_dir}\n\n")
                f.write("Files to be removed:\n")
                for file_path in self.files_to_remove:
                    f.write(f"  - {file_path}\n")
                f.write("\nImport replacements to be made:\n")
                for old, new in self.import_replacements.items():
                    f.write(f"  - '{old}' -> '{new}'\n")
            
            logger.info(f"✅ Backup created successfully: {self.backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            return False
    
    def verify_dependencies(self) -> Tuple[bool, List[str]]:
        """Verify that files to be removed don't have critical dependencies."""
        logger.info("🔍 Verifying dependencies before removal...")
        
        issues = []
        
        for file_to_remove in self.files_to_remove:
            file_path = self.project_root / file_to_remove
            if not file_path.exists():
                logger.warning(f"⚠️ File not found: {file_path}")
                continue
            
            # Search for imports of this file
            module_name = file_to_remove.replace('/', '.').replace('.py', '')
            search_pattern = f"from {module_name} import"
            
            try:
                result = subprocess.run(
                    ['grep', '-r', search_pattern, str(self.fs_agt_clean)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    dependencies = result.stdout.strip().split('\n')
                    # Filter out dependencies in files we're also modifying
                    critical_dependencies = [
                        dep for dep in dependencies 
                        if not any(safe_path in dep for safe_path in self.safe_to_modify)
                        and not any(exclude_path in dep for exclude_path in self.exclude_from_modification)
                    ]
                    
                    if critical_dependencies:
                        issues.append(f"Critical dependencies found for {file_to_remove}:")
                        for dep in critical_dependencies:
                            issues.append(f"  - {dep}")
                
            except Exception as e:
                issues.append(f"Error checking dependencies for {file_to_remove}: {e}")
        
        if issues:
            logger.error("❌ Dependency verification failed:")
            for issue in issues:
                logger.error(f"  {issue}")
            return False, issues
        else:
            logger.info("✅ Dependency verification passed")
            return True, []
    
    def find_files_to_modify(self) -> List[Path]:
        """Find all Python files that need import replacements."""
        logger.info("🔍 Finding files that need import replacements...")
        
        files_to_modify = []
        
        for pattern in self.safe_to_modify:
            search_path = self.fs_agt_clean / pattern.replace("fs_agt_clean/", "")
            
            if search_path.is_dir():
                # Search directory recursively
                for py_file in search_path.rglob("*.py"):
                    if not any(exclude in str(py_file) for exclude in self.exclude_from_modification):
                        files_to_modify.append(py_file)
            elif search_path.exists():
                # Single file
                files_to_modify.append(search_path)
            else:
                # Pattern matching
                for py_file in self.fs_agt_clean.rglob(pattern):
                    if not any(exclude in str(py_file) for exclude in self.exclude_from_modification):
                        files_to_modify.append(py_file)
        
        # Remove duplicates and sort
        files_to_modify = sorted(set(files_to_modify))
        
        logger.info(f"📊 Found {len(files_to_modify)} files to potentially modify")
        return files_to_modify
    
    def analyze_file_changes(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Analyze what changes would be made to a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            changes = []
            needs_modification = False
            
            for old_pattern, new_pattern in self.import_replacements.items():
                if old_pattern in content:
                    needs_modification = True
                    count = content.count(old_pattern)
                    changes.append(f"Replace '{old_pattern}' -> '{new_pattern}' ({count} occurrences)")
            
            return needs_modification, changes
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return False, [f"Error: {e}"]
    
    def dry_run(self) -> Dict[str, any]:
        """Perform dry run to show what would be changed."""
        logger.info("🧪 Performing dry run analysis...")
        
        analysis = {
            "files_to_remove": [],
            "files_to_modify": [],
            "total_changes": 0,
            "issues": []
        }
        
        # Analyze files to remove
        for file_to_remove in self.files_to_remove:
            file_path = self.project_root / file_to_remove
            if file_path.exists():
                analysis["files_to_remove"].append(str(file_path))
            else:
                analysis["issues"].append(f"File not found: {file_path}")
        
        # Analyze files to modify
        files_to_check = self.find_files_to_modify()
        
        for file_path in files_to_check:
            needs_modification, changes = self.analyze_file_changes(file_path)
            if needs_modification:
                analysis["files_to_modify"].append({
                    "file": str(file_path),
                    "changes": changes
                })
                analysis["total_changes"] += len(changes)
        
        # Verify dependencies
        deps_ok, dep_issues = self.verify_dependencies()
        if not deps_ok:
            analysis["issues"].extend(dep_issues)
        
        return analysis
    
    def execute_cleanup(self) -> bool:
        """Execute the actual cleanup operations."""
        logger.info("🚀 Executing Phase 1 redundancy cleanup...")
        
        # Verify dependencies first
        deps_ok, dep_issues = self.verify_dependencies()
        if not deps_ok:
            logger.error("❌ Cannot proceed - dependency verification failed")
            return False
        
        # Create backup
        if not self.create_backup():
            logger.error("❌ Cannot proceed - backup creation failed")
            return False
        
        try:
            # Remove legacy files
            for file_to_remove in self.files_to_remove:
                file_path = self.project_root / file_to_remove
                if file_path.exists():
                    logger.info(f"🗑️ Removing {file_path}")
                    file_path.unlink()
                else:
                    logger.warning(f"⚠️ File not found: {file_path}")
            
            # Modify files with import replacements
            files_to_modify = self.find_files_to_modify()
            modified_count = 0
            
            for file_path in files_to_modify:
                needs_modification, changes = self.analyze_file_changes(file_path)
                if needs_modification:
                    logger.info(f"🔄 Modifying {file_path}")
                    
                    # Read file content
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Apply replacements
                    for old_pattern, new_pattern in self.import_replacements.items():
                        content = content.replace(old_pattern, new_pattern)
                    
                    # Write modified content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    modified_count += 1
            
            logger.info(f"✅ Phase 1 cleanup completed successfully!")
            logger.info(f"📊 Files removed: {len(self.files_to_remove)}")
            logger.info(f"📊 Files modified: {modified_count}")
            logger.info(f"💾 Backup available at: {self.backup_dir}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Cleanup failed: {e}")
            logger.info(f"🔄 Restore from backup: {self.backup_dir}")
            return False
    
    def rollback(self, backup_path: str = None) -> bool:
        """Rollback changes from backup."""
        if backup_path:
            backup_dir = Path(backup_path)
        else:
            # Find most recent backup
            backup_parent = self.project_root / "cleanup_backups"
            if not backup_parent.exists():
                logger.error("❌ No backups found")
                return False
            
            backups = sorted(backup_parent.glob("phase1_*"), reverse=True)
            if not backups:
                logger.error("❌ No Phase 1 backups found")
                return False
            
            backup_dir = backups[0]
        
        logger.info(f"🔄 Rolling back from {backup_dir}")
        
        try:
            # Remove current fs_agt_clean
            if self.fs_agt_clean.exists():
                shutil.rmtree(self.fs_agt_clean)
            
            # Restore from backup
            shutil.copytree(
                backup_dir / "fs_agt_clean",
                self.fs_agt_clean
            )
            
            logger.info("✅ Rollback completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Rollback failed: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="FlipSync Redundancy Cleanup Phase 1")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    parser.add_argument("--execute", action="store_true", help="Execute cleanup operations")
    parser.add_argument("--rollback", action="store_true", help="Rollback previous cleanup")
    parser.add_argument("--backup-path", help="Specific backup path for rollback")
    parser.add_argument("--project-root", default="/home/brend/Flipsync_Final", help="Project root directory")
    
    args = parser.parse_args()
    
    if not any([args.dry_run, args.execute, args.rollback]):
        parser.print_help()
        sys.exit(1)
    
    cleanup = RedundancyCleanupPhase1(args.project_root)
    
    if args.dry_run:
        logger.info("🧪 PERFORMING DRY RUN - NO CHANGES WILL BE MADE")
        analysis = cleanup.dry_run()
        
        print("\n" + "="*80)
        print("PHASE 1 REDUNDANCY CLEANUP - DRY RUN ANALYSIS")
        print("="*80)
        
        print(f"\n📁 FILES TO REMOVE ({len(analysis['files_to_remove'])}):")
        for file_path in analysis['files_to_remove']:
            print(f"  🗑️ {file_path}")
        
        print(f"\n📝 FILES TO MODIFY ({len(analysis['files_to_modify'])}):")
        for file_info in analysis['files_to_modify']:
            print(f"  🔄 {file_info['file']}")
            for change in file_info['changes']:
                print(f"     - {change}")
        
        print(f"\n📊 SUMMARY:")
        print(f"  - Files to remove: {len(analysis['files_to_remove'])}")
        print(f"  - Files to modify: {len(analysis['files_to_modify'])}")
        print(f"  - Total changes: {analysis['total_changes']}")
        
        if analysis['issues']:
            print(f"\n⚠️ ISSUES FOUND ({len(analysis['issues'])}):")
            for issue in analysis['issues']:
                print(f"  ❌ {issue}")
            print("\n🛑 RESOLVE ISSUES BEFORE EXECUTING CLEANUP")
        else:
            print("\n✅ NO ISSUES FOUND - SAFE TO EXECUTE CLEANUP")
    
    elif args.execute:
        logger.info("🚀 EXECUTING PHASE 1 REDUNDANCY CLEANUP")
        success = cleanup.execute_cleanup()
        if success:
            print("\n✅ PHASE 1 CLEANUP COMPLETED SUCCESSFULLY!")
            print("🔄 Run tests to verify everything works correctly")
            print("📝 Review changes and commit to version control")
        else:
            print("\n❌ CLEANUP FAILED - CHECK LOGS FOR DETAILS")
            sys.exit(1)
    
    elif args.rollback:
        logger.info("🔄 ROLLING BACK PHASE 1 CLEANUP")
        success = cleanup.rollback(args.backup_path)
        if success:
            print("\n✅ ROLLBACK COMPLETED SUCCESSFULLY!")
        else:
            print("\n❌ ROLLBACK FAILED - CHECK LOGS FOR DETAILS")
            sys.exit(1)


if __name__ == "__main__":
    main()
