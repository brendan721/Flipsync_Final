#!/usr/bin/env python3
"""
Validate Proxmox Database Configuration for FlipSync
====================================================

This script validates that all FlipSync database configurations have been
properly updated for Proxmox deployment without requiring actual database connectivity.
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

class ProxmoxConfigValidator:
    def __init__(self):
        """Initialize the configuration validator."""
        self.project_root = Path("/home/brend/Flipsync_Final")
        self.issues_found = []
        self.files_checked = 0
        self.digitalocean_references = []
        
    def check_file_for_digitalocean_refs(self, file_path: Path) -> List[Tuple[int, str]]:
        """Check a file for DigitalOcean database references."""
        digitalocean_refs = []
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            lines = content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                # Check for DigitalOcean IP
                if '174.138.77.110' in line:
                    digitalocean_refs.append((line_num, line.strip()))
                
                # Check for old IP references
                if '192.168.110.71' in line:
                    digitalocean_refs.append((line_num, f"OLD_IP: {line.strip()}"))
                    
        except Exception as e:
            self.issues_found.append(f"Error reading {file_path}: {e}")
            
        return digitalocean_refs
    
    def check_database_urls(self, file_path: Path) -> List[str]:
        """Check for proper database URL configuration."""
        issues = []
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Check for correct database name
            if 'flipsync_agentic_test' not in content and 'DATABASE_URL' in content:
                issues.append(f"May be missing correct database name 'flipsync_agentic_test'")
            
            # Check for localhost in database URLs
            if 'postgresql' in content and '@localhost:' not in content and 'DATABASE_URL' in content:
                if '174.138.77.110' in content or '192.168.110.71' in content:
                    issues.append(f"Contains non-localhost database host")
            
            # Check for correct password
            if 'FlipSync_DB_Prod_2024_Secure_Key_9x7z' not in content and 'postgresql' in content:
                if 'password' in content.lower():
                    issues.append(f"May be missing correct database password")
                    
        except Exception as e:
            issues.append(f"Error checking database URLs: {e}")
            
        return issues
    
    def validate_env_files(self) -> Dict[str, any]:
        """Validate environment configuration files."""
        print("🔍 Validating environment configuration files...")
        
        env_files = [
            self.project_root / ".env.example",
            self.project_root / ".env.proxmox",
        ]
        
        results = {}
        
        for env_file in env_files:
            if env_file.exists():
                print(f"   Checking {env_file.name}...")
                
                content = env_file.read_text()
                file_results = {
                    'exists': True,
                    'has_database_url': 'DATABASE_URL=' in content,
                    'uses_localhost': '@localhost:' in content,
                    'has_correct_db_name': 'flipsync_agentic_test' in content,
                    'has_correct_password': 'FlipSync_DB_Prod_2024_Secure_Key_9x7z' in content,
                    'no_digitalocean_refs': '174.138.77.110' not in content,
                }
                
                results[env_file.name] = file_results
                
                # Print status
                status = "✅" if all(file_results.values()) else "⚠️"
                print(f"   {status} {env_file.name}: {sum(file_results.values())}/{len(file_results)} checks passed")
                
            else:
                results[env_file.name] = {'exists': False}
                print(f"   ❌ {env_file.name}: File not found")
        
        return results
    
    def scan_codebase_for_digitalocean_refs(self) -> Dict[str, List]:
        """Scan the entire codebase for DigitalOcean references."""
        print("🔍 Scanning codebase for DigitalOcean references...")
        
        # File patterns to check
        patterns = [
            "**/*.py",
            "**/*.js", 
            "**/*.yaml",
            "**/*.yml",
            "**/*.json",
            "**/*.env*",
            "**/*.md",
        ]
        
        # Directories to skip
        skip_dirs = {
            'venv_agentic', 'node_modules', '.git', '__pycache__', 
            'migration_backups', '.pytest_cache', 'build', 'dist'
        }
        
        digitalocean_files = {}
        
        for pattern in patterns:
            for file_path in self.project_root.glob(pattern):
                # Skip if in excluded directory
                if any(skip_dir in file_path.parts for skip_dir in skip_dirs):
                    continue
                
                if file_path.is_file():
                    self.files_checked += 1
                    refs = self.check_file_for_digitalocean_refs(file_path)
                    
                    if refs:
                        relative_path = file_path.relative_to(self.project_root)
                        digitalocean_files[str(relative_path)] = refs
        
        return digitalocean_files
    
    def validate_database_config_files(self) -> Dict[str, List]:
        """Validate specific database configuration files."""
        print("🔍 Validating database configuration files...")
        
        db_config_files = [
            "fs_agt_clean/core/config/config.yaml",
            "fs_agt_clean/database/init_auth_db.py",
            "fs_agt_clean/core/db/optimized_database.py",
            "scripts/database/init_database.py",
            "scripts/database/fix_database_connection.py",
            "scripts/fix_database_config.py",
        ]
        
        validation_results = {}
        
        for file_path_str in db_config_files:
            file_path = self.project_root / file_path_str
            
            if file_path.exists():
                print(f"   Checking {file_path.name}...")
                issues = self.check_database_urls(file_path)
                digitalocean_refs = self.check_file_for_digitalocean_refs(file_path)
                
                validation_results[file_path_str] = {
                    'issues': issues,
                    'digitalocean_refs': digitalocean_refs,
                    'status': 'clean' if not issues and not digitalocean_refs else 'needs_attention'
                }
                
                status = "✅" if not issues and not digitalocean_refs else "⚠️"
                print(f"   {status} {file_path.name}: {len(issues)} issues, {len(digitalocean_refs)} DigitalOcean refs")
                
            else:
                validation_results[file_path_str] = {'status': 'missing'}
                print(f"   ❌ {file_path.name}: File not found")
        
        return validation_results
    
    def generate_report(self, env_results: Dict, digitalocean_files: Dict, db_config_results: Dict):
        """Generate a comprehensive validation report."""
        print("\n" + "=" * 80)
        print("📊 PROXMOX DATABASE CONFIGURATION VALIDATION REPORT")
        print("=" * 80)
        
        # Environment files summary
        print("\n🔧 ENVIRONMENT CONFIGURATION:")
        for file_name, results in env_results.items():
            if results.get('exists', False):
                passed = sum(v for v in results.values() if isinstance(v, bool))
                total = len([v for v in results.values() if isinstance(v, bool)])
                status = "✅" if passed == total else "⚠️"
                print(f"   {status} {file_name}: {passed}/{total} checks passed")
            else:
                print(f"   ❌ {file_name}: Missing")
        
        # DigitalOcean references summary
        print(f"\n🔍 DIGITALOCEAN REFERENCES SCAN:")
        print(f"   Files scanned: {self.files_checked}")
        print(f"   Files with DigitalOcean references: {len(digitalocean_files)}")
        
        if digitalocean_files:
            print("   ⚠️  Files needing attention:")
            for file_path, refs in digitalocean_files.items():
                print(f"      - {file_path}: {len(refs)} references")
        else:
            print("   ✅ No DigitalOcean references found")
        
        # Database configuration summary
        print(f"\n🗄️  DATABASE CONFIGURATION FILES:")
        clean_files = sum(1 for r in db_config_results.values() if r.get('status') == 'clean')
        total_files = len(db_config_results)
        print(f"   Clean files: {clean_files}/{total_files}")
        
        for file_path, results in db_config_results.items():
            status_icon = {
                'clean': '✅',
                'needs_attention': '⚠️',
                'missing': '❌'
            }.get(results.get('status'), '❓')
            
            print(f"   {status_icon} {Path(file_path).name}: {results.get('status', 'unknown')}")
        
        # Overall assessment
        print(f"\n🎯 OVERALL ASSESSMENT:")
        
        total_issues = (
            len(digitalocean_files) +
            sum(1 for r in env_results.values() if not r.get('exists') or not all(v for v in r.values() if isinstance(v, bool))) +
            sum(1 for r in db_config_results.values() if r.get('status') != 'clean')
        )
        
        if total_issues == 0:
            print("   🎉 EXCELLENT: All configurations are ready for Proxmox deployment!")
            print("   ✅ No DigitalOcean references found")
            print("   ✅ All database configurations use localhost")
            print("   ✅ Environment files are properly configured")
        else:
            print(f"   ⚠️  {total_issues} issues found that need attention")
            print("   📋 Review the detailed findings above")
        
        print("\n🚀 NEXT STEPS FOR PROXMOX DEPLOYMENT:")
        print("   1. Copy .env.proxmox to .env on Proxmox VM")
        print("   2. Install PostgreSQL on Proxmox VM 201")
        print("   3. Run setup_proxmox_database_schema.py")
        print("   4. Deploy FlipSync application")
        print("   5. Test all services with validate_proxmox_connectivity.py")
        
        return total_issues == 0

    def run_validation(self):
        """Run the complete validation process."""
        print("🚀 FlipSync Proxmox Database Configuration Validation")
        print("=" * 60)
        
        # Validate environment files
        env_results = self.validate_env_files()
        
        # Scan for DigitalOcean references
        digitalocean_files = self.scan_codebase_for_digitalocean_refs()
        
        # Validate database configuration files
        db_config_results = self.validate_database_config_files()
        
        # Generate comprehensive report
        success = self.generate_report(env_results, digitalocean_files, db_config_results)
        
        return success

def main():
    """Main validation function."""
    validator = ProxmoxConfigValidator()
    success = validator.run_validation()
    return 0 if success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
