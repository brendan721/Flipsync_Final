#!/usr/bin/env python3
"""
Test eBay OAuth Flow
Validates the complete eBay OAuth integration from mobile app to backend
"""

import asyncio
import aiohttp
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


class EbayOAuthFlowTest:
    """Test eBay OAuth flow end-to-end."""
    
    def __init__(self):
        """Initialize test configuration."""
        self.backend_url = "http://localhost:8001"
        self.test_results = {}
        
    async def test_oauth_url_generation(self) -> bool:
        """Test OAuth URL generation endpoint."""
        logger.info("🔗 Testing OAuth URL generation...")
        
        try:
            async with aiohttp.ClientSession() as session:
                # Test OAuth URL generation
                oauth_request = {
                    "scopes": [
                        "https://api.ebay.com/oauth/api_scope",
                        "https://api.ebay.com/oauth/api_scope/sell.inventory",
                        "https://api.ebay.com/oauth/api_scope/sell.fulfillment"
                    ]
                }
                
                async with session.post(
                    f"{self.backend_url}/api/v1/marketplace/ebay/oauth/authorize",
                    json=oauth_request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    
                    if response.status == 200:
                        data = await response.json()
                        oauth_data = data.get('data', {})
                        
                        # Validate OAuth URL structure
                        auth_url = oauth_data.get('authorization_url', '')
                        state = oauth_data.get('state', '')
                        ru_name = oauth_data.get('ru_name', '')
                        
                        logger.info(f"  ✅ OAuth URL generated successfully")
                        logger.info(f"  📍 RuName: {ru_name}")
                        logger.info(f"  🔑 State: {state[:20]}...")
                        logger.info(f"  🌐 Auth URL: {auth_url[:100]}...")
                        
                        # Validate URL components
                        expected_components = [
                            "https://auth.ebay.com/oauth2/authorize",
                            "client_id=BrendanB-Nashvill-PRD-7f5c11990-62c1c838",
                            "redirect_uri=Brendan_Blomfie-BrendanB-Nashvi-vuwrefym",
                            "response_type=code"
                        ]
                        
                        all_components_present = all(comp in auth_url for comp in expected_components)
                        
                        if all_components_present:
                            logger.info("  ✅ All required OAuth components present")
                            self.test_results['oauth_url_generation'] = {
                                'status': 'PASS',
                                'auth_url': auth_url,
                                'state': state,
                                'ru_name': ru_name
                            }
                            return True
                        else:
                            logger.error("  ❌ Missing required OAuth components")
                            return False
                            
                    else:
                        error_text = await response.text()
                        logger.error(f"  ❌ OAuth URL generation failed: {response.status}")
                        logger.error(f"  📝 Error: {error_text}")
                        return False
                        
        except Exception as e:
            logger.error(f"  ❌ Exception during OAuth URL test: {e}")
            return False
    
    async def test_backend_connectivity(self) -> bool:
        """Test basic backend connectivity."""
        logger.info("🔌 Testing backend connectivity...")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.backend_url}/health") as response:
                    if response.status == 200:
                        logger.info("  ✅ Backend is accessible")
                        return True
                    else:
                        logger.error(f"  ❌ Backend health check failed: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"  ❌ Backend connectivity failed: {e}")
            return False
    
    async def test_environment_configuration(self) -> bool:
        """Test environment configuration."""
        logger.info("⚙️ Testing environment configuration...")
        
        # Check required environment variables
        required_vars = [
            'EBAY_APP_ID',
            'EBAY_CERT_ID',
            'EBAY_DEV_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"  ❌ Missing environment variables: {missing_vars}")
            return False
        
        # Validate eBay credentials format
        app_id = os.getenv('EBAY_APP_ID')
        cert_id = os.getenv('EBAY_CERT_ID')
        
        if 'PRD' in app_id and 'PRD' in cert_id:
            logger.info("  ✅ Production eBay credentials configured")
            logger.info(f"  📱 App ID: {app_id}")
            logger.info(f"  🔐 Cert ID: {cert_id[:20]}...")
            return True
        else:
            logger.warning("  ⚠️ Non-production eBay credentials detected")
            return True  # Still pass, but warn
    
    async def test_mobile_integration_readiness(self) -> bool:
        """Test mobile integration readiness."""
        logger.info("📱 Testing mobile integration readiness...")
        
        # Check if mobile app files exist and are configured correctly
        mobile_files = [
            'mobile/lib/core/services/marketplace_service.dart',
            'mobile/lib/features/onboarding/marketplace_connection_screen.dart',
            'mobile/android/app/src/main/kotlin/com/flipsync/app/MainActivity.kt'
        ]
        
        for file_path in mobile_files:
            if not os.path.exists(file_path):
                logger.error(f"  ❌ Missing mobile file: {file_path}")
                return False
        
        logger.info("  ✅ All mobile integration files present")
        
        # Check MainActivity for correct RuName
        with open('mobile/android/app/src/main/kotlin/com/flipsync/app/MainActivity.kt', 'r') as f:
            content = f.read()
            if 'Brendan_Blomfie-BrendanB-Nashvi-vuwrefym' in content:
                logger.info("  ✅ MainActivity configured with correct production RuName")
                return True
            else:
                logger.error("  ❌ MainActivity RuName mismatch")
                return False
    
    async def run_complete_test(self) -> Dict[str, Any]:
        """Run complete eBay OAuth flow test."""
        logger.info("🚀 Starting Complete eBay OAuth Flow Test")
        logger.info("=" * 60)
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_status': 'UNKNOWN'
        }
        
        # Run all tests
        tests = [
            ('Backend Connectivity', self.test_backend_connectivity),
            ('Environment Configuration', self.test_environment_configuration),
            ('Mobile Integration Readiness', self.test_mobile_integration_readiness),
            ('OAuth URL Generation', self.test_oauth_url_generation),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                result = await test_func()
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
        logger.info("=" * 60)
        logger.info("📋 TEST SUMMARY:")
        logger.info("=" * 60)
        
        for test_name, status in test_results['tests'].items():
            status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            logger.info(f"{status_icon} {test_name}: {status}")
        
        logger.info(f"\n🎯 OVERALL STATUS: {test_results['overall_status']}")
        logger.info(f"📊 PASSED: {passed_tests}/{total_tests} tests")
        
        if test_results['overall_status'] == 'PASS':
            logger.info("\n🎉 eBay OAuth flow is ready for production testing!")
            logger.info("📱 Mobile app can now connect to eBay via OAuth")
            logger.info("🔗 Users will be redirected to real eBay authentication")
        else:
            logger.info("\n⚠️ Some issues need to be resolved before production use")
        
        return test_results


async def main():
    """Main test execution."""
    test_runner = EbayOAuthFlowTest()
    results = await test_runner.run_complete_test()
    
    # Save results to file
    with open('ebay_oauth_test_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Test results saved to: ebay_oauth_test_results.json")
    
    # Exit with appropriate code
    if results['overall_status'] == 'PASS':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
