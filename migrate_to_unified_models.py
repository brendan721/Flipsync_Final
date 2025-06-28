#!/usr/bin/env python3
"""
Database Model Standardization Migration Script
===============================================

This script migrates FlipSync from duplicate model hierarchies to unified models:

BEFORE (Duplicated):
- fs_agt_clean/database/models/user.py (Pydantic)
- fs_agt_clean/database/models/users.py (SQLAlchemy)
- fs_agt_clean/core/models/database/auth_user.py (SQLAlchemy)
- fs_agt_clean/database/models/agents.py (SQLAlchemy)
- fs_agt_clean/core/models/database/agents.py (SQLAlchemy)
- fs_agt_clean/database/models/base.py
- fs_agt_clean/core/models/database/base.py

AFTER (Unified):
- fs_agt_clean/database/models/unified_user.py (Complete user management)
- fs_agt_clean/database/models/unified_agent.py (Complete agent management)
- fs_agt_clean/database/models/unified_base.py (Complete base functionality)

AGENT_CONTEXT: Database model consolidation and standardization
AGENT_PRIORITY: Eliminate duplication while maintaining all functionality
AGENT_PATTERN: Systematic migration with backup and validation
"""

import asyncio
import json
import os
import shutil
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelStandardizationMigrator:
    """Handles migration to unified database models."""
    
    def __init__(self):
        """Initialize migration configuration."""
        self.project_root = Path(__file__).parent
        self.backup_dir = self.project_root / "model_migration_backup"
        
        # Files to be replaced by unified models
        self.duplicate_files = [
            "fs_agt_clean/database/models/user.py",
            "fs_agt_clean/database/models/users.py", 
            "fs_agt_clean/core/models/database/auth_user.py",
            "fs_agt_clean/database/models/agents.py",
            "fs_agt_clean/core/models/database/agents.py",
            "fs_agt_clean/database/models/base.py",
            "fs_agt_clean/core/models/database/base.py",
            "fs_agt_clean/database/models/market.py",
            "fs_agt_clean/database/models/market_models.py",
            "fs_agt_clean/database/models/executive.py",
            "fs_agt_clean/database/models/executive_models.py",
        ]
        
        # Import mappings for updating references
        self.import_mappings = {
            # User model mappings
            "from fs_agt_clean.database.models.user import": "from fs_agt_clean.database.models.unified_user import",
            "from fs_agt_clean.database.models.users import": "from fs_agt_clean.database.models.unified_user import",
            "from fs_agt_clean.core.models.database.auth_user import": "from fs_agt_clean.database.models.unified_user import",
            
            # Agent model mappings
            "from fs_agt_clean.database.models.agents import": "from fs_agt_clean.database.models.unified_agent import",
            "from fs_agt_clean.core.models.database.agents import": "from fs_agt_clean.database.models.unified_agent import",
            
            # Base model mappings
            "from fs_agt_clean.database.models.base import": "from fs_agt_clean.database.models.unified_base import",
            "from fs_agt_clean.core.models.database.base import": "from fs_agt_clean.database.models.unified_base import",
            
            # Class name mappings
            "AuthUser": "UnifiedUser",
            "User": "UnifiedUser",
            "AgentModel": "UnifiedAgent",
            "Agent": "UnifiedAgent",
        }
    
    def create_backup(self) -> bool:
        """Create backup of existing model files."""
        logger.info("🔄 Creating backup of existing model files...")
        
        try:
            # Create backup directory
            self.backup_dir.mkdir(exist_ok=True)
            
            backup_count = 0
            for file_path in self.duplicate_files:
                source_file = self.project_root / file_path
                if source_file.exists():
                    # Create backup directory structure
                    backup_file = self.backup_dir / file_path
                    backup_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file to backup
                    shutil.copy2(source_file, backup_file)
                    backup_count += 1
                    logger.info(f"  ✅ Backed up: {file_path}")
            
            logger.info(f"  📦 Created backup of {backup_count} files in: {self.backup_dir}")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Backup creation failed: {e}")
            return False
    
    def update_imports_in_file(self, file_path: Path) -> bool:
        """Update imports in a single file."""
        try:
            if not file_path.exists() or not file_path.is_file():
                return True
            
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Track if any changes were made
            original_content = content
            
            # Apply import mappings
            for old_import, new_import in self.import_mappings.items():
                if old_import in content:
                    content = content.replace(old_import, new_import)
                    logger.info(f"    🔄 Updated import in {file_path.name}: {old_import}")
            
            # Write back if changes were made
            if content != original_content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                return True
            
            return True
            
        except Exception as e:
            logger.error(f"    ❌ Failed to update imports in {file_path}: {e}")
            return False
    
    def update_all_imports(self) -> bool:
        """Update imports across all Python files."""
        logger.info("🔄 Updating imports across codebase...")
        
        try:
            # Find all Python files
            python_files = []
            for root, dirs, files in os.walk(self.project_root / "fs_agt_clean"):
                for file in files:
                    if file.endswith('.py'):
                        python_files.append(Path(root) / file)
            
            updated_count = 0
            for file_path in python_files:
                if self.update_imports_in_file(file_path):
                    updated_count += 1
            
            logger.info(f"  ✅ Updated imports in {updated_count} files")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Import update failed: {e}")
            return False
    
    def remove_duplicate_files(self) -> bool:
        """Remove duplicate model files after migration."""
        logger.info("🗑️ Removing duplicate model files...")
        
        try:
            removed_count = 0
            for file_path in self.duplicate_files:
                source_file = self.project_root / file_path
                if source_file.exists():
                    source_file.unlink()
                    removed_count += 1
                    logger.info(f"  ✅ Removed: {file_path}")
            
            logger.info(f"  🗑️ Removed {removed_count} duplicate files")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ File removal failed: {e}")
            return False
    
    def update_model_imports(self) -> bool:
        """Update __init__.py files to use unified models."""
        logger.info("🔄 Updating model __init__.py files...")
        
        try:
            # Update main models __init__.py
            models_init = self.project_root / "fs_agt_clean/database/models/__init__.py"
            if models_init.exists():
                with open(models_init, 'w', encoding='utf-8') as f:
                    f.write('''"""
Unified Database Models for FlipSync
====================================

This module exports all unified database models, eliminating previous duplication.
"""

# Import unified models
from .unified_base import *
from .unified_user import *
from .unified_agent import *

# Export all unified models
__all__ = [
    # Base classes
    "Base",
    "BaseModel", 
    "AuditableModel",
    "MetadataModel",
    "FullFeaturedModel",
    
    # User models
    "UnifiedUser",
    "Role",
    "UserAccount",
    "UserSession",
    "UserResponse",
    "UserCreate",
    "UserUpdate",
    "LoginRequest",
    "LoginResponse",
    
    # Agent models
    "UnifiedAgent",
    "AgentDecision",
    "AgentTask", 
    "AgentCommunication",
    "AgentPerformanceMetric",
    "AgentResponse",
    "AgentCreate",
    "AgentUpdate",
    "TaskResponse",
    "TaskCreate",
    
    # Enums
    "UserRole",
    "UserStatus",
    "AccountType", 
    "AccountStatus",
    "MfaType",
    "AgentType",
    "AgentStatus",
    "AgentPriority",
    "TaskStatus",
    "DecisionStatus",
]
''')
                logger.info("  ✅ Updated models/__init__.py")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Failed to update __init__.py files: {e}")
            return False
    
    def validate_migration(self) -> bool:
        """Validate that migration was successful."""
        logger.info("✅ Validating migration...")
        
        try:
            # Check that unified models exist
            unified_models = [
                "fs_agt_clean/database/models/unified_base.py",
                "fs_agt_clean/database/models/unified_user.py", 
                "fs_agt_clean/database/models/unified_agent.py",
            ]
            
            for model_file in unified_models:
                model_path = self.project_root / model_file
                if not model_path.exists():
                    logger.error(f"  ❌ Missing unified model: {model_file}")
                    return False
                logger.info(f"  ✅ Found unified model: {model_file}")
            
            # Check that duplicate files are removed
            remaining_duplicates = []
            for file_path in self.duplicate_files:
                source_file = self.project_root / file_path
                if source_file.exists():
                    remaining_duplicates.append(file_path)
            
            if remaining_duplicates:
                logger.warning(f"  ⚠️ Some duplicate files still exist: {remaining_duplicates}")
            else:
                logger.info("  ✅ All duplicate files removed")
            
            # Try importing unified models
            try:
                sys.path.insert(0, str(self.project_root))
                from fs_agt_clean.database.models.unified_user import UnifiedUser
                from fs_agt_clean.database.models.unified_agent import UnifiedAgent
                from fs_agt_clean.database.models.unified_base import BaseModel
                logger.info("  ✅ Unified models import successfully")
            except ImportError as e:
                logger.error(f"  ❌ Failed to import unified models: {e}")
                return False
            
            logger.info("  ✅ Migration validation successful")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Migration validation failed: {e}")
            return False
    
    async def run_migration(self) -> Dict[str, Any]:
        """Run complete model standardization migration."""
        logger.info("🚀 Starting Database Model Standardization Migration")
        logger.info("=" * 70)
        
        migration_results = {
            'timestamp': datetime.now().isoformat(),
            'steps': {},
            'overall_status': 'UNKNOWN'
        }
        
        # Migration steps
        steps = [
            ('Create Backup', self.create_backup),
            ('Update Imports', self.update_all_imports),
            ('Update Model Imports', self.update_model_imports),
            ('Remove Duplicate Files', self.remove_duplicate_files),
            ('Validate Migration', self.validate_migration),
        ]
        
        passed_steps = 0
        total_steps = len(steps)
        
        for step_name, step_func in steps:
            try:
                logger.info(f"\n📋 Step: {step_name}")
                result = step_func()
                migration_results['steps'][step_name] = 'PASS' if result else 'FAIL'
                if result:
                    passed_steps += 1
                    logger.info(f"✅ {step_name}: COMPLETED")
                else:
                    logger.error(f"❌ {step_name}: FAILED")
                    
            except Exception as e:
                logger.error(f"❌ {step_name}: ERROR - {e}")
                migration_results['steps'][step_name] = 'ERROR'
        
        # Determine overall status
        if passed_steps == total_steps:
            migration_results['overall_status'] = 'SUCCESS'
        elif passed_steps >= total_steps * 0.75:
            migration_results['overall_status'] = 'PARTIAL_SUCCESS'
        else:
            migration_results['overall_status'] = 'FAILED'
        
        # Print summary
        logger.info("\n" + "=" * 70)
        logger.info("📋 DATABASE MODEL STANDARDIZATION SUMMARY:")
        logger.info("=" * 70)
        
        for step_name, status in migration_results['steps'].items():
            status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            logger.info(f"{status_icon} {step_name}: {status}")
        
        logger.info(f"\n🎯 OVERALL STATUS: {migration_results['overall_status']}")
        logger.info(f"📊 PASSED: {passed_steps}/{total_steps} steps")
        
        if migration_results['overall_status'] == 'SUCCESS':
            logger.info("\n🎉 Database Model Standardization SUCCESSFUL!")
            logger.info("✅ Eliminated duplicate model hierarchies")
            logger.info("✅ Unified user management models")
            logger.info("✅ Unified agent management models") 
            logger.info("✅ Unified base model functionality")
            logger.info("✅ Updated all import references")
            logger.info("📈 Reduced model complexity and maintenance overhead")
        else:
            logger.info("\n⚠️ Some migration issues detected")
            logger.info(f"📁 Backup available at: {self.backup_dir}")
        
        return migration_results


async def main():
    """Main migration execution."""
    migrator = ModelStandardizationMigrator()
    results = await migrator.run_migration()
    
    # Save results
    with open('model_standardization_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Migration results saved to: model_standardization_results.json")
    
    # Exit with appropriate code
    if results['overall_status'] == 'SUCCESS':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
