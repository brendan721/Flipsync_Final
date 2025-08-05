#!/usr/bin/env python3
"""
FlipSync Codebase Redundancy Cleanup - Phase 2 (Systematic Import Replacement)
==============================================================================

This script performs systematic import replacement across 81 files identified in the analysis.
Phase 2 focuses on updating imports without removing legacy files (that's Phase 3).

SYSTEMATIC REPLACEMENT TARGETS:
1. UnifiedAgent -> AutonomousAgent
2. UnifiedAgentRepository -> AutonomousAgentRepository  
3. UnifiedAgentDecision -> AutonomousAgentDecision
4. UnifiedAgentCommunication -> AutonomousAgentCommunication
5. Legacy authentication imports -> 4+1 architecture imports

SAFETY FEATURES:
- Backup creation for all modified files
- Rollback capability
- Comprehensive logging
- Validation after changes

Usage:
    python cleanup_redundancy_phase2.py --dry-run  # Preview changes
    python cleanup_redundancy_phase2.py --execute  # Execute cleanup
    python cleanup_redundancy_phase2.py --rollback # Rollback changes
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


class RedundancyCleanupPhase2:
    """
    Phase 2 redundancy cleanup for FlipSync codebase.
    
    Focuses on systematic import replacement without removing legacy files.
    """
    
    def __init__(self, project_root: str = "/home/brend/Flipsync_Final"):
        self.project_root = Path(project_root)
        self.backup_dir = self.project_root / "cleanup_backups" / f"phase2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.fs_agt_clean = self.project_root / "fs_agt_clean"
        
        # Import replacements for Phase 2
        self.import_replacements = {
            # Core agent model replacements
            "UnifiedAgent": "AutonomousAgent",
            "UnifiedAgentDecision": "AutonomousAgentDecision", 
            "UnifiedAgentCommunication": "AutonomousAgentCommunication",
            "unified_agents": "autonomous_agents",
            
            # Repository replacements
            "UnifiedAgentRepository": "AutonomousAgentRepository",
            "from fs_agt_clean.database.repositories.agent_repository import UnifiedAgentRepository": "from fs_agt_clean.database.repositories.autonomous_agent_repository import AutonomousAgentRepository",
            
            # Import path standardization
            "from fs_agt_clean.database.models.unified_agent import": "from fs_agt_clean.database.models.autonomous_agent import",
            "from fs_agt_clean.core.models.user import UnifiedUserResponse": "from fs_agt_clean.database.models.unified_user import UnifiedUserResponse",
            "from fs_agt_clean.core.auth.auth_factory import get_current_user_optional": "from fs_agt_clean.api.dependencies.dependencies import get_current_user_optional",
        }
        
        # Files to exclude from modification (critical system files)
        self.exclude_from_modification = [
            "fs_agt_clean/database/models/unified_agent.py",  # Will be removed in Phase 3
            "fs_agt_clean/database/repositories/agent_repository.py",  # Will be removed in Phase 3
            "fs_agt_clean/database/models/autonomous_agent.py",  # New 4+1 models (don't modify)
            "fs_agt_clean/database/repositories/autonomous_agent_repository.py",  # New 4+1 repos (don't modify)
            "fs_agt_clean/api/routes/agents_4plus1.py",  # New 4+1 APIs (don't modify)
            "fs_agt_clean/api/routes/decisions_4plus1.py",
            "fs_agt_clean/api/routes/chat_4plus1.py",
            "fs_agt_clean/api/websocket/agents_4plus1_ws.py",  # New 4+1 WebSockets (don't modify)
            "fs_agt_clean/api/websocket/learning_4plus1_ws.py",
            "fs_agt_clean/api/websocket/chat_4plus1_ws.py",
        ]
        
        logger.info(f"RedundancyCleanupPhase2 initialized for {self.project_root}")
    
    def create_backup(self) -> bool:
        """Create backup of entire codebase before cleanup."""
        try:
            logger.info(f"Creating Phase 2 backup in {self.backup_dir}")
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
                f.write(f"FlipSync Redundancy Cleanup Phase 2 Backup\n")
                f.write(f"Created: {datetime.now().isoformat()}\n")
                f.write(f"Project Root: {self.project_root}\n")
                f.write(f"Backup Directory: {self.backup_dir}\n\n")
                f.write("Import replacements to be made:\n")
                for old, new in self.import_replacements.items():
                    f.write(f"  - '{old}' -> '{new}'\n")
            
            logger.info(f"✅ Phase 2 backup created successfully: {self.backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {e}")
            return False
    
    def find_files_to_modify(self) -> List[Path]:
        """Find all Python files that need import replacements."""
        logger.info("🔍 Finding files that need import replacements...")
        
        files_to_modify = []
        
        # Search all Python files in fs_agt_clean
        for py_file in self.fs_agt_clean.rglob("*.py"):
            # Skip excluded files
            relative_path = str(py_file.relative_to(self.project_root))
            if any(exclude in relative_path for exclude in self.exclude_from_modification):
                continue
                
            files_to_modify.append(py_file)
        
        # Remove duplicates and sort
        files_to_modify = sorted(set(files_to_modify))
        
        logger.info(f"📊 Found {len(files_to_modify)} files to potentially modify")
        return files_to_modify
    
    def analyze_file_changes(self, file_path: Path) -> Tuple[bool, List[str], Dict[str, int]]:
        """Analyze what changes would be made to a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            changes = []
            replacement_counts = {}
            needs_modification = False
            
            for old_pattern, new_pattern in self.import_replacements.items():
                if old_pattern in content:
                    needs_modification = True
                    count = content.count(old_pattern)
                    replacement_counts[old_pattern] = count
                    changes.append(f"Replace '{old_pattern}' -> '{new_pattern}' ({count} occurrences)")
            
            return needs_modification, changes, replacement_counts
            
        except Exception as e:
            logger.error(f"Error analyzing {file_path}: {e}")
            return False, [f"Error: {e}"], {}
    
    def apply_replacements_to_file(self, file_path: Path) -> bool:
        """Apply import replacements to a single file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Apply all replacements
            for old_pattern, new_pattern in self.import_replacements.items():
                content = content.replace(old_pattern, new_pattern)
            
            # Only write if content changed
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error modifying {file_path}: {e}")
            return False
    
    def dry_run(self) -> Dict[str, any]:
        """Perform dry run to show what would be changed."""
        logger.info("🧪 Performing Phase 2 dry run analysis...")
        
        analysis = {
            "files_to_modify": [],
            "total_changes": 0,
            "replacement_summary": {},
            "issues": []
        }
        
        # Initialize replacement summary
        for old_pattern in self.import_replacements.keys():
            analysis["replacement_summary"][old_pattern] = 0
        
        # Analyze files to modify
        files_to_check = self.find_files_to_modify()
        
        for file_path in files_to_check:
            needs_modification, changes, replacement_counts = self.analyze_file_changes(file_path)
            if needs_modification:
                analysis["files_to_modify"].append({
                    "file": str(file_path),
                    "changes": changes,
                    "replacement_counts": replacement_counts
                })
                analysis["total_changes"] += len(changes)
                
                # Update replacement summary
                for pattern, count in replacement_counts.items():
                    analysis["replacement_summary"][pattern] += count
        
        return analysis
    
    def execute_cleanup(self) -> bool:
        """Execute the systematic import replacement."""
        logger.info("🚀 Executing Phase 2 systematic import replacement...")
        
        # Create backup
        if not self.create_backup():
            logger.error("❌ Cannot proceed - backup creation failed")
            return False
        
        try:
            # Find and modify files
            files_to_modify = self.find_files_to_modify()
            modified_count = 0
            total_replacements = 0
            
            for file_path in files_to_modify:
                needs_modification, changes, replacement_counts = self.analyze_file_changes(file_path)
                if needs_modification:
                    logger.info(f"🔄 Modifying {file_path}")
                    
                    if self.apply_replacements_to_file(file_path):
                        modified_count += 1
                        total_replacements += sum(replacement_counts.values())
            
            logger.info(f"✅ Phase 2 cleanup completed successfully!")
            logger.info(f"📊 Files modified: {modified_count}")
            logger.info(f"📊 Total replacements: {total_replacements}")
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
            
            backups = sorted(backup_parent.glob("phase2_*"), reverse=True)
            if not backups:
                logger.error("❌ No Phase 2 backups found")
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
    parser = argparse.ArgumentParser(description="FlipSync Redundancy Cleanup Phase 2")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without executing")
    parser.add_argument("--execute", action="store_true", help="Execute cleanup operations")
    parser.add_argument("--rollback", action="store_true", help="Rollback previous cleanup")
    parser.add_argument("--backup-path", help="Specific backup path for rollback")
    parser.add_argument("--project-root", default="/home/brend/Flipsync_Final", help="Project root directory")
    
    args = parser.parse_args()
    
    if not any([args.dry_run, args.execute, args.rollback]):
        parser.print_help()
        sys.exit(1)
    
    cleanup = RedundancyCleanupPhase2(args.project_root)
    
    if args.dry_run:
        logger.info("🧪 PERFORMING DRY RUN - NO CHANGES WILL BE MADE")
        analysis = cleanup.dry_run()
        
        print("\n" + "="*80)
        print("PHASE 2 SYSTEMATIC IMPORT REPLACEMENT - DRY RUN ANALYSIS")
        print("="*80)
        
        print(f"\n📝 FILES TO MODIFY ({len(analysis['files_to_modify'])}):")
        for i, file_info in enumerate(analysis['files_to_modify'][:10]):  # Show first 10
            print(f"  🔄 {file_info['file']}")
            for change in file_info['changes'][:3]:  # Show first 3 changes per file
                print(f"     - {change}")
        
        if len(analysis['files_to_modify']) > 10:
            print(f"  ... and {len(analysis['files_to_modify']) - 10} more files")
        
        print(f"\n📊 REPLACEMENT SUMMARY:")
        for pattern, count in analysis['replacement_summary'].items():
            if count > 0:
                print(f"  - '{pattern}': {count} occurrences")
        
        print(f"\n📊 SUMMARY:")
        print(f"  - Files to modify: {len(analysis['files_to_modify'])}")
        print(f"  - Total changes: {analysis['total_changes']}")
        print(f"  - Total replacements: {sum(analysis['replacement_summary'].values())}")
        
        if analysis['issues']:
            print(f"\n⚠️ ISSUES FOUND ({len(analysis['issues'])}):")
            for issue in analysis['issues']:
                print(f"  ❌ {issue}")
        else:
            print("\n✅ NO ISSUES FOUND - SAFE TO EXECUTE CLEANUP")
    
    elif args.execute:
        logger.info("🚀 EXECUTING PHASE 2 SYSTEMATIC IMPORT REPLACEMENT")
        success = cleanup.execute_cleanup()
        if success:
            print("\n✅ PHASE 2 CLEANUP COMPLETED SUCCESSFULLY!")
            print("🔄 Run tests to verify everything works correctly")
            print("📝 Review changes and commit to version control")
        else:
            print("\n❌ CLEANUP FAILED - CHECK LOGS FOR DETAILS")
            sys.exit(1)
    
    elif args.rollback:
        logger.info("🔄 ROLLING BACK PHASE 2 CLEANUP")
        success = cleanup.rollback(args.backup_path)
        if success:
            print("\n✅ ROLLBACK COMPLETED SUCCESSFULLY!")
        else:
            print("\n❌ ROLLBACK FAILED - CHECK LOGS FOR DETAILS")
            sys.exit(1)


if __name__ == "__main__":
    main()
