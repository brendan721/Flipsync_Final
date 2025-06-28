#!/usr/bin/env python3
"""
Test Database Model Standardization
===================================

Validates that the database model standardization is complete and working correctly.
Tests unified models, backward compatibility, and elimination of duplicates.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from typing import Dict, Any

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configure logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseModelStandardizationTest:
    """Test the standardized database models."""
    
    def __init__(self):
        """Initialize test configuration."""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        
    def test_unified_models_import(self) -> bool:
        """Test that unified models import correctly."""
        logger.info("🔧 Testing unified models import...")
        
        try:
            # Test unified user models
            from fs_agt_clean.database.models.unified_user import (
                UnifiedUser, User, UserRole, UserStatus, UserAccount, UserSession
            )
            
            # Test unified agent models
            from fs_agt_clean.database.models.unified_agent import (
                UnifiedAgent, Agent, AgentType, AgentStatus, AgentDecision, AgentTask
            )
            
            # Test unified base models
            from fs_agt_clean.database.models.unified_base import (
                Base, BaseModel, TimestampMixin, UUIDMixin
            )
            
            logger.info("  ✅ All unified models import successfully")
            logger.info(f"  📝 UnifiedUser table: {UnifiedUser.__tablename__}")
            logger.info(f"  📝 UnifiedAgent table: {UnifiedAgent.__tablename__}")
            logger.info(f"  📝 User alias works: {User.__tablename__}")
            logger.info(f"  📝 Agent alias works: {Agent.__tablename__}")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Unified models import failed: {e}")
            return False
    
    def test_backward_compatibility(self) -> bool:
        """Test backward compatibility aliases."""
        logger.info("🔄 Testing backward compatibility aliases...")
        
        try:
            # Test that old class names still work
            from fs_agt_clean.database.models.unified_user import User, UserRole, UserStatus
            from fs_agt_clean.database.models.unified_agent import Agent, AgentType, AgentStatus
            
            # Test enum values
            assert UserRole.ADMIN == "admin"
            assert UserStatus.ACTIVE == "active"
            assert AgentType.MARKET == "market"
            assert AgentStatus.RUNNING == "running"
            
            logger.info("  ✅ Backward compatibility aliases working")
            logger.info("  📝 Old class names (User, Agent) still work")
            logger.info("  📝 Enum values preserved")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Backward compatibility test failed: {e}")
            return False
    
    def test_duplicate_files_removed(self) -> bool:
        """Test that duplicate model files were removed."""
        logger.info("🗑️ Testing duplicate files removal...")
        
        duplicate_files = [
            "fs_agt_clean/database/models/user.py",
            "fs_agt_clean/database/models/users.py", 
            "fs_agt_clean/core/models/database/auth_user.py",
            "fs_agt_clean/database/models/agents.py",
            "fs_agt_clean/core/models/database/agents.py",
            "fs_agt_clean/database/models/base.py",
            "fs_agt_clean/core/models/database/base.py",
        ]
        
        try:
            removed_count = 0
            for file_path in duplicate_files:
                full_path = os.path.join(self.project_root, file_path)
                if not os.path.exists(full_path):
                    removed_count += 1
                    logger.info(f"  ✅ Removed: {file_path}")
                else:
                    logger.warning(f"  ⚠️ Still exists: {file_path}")
            
            if removed_count == len(duplicate_files):
                logger.info("  ✅ All duplicate files successfully removed")
                return True
            else:
                logger.warning(f"  ⚠️ {len(duplicate_files) - removed_count} duplicate files still exist")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Duplicate files check failed: {e}")
            return False
    
    def test_unified_files_exist(self) -> bool:
        """Test that unified model files exist."""
        logger.info("📁 Testing unified files existence...")
        
        unified_files = [
            "fs_agt_clean/database/models/unified_user.py",
            "fs_agt_clean/database/models/unified_agent.py",
            "fs_agt_clean/database/models/unified_base.py",
        ]
        
        try:
            for file_path in unified_files:
                full_path = os.path.join(self.project_root, file_path)
                if os.path.exists(full_path):
                    logger.info(f"  ✅ Found: {file_path}")
                else:
                    logger.error(f"  ❌ Missing: {file_path}")
                    return False
            
            logger.info("  ✅ All unified files exist")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Unified files check failed: {e}")
            return False
    
    def test_model_functionality(self) -> bool:
        """Test basic model functionality."""
        logger.info("⚙️ Testing model functionality...")
        
        try:
            from fs_agt_clean.database.models.unified_user import UnifiedUser, UserRole, UserStatus
            from fs_agt_clean.database.models.unified_agent import UnifiedAgent, AgentType, AgentStatus
            
            # Test user model creation (without database)
            user_data = {
                "email": "test@example.com",
                "username": "testuser",
                "password": "SecurePassword123!"
            }
            
            # Test that we can create model instances
            user = UnifiedUser(**user_data)
            assert user.email == "test@example.com"
            assert user.username == "testuser"
            assert user.verify_password("SecurePassword123!")
            
            logger.info("  ✅ User model functionality working")
            
            # Test agent model
            agent = UnifiedAgent(
                name="Test Agent",
                agent_type=AgentType.MARKET,
                status=AgentStatus.RUNNING
            )
            assert agent.name == "Test Agent"
            assert agent.agent_type == AgentType.MARKET
            
            logger.info("  ✅ Agent model functionality working")
            logger.info("  📝 Model instances can be created")
            logger.info("  📝 Password hashing/verification works")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Model functionality test failed: {e}")
            return False
    
    def test_import_updates(self) -> bool:
        """Test that import updates were successful."""
        logger.info("🔄 Testing import updates...")
        
        try:
            # Test that we can import from the new unified location
            from fs_agt_clean.database.models import UnifiedUser, UnifiedAgent, BaseModel
            
            logger.info("  ✅ Can import from unified models package")
            
            # Test that the models are the same
            from fs_agt_clean.database.models.unified_user import UnifiedUser as DirectUser
            from fs_agt_clean.database.models.unified_agent import UnifiedAgent as DirectAgent
            
            assert UnifiedUser is DirectUser
            assert UnifiedAgent is DirectAgent
            
            logger.info("  ✅ Package imports match direct imports")
            logger.info("  📝 Import consolidation successful")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Import updates test failed: {e}")
            return False
    
    async def run_standardization_test(self) -> Dict[str, Any]:
        """Run complete database model standardization test."""
        logger.info("🚀 Starting Database Model Standardization Test")
        logger.info("=" * 70)
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_status': 'UNKNOWN'
        }
        
        # Run all tests
        tests = [
            ('Unified Models Import', self.test_unified_models_import),
            ('Backward Compatibility', self.test_backward_compatibility),
            ('Duplicate Files Removed', self.test_duplicate_files_removed),
            ('Unified Files Exist', self.test_unified_files_exist),
            ('Model Functionality', self.test_model_functionality),
            ('Import Updates', self.test_import_updates),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results['tests'][test_name] = 'PASS' if result else 'FAIL'
                if result:
                    passed_tests += 1
                print()  # Add spacing between tests
            except Exception as e:
                logger.error(f"Test '{test_name}' failed with exception: {e}")
                test_results['tests'][test_name] = 'ERROR'
                print()
        
        # Determine overall status
        if passed_tests == total_tests:
            test_results['overall_status'] = 'PASS'
        elif passed_tests >= total_tests * 0.75:
            test_results['overall_status'] = 'PARTIAL_PASS'
        else:
            test_results['overall_status'] = 'FAIL'
        
        # Print summary
        logger.info("=" * 70)
        logger.info("📋 DATABASE MODEL STANDARDIZATION TEST SUMMARY:")
        logger.info("=" * 70)
        
        for test_name, status in test_results['tests'].items():
            status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            logger.info(f"{status_icon} {test_name}: {status}")
        
        logger.info(f"\n🎯 OVERALL STATUS: {test_results['overall_status']}")
        logger.info(f"📊 PASSED: {passed_tests}/{total_tests} tests")
        
        if test_results['overall_status'] == 'PASS':
            logger.info("\n🎉 Database Model Standardization SUCCESSFUL!")
            logger.info("✅ Unified user management models")
            logger.info("✅ Unified agent management models") 
            logger.info("✅ Unified base model functionality")
            logger.info("✅ Backward compatibility maintained")
            logger.info("✅ Duplicate files eliminated")
            logger.info("✅ Import references updated")
            logger.info("📈 Reduced model complexity and maintenance overhead")
        else:
            logger.info("\n⚠️ Some standardization issues detected")
        
        return test_results


async def main():
    """Main test execution."""
    test_runner = DatabaseModelStandardizationTest()
    results = await test_runner.run_standardization_test()
    
    # Save results
    with open('database_model_standardization_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Test results saved to: database_model_standardization_results.json")
    
    # Exit with appropriate code
    if results['overall_status'] == 'PASS':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
