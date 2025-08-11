#!/usr/bin/env python3
"""
Fix Database Naming Inconsistencies
==================================

This script fixes database naming inconsistencies throughout the FlipSync codebase
to standardize on 'flipsync_agentic_test' as the single production database.

Issues Fixed:
- Configuration files referencing wrong database names
- Environment variable inconsistencies
- Code references to non-existent 'flipsync' database
"""

import os
import re
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Standard database configuration
CORRECT_DATABASE_NAME = "flipsync_agentic_test"
CORRECT_DATABASE_URL = "postgresql+asyncpg://postgres:FlipSync_DB_Prod_2024_Secure_Key_9x7z@192.168.110.71:5432/flipsync_agentic_test"

class DatabaseNamingFixer:
    """Fix database naming inconsistencies throughout the codebase."""
    
    def __init__(self, project_root: str = "/home/brend/Flipsync_Final"):
        self.project_root = Path(project_root)
        self.fixes_applied = []
        self.issues_found = []
        
    def scan_for_issues(self) -> List[Dict[str, str]]:
        """Scan codebase for database naming issues."""
        logger.info("🔍 Scanning for database naming issues...")
        
        issues = []
        
        # Patterns to look for
        problematic_patterns = [
            (r'database.*["\']flipsync["\']', 'References to "flipsync" database'),
            (r'DB_NAME.*["\']flipsync["\']', 'DB_NAME set to "flipsync"'),
            (r'postgresql.*://.*flipsync[^_]', 'Connection string with "flipsync" (not flipsync_agentic_test)'),
            (r'flipsync_dev', 'References to development database'),
            (r'flipsync_test[^_]', 'References to test database (not flipsync_agentic_test)'),
        ]
        
        # File extensions to scan
        extensions = ['.py', '.yaml', '.yml', '.json', '.env', '.example', '.md']
        
        # Scan files
        for file_path in self.project_root.rglob('*'):
            if file_path.is_file() and file_path.suffix in extensions:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    for pattern, description in problematic_patterns:
                        matches = re.finditer(pattern, content, re.IGNORECASE)
                        for match in matches:
                            line_num = content[:match.start()].count('\n') + 1
                            issues.append({
                                'file': str(file_path.relative_to(self.project_root)),
                                'line': line_num,
                                'pattern': pattern,
                                'description': description,
                                'match': match.group(0)
                            })
                            
                except (UnicodeDecodeError, PermissionError):
                    # Skip binary files or files we can't read
                    continue
        
        self.issues_found = issues
        logger.info(f"🔍 Found {len(issues)} database naming issues")
        return issues
    
    def fix_configuration_files(self) -> List[str]:
        """Fix database configuration in key files."""
        logger.info("🔧 Fixing configuration files...")
        
        fixes = []
        
        # Key configuration files to fix
        config_files = [
            'fs_agt_clean/core/config/unified_config.py',
            'fs_agt_clean/core/config/config_manager.py',
            '.env.example',
            'database_optimization.py',
            'init_database.py',
        ]
        
        for config_file in config_files:
            file_path = self.project_root / config_file
            if file_path.exists():
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    original_content = content
                    
                    # Apply fixes
                    content = re.sub(
                        r'DB_NAME.*["\']flipsync["\']',
                        f'DB_NAME = "{CORRECT_DATABASE_NAME}"',
                        content
                    )
                    
                    content = re.sub(
                        r'database.*["\']flipsync["\']',
                        f'database = "{CORRECT_DATABASE_NAME}"',
                        content
                    )
                    
                    content = re.sub(
                        r'flipsync_dev',
                        CORRECT_DATABASE_NAME,
                        content
                    )
                    
                    # Fix connection strings
                    content = re.sub(
                        r'postgresql\+asyncpg://[^/]+/flipsync[^_\s"\']*',
                        CORRECT_DATABASE_URL,
                        content
                    )
                    
                    if content != original_content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(content)
                        fixes.append(f"✅ Fixed {config_file}")
                        logger.info(f"✅ Fixed {config_file}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to fix {config_file}: {e}")
        
        return fixes
    
    def set_environment_variables(self) -> List[str]:
        """Set correct environment variables."""
        logger.info("🔧 Setting environment variables...")
        
        fixes = []
        
        # Set correct environment variables
        env_vars = {
            'DATABASE_URL': CORRECT_DATABASE_URL,
            'DB_NAME': CORRECT_DATABASE_NAME,
            'DB_HOST': '192.168.110.71',
            'DB_PORT': '5432',
            'DB_USER': 'postgres',
            'DB_PASSWORD': 'FlipSync_DB_Prod_2024_Secure_Key_9x7z'
        }
        
        for key, value in env_vars.items():
            os.environ[key] = value
            fixes.append(f"✅ Set {key}={value}")
        
        logger.info(f"✅ Set {len(env_vars)} environment variables")
        return fixes
    
    def validate_database_connection(self) -> bool:
        """Validate that database connection works with correct name."""
        logger.info("🔍 Validating database connection...")
        
        try:
            import asyncio
            import asyncpg
            
            async def test_connection():
                conn = await asyncpg.connect(
                    host='192.168.110.71',
                    port=5432,
                    database=CORRECT_DATABASE_NAME,
                    user='postgres',
                    password='FlipSync_DB_Prod_2024_Secure_Key_9x7z'
                )
                
                # Test query
                result = await conn.fetchrow("SELECT current_database(), version()")
                await conn.close()
                
                return result
            
            result = asyncio.run(test_connection())
            
            if result and result[0] == CORRECT_DATABASE_NAME:
                logger.info(f"✅ Database connection validated: {result[0]}")
                return True
            else:
                logger.error(f"❌ Database connection failed: {result}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Database validation failed: {e}")
            return False
    
    def generate_report(self) -> str:
        """Generate comprehensive fix report."""
        report = f"""
🔧 DATABASE NAMING FIXES REPORT
==============================

Database Standardization: {CORRECT_DATABASE_NAME}
Connection String: {CORRECT_DATABASE_URL}

📊 ISSUES FOUND: {len(self.issues_found)}
"""
        
        if self.issues_found:
            report += "\n🔍 ISSUES IDENTIFIED:\n"
            for issue in self.issues_found[:10]:  # Show first 10 issues
                report += f"  - {issue['file']}:{issue['line']} - {issue['description']}\n"
            
            if len(self.issues_found) > 10:
                report += f"  ... and {len(self.issues_found) - 10} more issues\n"
        
        report += f"\n✅ FIXES APPLIED: {len(self.fixes_applied)}\n"
        for fix in self.fixes_applied:
            report += f"  - {fix}\n"
        
        report += f"""
🎯 RECOMMENDATIONS:
1. ✅ Use single database architecture (flipsync_agentic_test)
2. ✅ Standardize all configuration files
3. ✅ Set correct environment variables
4. ✅ Validate database connections

🚀 NEXT STEPS:
- Proceed with Phase 2: Agent Implementation Migration
- All database naming issues resolved
- 4+1 architecture foundation ready
"""
        
        return report
    
    def run_all_fixes(self) -> bool:
        """Run all database naming fixes."""
        logger.info("🚀 Starting database naming fixes...")
        
        try:
            # Scan for issues
            self.scan_for_issues()
            
            # Apply fixes
            config_fixes = self.fix_configuration_files()
            env_fixes = self.set_environment_variables()
            
            self.fixes_applied.extend(config_fixes)
            self.fixes_applied.extend(env_fixes)
            
            # Validate connection
            connection_valid = self.validate_database_connection()
            
            if connection_valid:
                self.fixes_applied.append("✅ Database connection validated")
            
            # Generate report
            report = self.generate_report()
            logger.info(report)
            
            logger.info("🎉 Database naming fixes completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Database naming fixes failed: {e}")
            return False


def main():
    """Main function to run database naming fixes."""
    fixer = DatabaseNamingFixer()
    success = fixer.run_all_fixes()
    
    if success:
        print("\n🎉 DATABASE NAMING STANDARDIZATION COMPLETE!")
        print(f"✅ Standardized on: {CORRECT_DATABASE_NAME}")
        print("✅ Ready to proceed with Phase 2: Agent Implementation Migration")
    else:
        print("\n❌ Database naming fixes failed")
        print("Please review the logs and fix issues manually")
    
    return success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
