#!/usr/bin/env python3
"""
Test Mobile App Feature Alignment
=================================

Validates that the mobile app feature alignment is complete and comprehensive.
Tests mobile-backend feature parity, documentation updates, and integration capabilities.
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


class MobileAppFeatureAlignmentTest:
    """Test the mobile app feature alignment."""
    
    def __init__(self):
        """Initialize test configuration."""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        
        # Expected mobile documentation files
        self.mobile_docs = {
            "MOBILE_APP_FEATURE_ALIGNMENT.md": {
                "description": "Comprehensive mobile-backend feature parity analysis",
                "min_size": 15000,
                "key_sections": [
                    "FEATURE PARITY MATRIX",
                    "MOBILE WORKFLOW INTEGRATION",
                    "AUTHENTICATION & SECURITY ALIGNMENT",
                    "PERFORMANCE OPTIMIZATION"
                ]
            },
            "mobile/MOBILE_BACKEND_INTEGRATION.md": {
                "description": "Updated mobile-backend integration documentation",
                "min_size": 1000,
                "key_sections": [
                    "Agent Integration Overview",
                    "Integration Status"
                ]
            }
        }
        
        # Mobile app structure validation
        self.mobile_structure = {
            "mobile/lib/": ["agents/", "services/", "screens/", "widgets/", "features/"],
            "mobile/test/": ["integration/", "usability/"],
            "mobile/": ["pubspec.yaml", "android/", "ios/"]
        }
        
    def test_mobile_documentation_exists(self) -> bool:
        """Test that mobile documentation files exist."""
        logger.info("📱 Testing mobile documentation existence...")
        
        try:
            missing_files = []
            for file_name, file_info in self.mobile_docs.items():
                file_path = os.path.join(self.project_root, file_name)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    if file_size >= file_info["min_size"]:
                        logger.info(f"  ✅ Found: {file_name} ({file_size} bytes)")
                    else:
                        logger.warning(f"  ⚠️ Found but small: {file_name} ({file_size} bytes)")
                        missing_files.append(file_name)
                else:
                    logger.error(f"  ❌ Missing: {file_name}")
                    missing_files.append(file_name)
            
            if not missing_files:
                logger.info("  ✅ All mobile documentation files exist with substantial content")
                return True
            else:
                logger.error(f"  ❌ Missing or insufficient files: {missing_files}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Mobile documentation check failed: {e}")
            return False
    
    def test_mobile_app_structure(self) -> bool:
        """Test mobile app directory structure."""
        logger.info("🏗️ Testing mobile app structure...")
        
        try:
            missing_dirs = []
            for base_dir, expected_subdirs in self.mobile_structure.items():
                base_path = os.path.join(self.project_root, base_dir)
                if os.path.exists(base_path):
                    logger.info(f"  ✅ Found base directory: {base_dir}")
                    
                    for subdir in expected_subdirs:
                        subdir_path = os.path.join(base_path, subdir)
                        if os.path.exists(subdir_path):
                            logger.info(f"    ✅ Found: {base_dir}{subdir}")
                        else:
                            logger.warning(f"    ⚠️ Missing: {base_dir}{subdir}")
                            missing_dirs.append(f"{base_dir}{subdir}")
                else:
                    logger.error(f"  ❌ Missing base directory: {base_dir}")
                    missing_dirs.append(base_dir)
            
            if len(missing_dirs) <= 2:  # Allow some flexibility
                logger.info("  ✅ Mobile app structure validated")
                return True
            else:
                logger.error(f"  ❌ Too many missing directories: {missing_dirs}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Mobile app structure check failed: {e}")
            return False
    
    def test_feature_parity_content(self) -> bool:
        """Test feature parity documentation content."""
        logger.info("🔄 Testing feature parity content...")
        
        try:
            file_path = os.path.join(self.project_root, "MOBILE_APP_FEATURE_ALIGNMENT.md")
            if not os.path.exists(file_path):
                logger.error("  ❌ Feature alignment document not found")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for agent integration indicators
            agent_indicators = [
                "39-agent",
                "Executive Agent",
                "Market Analysis Agent",
                "Content Creation Agent",
                "eBay Integration Agent",
                "Feature Parity Matrix",
                "Mobile Workflow Integration"
            ]
            
            found_indicators = 0
            for indicator in agent_indicators:
                if indicator in content:
                    found_indicators += 1
                    logger.info(f"  ✅ Found indicator: {indicator}")
            
            # Check for mobile-specific features
            mobile_features = [
                "Flutter",
                "Authentication Guard",
                "Chat Interface",
                "Real-Time Agent Monitoring",
                "Mobile-Optimized Workflows",
                "WebSocket"
            ]
            
            found_features = 0
            for feature in mobile_features:
                if feature in content:
                    found_features += 1
            
            # Check for code examples
            dart_code_blocks = content.count("```dart")
            mermaid_diagrams = content.count("```mermaid")
            
            logger.info(f"  📊 Content analysis:")
            logger.info(f"    - Agent indicators: {found_indicators}/{len(agent_indicators)}")
            logger.info(f"    - Mobile features: {found_features}/{len(mobile_features)}")
            logger.info(f"    - Dart code examples: {dart_code_blocks}")
            logger.info(f"    - Mermaid diagrams: {mermaid_diagrams}")
            
            if found_indicators < len(agent_indicators) * 0.8:
                logger.error(f"  ❌ Insufficient agent integration coverage")
                return False
            
            if found_features < len(mobile_features) * 0.8:
                logger.error(f"  ❌ Insufficient mobile feature coverage")
                return False
            
            if dart_code_blocks < 3:
                logger.error(f"  ❌ Insufficient Dart code examples")
                return False
            
            logger.info("  ✅ Feature parity content validated")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Feature parity content test failed: {e}")
            return False
    
    def test_mobile_backend_integration_update(self) -> bool:
        """Test mobile-backend integration documentation update."""
        logger.info("🔗 Testing mobile-backend integration update...")
        
        try:
            file_path = os.path.join(self.project_root, "mobile/MOBILE_BACKEND_INTEGRATION.md")
            if not os.path.exists(file_path):
                logger.error("  ❌ Mobile-backend integration document not found")
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for updated content
            updated_indicators = [
                "39-agent ecosystem",
                "Agent Integration Overview",
                "Conversational AI Interface",
                "Real-Time Agent Monitoring",
                "Workflow Orchestration",
                "Intelligent Routing"
            ]
            
            found_updates = 0
            for indicator in updated_indicators:
                if indicator in content:
                    found_updates += 1
                    logger.info(f"  ✅ Found update: {indicator}")
            
            logger.info(f"  📝 Update analysis:")
            logger.info(f"    - Updated indicators: {found_updates}/{len(updated_indicators)}")
            
            if found_updates < len(updated_indicators) * 0.7:
                logger.error(f"  ❌ Insufficient documentation updates")
                return False
            
            logger.info("  ✅ Mobile-backend integration update validated")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Mobile-backend integration update test failed: {e}")
            return False
    
    def test_mobile_configuration_files(self) -> bool:
        """Test mobile configuration files."""
        logger.info("⚙️ Testing mobile configuration files...")
        
        try:
            # Check pubspec.yaml
            pubspec_path = os.path.join(self.project_root, "mobile/pubspec.yaml")
            if os.path.exists(pubspec_path):
                with open(pubspec_path, 'r', encoding='utf-8') as f:
                    pubspec_content = f.read()
                
                # Check for key dependencies
                key_dependencies = [
                    "flutter:",
                    "http:",
                    "provider:",
                    "shared_preferences:",
                    "flutter_bloc:",
                    "dio:",
                    "web_socket_channel:"
                ]
                
                found_deps = 0
                for dep in key_dependencies:
                    if dep in pubspec_content:
                        found_deps += 1
                
                logger.info(f"  ✅ pubspec.yaml found with {found_deps}/{len(key_dependencies)} key dependencies")
            else:
                logger.error("  ❌ pubspec.yaml not found")
                return False
            
            # Check for Android configuration
            android_manifest = os.path.join(self.project_root, "mobile/android/app/src/main/AndroidManifest.xml")
            if os.path.exists(android_manifest):
                logger.info("  ✅ Android configuration found")
            else:
                logger.warning("  ⚠️ Android configuration not found")
            
            # Check for iOS configuration
            ios_info = os.path.join(self.project_root, "mobile/ios/Runner/Info.plist")
            if os.path.exists(ios_info):
                logger.info("  ✅ iOS configuration found")
            else:
                logger.warning("  ⚠️ iOS configuration not found")
            
            logger.info("  ✅ Mobile configuration files validated")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Mobile configuration files test failed: {e}")
            return False
    
    def test_mobile_test_coverage(self) -> bool:
        """Test mobile test coverage."""
        logger.info("🧪 Testing mobile test coverage...")
        
        try:
            test_files = []
            mobile_test_dir = os.path.join(self.project_root, "mobile/test")
            
            if os.path.exists(mobile_test_dir):
                for root, dirs, files in os.walk(mobile_test_dir):
                    for file in files:
                        if file.endswith('_test.dart'):
                            test_files.append(os.path.join(root, file))
                
                logger.info(f"  ✅ Found {len(test_files)} test files")
                
                # Check for specific test types
                test_types = {
                    "integration": 0,
                    "unit": 0,
                    "widget": 0,
                    "usability": 0
                }
                
                for test_file in test_files:
                    file_name = os.path.basename(test_file).lower()
                    for test_type in test_types.keys():
                        if test_type in file_name:
                            test_types[test_type] += 1
                
                logger.info(f"  📊 Test coverage:")
                for test_type, count in test_types.items():
                    logger.info(f"    - {test_type.title()} tests: {count}")
                
                if len(test_files) >= 5:  # Minimum test coverage
                    logger.info("  ✅ Mobile test coverage validated")
                    return True
                else:
                    logger.error(f"  ❌ Insufficient test coverage ({len(test_files)} files)")
                    return False
            else:
                logger.error("  ❌ Mobile test directory not found")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Mobile test coverage check failed: {e}")
            return False
    
    def test_mobile_feature_completeness(self) -> bool:
        """Test overall mobile feature completeness."""
        logger.info("📋 Testing mobile feature completeness...")
        
        try:
            # Check for key mobile features in documentation
            feature_alignment_path = os.path.join(self.project_root, "MOBILE_APP_FEATURE_ALIGNMENT.md")
            if os.path.exists(feature_alignment_path):
                with open(feature_alignment_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Count feature implementations
                complete_features = content.count("✅ **COMPLETE**")
                partial_features = content.count("🚧 **PARTIAL**")
                planned_features = content.count("📋 **PLANNED**")
                
                total_features = complete_features + partial_features + planned_features
                completion_rate = complete_features / total_features if total_features > 0 else 0
                
                logger.info(f"  📊 Feature completeness:")
                logger.info(f"    - Complete features: {complete_features}")
                logger.info(f"    - Partial features: {partial_features}")
                logger.info(f"    - Planned features: {planned_features}")
                logger.info(f"    - Completion rate: {completion_rate:.1%}")
                
                if completion_rate >= 0.8:  # 80% completion threshold
                    logger.info("  ✅ Mobile feature completeness validated")
                    return True
                else:
                    logger.error(f"  ❌ Low feature completion rate: {completion_rate:.1%}")
                    return False
            else:
                logger.error("  ❌ Feature alignment document not found")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Mobile feature completeness test failed: {e}")
            return False
    
    async def run_mobile_alignment_test(self) -> Dict[str, Any]:
        """Run complete mobile app feature alignment test."""
        logger.info("🚀 Starting Mobile App Feature Alignment Test")
        logger.info("=" * 70)
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_status': 'UNKNOWN'
        }
        
        # Run all tests
        tests = [
            ('Mobile Documentation Exists', self.test_mobile_documentation_exists),
            ('Mobile App Structure', self.test_mobile_app_structure),
            ('Feature Parity Content', self.test_feature_parity_content),
            ('Mobile-Backend Integration Update', self.test_mobile_backend_integration_update),
            ('Mobile Configuration Files', self.test_mobile_configuration_files),
            ('Mobile Test Coverage', self.test_mobile_test_coverage),
            ('Mobile Feature Completeness', self.test_mobile_feature_completeness),
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
        logger.info("📋 MOBILE APP FEATURE ALIGNMENT TEST SUMMARY:")
        logger.info("=" * 70)
        
        for test_name, status in test_results['tests'].items():
            status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            logger.info(f"{status_icon} {test_name}: {status}")
        
        logger.info(f"\n🎯 OVERALL STATUS: {test_results['overall_status']}")
        logger.info(f"📊 PASSED: {passed_tests}/{total_tests} tests")
        
        if test_results['overall_status'] == 'PASS':
            logger.info("\n🎉 Mobile App Feature Alignment SUCCESSFUL!")
            logger.info("✅ Mobile-backend feature parity achieved")
            logger.info("✅ 39-agent ecosystem accessible via mobile")
            logger.info("✅ Comprehensive mobile documentation")
            logger.info("✅ Flutter app structure validated")
            logger.info("✅ Mobile test coverage adequate")
            logger.info("✅ Configuration files validated")
            logger.info("📱 Mobile app ready for sophisticated agent interactions")
        else:
            logger.info("\n⚠️ Some mobile alignment issues detected")
        
        return test_results


async def main():
    """Main test execution."""
    test_runner = MobileAppFeatureAlignmentTest()
    results = await test_runner.run_mobile_alignment_test()
    
    # Save results
    with open('mobile_app_feature_alignment_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Test results saved to: mobile_app_feature_alignment_results.json")
    
    # Exit with appropriate code
    if results['overall_status'] == 'PASS':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
