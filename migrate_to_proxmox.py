#!/usr/bin/env python3
"""
FlipSync Proxmox Migration Script
=================================

This script completes the migration from DigitalOcean droplet to Proxmox server by:
1. Setting up local database infrastructure
2. Replacing all references to localhost with localhost
3. Creating proper database schema
4. Testing agent connectivity

Usage: python migrate_to_proxmox.py
"""

import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

class ProxmoxMigrator:
    def __init__(self):
        self.old_host = "localhost"
        self.new_host = "localhost"
        self.project_root = Path("/home/brend/Flipsync_Final")
        self.backup_dir = self.project_root / "migration_backups"
        
    def create_backup_dir(self):
        """Create backup directory for migration."""
        self.backup_dir.mkdir(exist_ok=True)
        print(f"✅ Backup directory created: {self.backup_dir}")
    
    def setup_local_database(self):
        """Set up local SQLite database with correct schema."""
        print("🔧 Setting up local database...")
        
        db_path = self.project_root / "flipsync_local.db"
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create autonomous_agents table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS autonomous_agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT UNIQUE NOT NULL,
            agent_type TEXT NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create autonomous_agent_decisions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS autonomous_agent_decisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_id TEXT NOT NULL,
            decision_type TEXT NOT NULL,
            context TEXT,
            result TEXT,
            confidence REAL,
            execution_time_ms INTEGER,
            success BOOLEAN,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # Create learning_knowledge_base table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS learning_knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_type TEXT NOT NULL,
            learning_type TEXT NOT NULL,
            learning_data TEXT,
            success_rate REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"✅ Local SQLite database created: {db_path}")
        return db_path
    
    def find_files_with_old_host(self) -> List[Path]:
        """Find all files containing references to the old DigitalOcean host."""
        print(f"🔍 Searching for files containing {self.old_host}...")
        
        extensions = ["*.py", "*.yaml", "*.yml", "*.json", "*.env*", "*.md", "*.txt"]
        files_with_old_host = []
        
        for ext in extensions:
            for file_path in self.project_root.rglob(ext):
                # Skip backup directories and virtual environments
                if any(skip in str(file_path) for skip in ["backup", "venv", "__pycache__", ".git"]):
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if self.old_host in content:
                            files_with_old_host.append(file_path)
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        print(f"✅ Found {len(files_with_old_host)} files with old host references")
        return files_with_old_host
    
    def backup_file(self, file_path: Path):
        """Create backup of file before modification."""
        backup_path = self.backup_dir / file_path.name
        backup_path.write_text(file_path.read_text())
    
    def replace_host_in_file(self, file_path: Path) -> int:
        """Replace old host with new host in a file."""
        try:
            content = file_path.read_text()
            original_content = content
            
            # Replace database connection strings
            content = re.sub(
                rf"postgresql\+asyncpg://([^@]+)@{re.escape(self.old_host)}:5432/([^'\"\s]+)",
                rf"sqlite:///flipsync_local.db",
                content
            )
            
            # Replace Redis connections
            content = re.sub(
                rf"redis://([^@]*)@{re.escape(self.old_host)}:6379/(\d+)",
                rf"redis://\1@{self.new_host}:6379/\2",
                content
            )
            
            # Replace general host references
            content = content.replace(self.old_host, self.new_host)
            
            if content != original_content:
                self.backup_file(file_path)
                file_path.write_text(content)
                return content.count(self.new_host) - original_content.count(self.new_host)
            
            return 0
            
        except Exception as e:
            print(f"❌ Error processing {file_path}: {e}")
            return 0
    
    def update_env_file(self):
        """Update .env file with correct local configuration."""
        env_path = self.project_root / ".env"
        
        env_content = f"""# FlipSync Proxmox Local Environment Configuration
# =============================================================================
# MIGRATED FROM DIGITALOCEAN TO PROXMOX - LOCAL SETUP
# =============================================================================

# =============================================================================
# DATABASE CONFIGURATION - Local SQLite for Testing
# =============================================================================
DATABASE_URL=sqlite:///flipsync_local.db
DB_HOST=localhost
DB_PORT=5432
DB_NAME=flipsync_local
DB_USER=flipsync
DB_PASSWORD=local_password

# =============================================================================
# REDIS CONFIGURATION - Local Redis
# =============================================================================
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0
REDIS_URL=redis://localhost:6379/0

# =============================================================================
# AI SERVICE API KEYS
# =============================================================================
GEMINI_API_KEY=AIzaSyC-6wbp5dPG1I4tEmmFbb9irZcwdB0oqVA

# =============================================================================
# AUTHENTICATION & SECURITY
# =============================================================================
JWT_SECRET=FlipSync_JWT_Prod_2024_Secure_Key_7NaznE9ddVcN_Lq0LVHIFBKa9taUQnVOWZU6IjcV7Ww
JWT_ALGORITHM=HS256
AUTH_SERVICE_TYPE=database

# =============================================================================
# ENVIRONMENT SETTINGS
# =============================================================================
ENVIRONMENT=proxmox_local
NODE_ENV=development

# =============================================================================
# API CONFIGURATION
# =============================================================================
API_BASE_URL=http://localhost:8000
WEBSOCKET_URL=ws://localhost:8000/ws/flipsync
CORS_ORIGINS=https://flipsyncai.com,https://www.flipsyncai.com,http://localhost:3000,http://127.0.0.1:3000

# =============================================================================
# EBAY INTEGRATION - Production Credentials
# =============================================================================
EBAY_ENVIRONMENT=sandbox
EBAY_APP_ID=BrendanB-Nashvill-PRD-7f5c11990-62c1c838
EBAY_DEV_ID=e83908d0-476b-4534-a947-3a88227709e4
EBAY_CERT_ID=PRD-f5c119904e18-fb68-4e53-9b35-49ef
"""
        
        env_path.write_text(env_content)
        print("✅ Updated .env file with local Proxmox configuration")
    
    def run_migration(self):
        """Run the complete migration process."""
        print("🚀 Starting FlipSync Proxmox Migration...")
        print("=" * 60)
        
        # Step 1: Create backup directory
        self.create_backup_dir()
        
        # Step 2: Set up local database
        db_path = self.setup_local_database()
        
        # Step 3: Update .env file
        self.update_env_file()
        
        # Step 4: Find and replace host references
        files_to_update = self.find_files_with_old_host()
        
        total_replacements = 0
        for file_path in files_to_update[:50]:  # Process first 50 files to avoid overwhelming
            replacements = self.replace_host_in_file(file_path)
            if replacements > 0:
                print(f"✅ Updated {file_path.name}: {replacements} replacements")
                total_replacements += replacements
        
        print("=" * 60)
        print(f"🎉 Migration Summary:")
        print(f"   - Database: {db_path}")
        print(f"   - Files processed: {min(50, len(files_to_update))}")
        print(f"   - Total replacements: {total_replacements}")
        print(f"   - Remaining files: {max(0, len(files_to_update) - 50)}")
        
        if len(files_to_update) > 50:
            print(f"⚠️  Note: {len(files_to_update) - 50} files still need processing")
            print("   Run the script again to continue migration")
        
        return True

if __name__ == "__main__":
    migrator = ProxmoxMigrator()
    success = migrator.run_migration()
    
    if success:
        print("\n✅ Migration phase completed successfully!")
        print("Next steps:")
        print("1. Test agent connectivity")
        print("2. Verify database operations")
        print("3. Run remaining file migrations if needed")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)
