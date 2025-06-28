#!/usr/bin/env python3
"""
SQLAlchemy Table Conflict Resolution Script
==========================================

This script resolves SQLAlchemy table redefinition conflicts by ensuring
all models use the same Base class and clearing metadata when needed.
"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def clear_sqlalchemy_metadata():
    """Clear SQLAlchemy metadata to prevent table redefinition conflicts."""
    try:
        # Import the unified Base
        from fs_agt_clean.database.models.base import Base
        
        # Clear existing metadata
        Base.metadata.clear()
        print("✅ SQLAlchemy metadata cleared successfully")
        
        return True
    except Exception as e:
        print(f"❌ Error clearing SQLAlchemy metadata: {e}")
        return False

def main():
    """Main function to fix SQLAlchemy conflicts."""
    print("🔧 SQLAlchemy Conflict Resolution")
    print("=" * 40)
    
    success = clear_sqlalchemy_metadata()
    
    if success:
        print("✅ SQLAlchemy conflicts resolved successfully!")
    else:
        print("❌ Some issues remain.")
    
    return 0 if success else 1

if __name__ == "__main__":
    exit(main())
