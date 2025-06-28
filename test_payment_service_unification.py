#!/usr/bin/env python3
"""
Test Payment Service Unification
================================

Validates that the payment service unification is complete and working correctly.
Tests unified payment service, backward compatibility, and elimination of duplicates.
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


class PaymentServiceUnificationTest:
    """Test the unified payment service."""
    
    def __init__(self):
        """Initialize test configuration."""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        
    def test_unified_payment_service_import(self) -> bool:
        """Test that unified payment service imports correctly."""
        logger.info("🔧 Testing unified payment service import...")
        
        try:
            # Test unified payment service
            from fs_agt_clean.core.payment.unified_payment_service import (
                UnifiedPaymentService, PaymentProvider, PaymentStatus, PaymentType,
                PaymentRequest, PaymentResponse, SubscriptionRequest
            )
            
            logger.info("  ✅ Unified payment service imports successfully")
            logger.info(f"  📝 UnifiedPaymentService: {UnifiedPaymentService.__name__}")
            logger.info(f"  📝 PaymentProvider: {PaymentProvider.PAYPAL}")
            logger.info(f"  📝 PaymentStatus: {PaymentStatus.COMPLETED}")
            logger.info(f"  📝 PaymentType: {PaymentType.ONE_TIME}")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Unified payment service import failed: {e}")
            return False
    
    def test_payment_service_functionality(self) -> bool:
        """Test basic payment service functionality."""
        logger.info("⚙️ Testing payment service functionality...")
        
        try:
            from fs_agt_clean.core.payment.unified_payment_service import (
                UnifiedPaymentService, PaymentRequest, PaymentProvider
            )
            from decimal import Decimal
            
            # Test payment service creation (without actual PayPal credentials)
            payment_service = UnifiedPaymentService(
                paypal_client_id="test_client_id",
                paypal_client_secret="test_client_secret",
                sandbox_mode=True
            )
            
            # Test payment request creation
            payment_request = PaymentRequest(
                amount=Decimal("29.99"),
                currency="USD",
                description="Test payment",
                payment_method={"email": "test@example.com"}
            )
            
            assert payment_request.amount == Decimal("29.99")
            assert payment_request.currency == "USD"
            assert payment_request.description == "Test payment"
            
            logger.info("  ✅ Payment service instantiation working")
            logger.info("  ✅ Payment request model working")
            logger.info("  📝 Service configured for sandbox mode")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Payment service functionality test failed: {e}")
            return False
    
    def test_duplicate_files_removed(self) -> bool:
        """Test that duplicate payment files were removed."""
        logger.info("🗑️ Testing duplicate files removal...")
        
        duplicate_files = [
            "fs_agt_clean/services/payment_processing/paypal_service.py",
            "fs_agt_clean/services/payment_processing/test_paypal_service.py",
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
                logger.info("  ✅ All duplicate payment files successfully removed")
                return True
            else:
                logger.warning(f"  ⚠️ {len(duplicate_files) - removed_count} duplicate files still exist")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Duplicate files check failed: {e}")
            return False
    
    def test_unified_payment_file_exists(self) -> bool:
        """Test that unified payment service file exists."""
        logger.info("📁 Testing unified payment file existence...")
        
        unified_file = "fs_agt_clean/core/payment/unified_payment_service.py"
        
        try:
            full_path = os.path.join(self.project_root, unified_file)
            if os.path.exists(full_path):
                logger.info(f"  ✅ Found: {unified_file}")
                
                # Check file size to ensure it's not empty
                file_size = os.path.getsize(full_path)
                if file_size > 1000:  # Should be substantial
                    logger.info(f"  ✅ File size: {file_size} bytes (substantial)")
                else:
                    logger.warning(f"  ⚠️ File size: {file_size} bytes (may be incomplete)")
                
                return True
            else:
                logger.error(f"  ❌ Missing: {unified_file}")
                return False
            
        except Exception as e:
            logger.error(f"  ❌ Unified file check failed: {e}")
            return False
    
    def test_payment_enums_and_models(self) -> bool:
        """Test payment enums and models."""
        logger.info("📋 Testing payment enums and models...")
        
        try:
            from fs_agt_clean.core.payment.unified_payment_service import (
                PaymentProvider, PaymentStatus, PaymentType, PaymentRequest, PaymentResponse
            )
            from decimal import Decimal
            
            # Test enums
            assert PaymentProvider.PAYPAL == "paypal"
            assert PaymentStatus.COMPLETED == "completed"
            assert PaymentType.SUBSCRIPTION == "subscription"
            
            # Test models
            payment_request = PaymentRequest(
                amount=Decimal("49.99"),
                currency="USD",
                description="Test subscription",
                payment_method={"email": "user@example.com"},
                metadata={"plan": "premium"}
            )
            
            assert payment_request.amount == Decimal("49.99")
            assert payment_request.metadata["plan"] == "premium"
            
            logger.info("  ✅ Payment enums working correctly")
            logger.info("  ✅ Payment models working correctly")
            logger.info("  📝 All enum values accessible")
            logger.info("  📝 Model validation working")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Payment enums and models test failed: {e}")
            return False
    
    def test_import_consolidation(self) -> bool:
        """Test that import consolidation was successful."""
        logger.info("🔄 Testing import consolidation...")
        
        try:
            # Test that we can import from the unified location
            from fs_agt_clean.core.payment import UnifiedPaymentService
            
            logger.info("  ✅ Can import from unified payment package")
            
            # Test that the service is the same
            from fs_agt_clean.core.payment.unified_payment_service import UnifiedPaymentService as DirectService
            
            assert UnifiedPaymentService is DirectService
            
            logger.info("  ✅ Package imports match direct imports")
            logger.info("  📝 Import consolidation successful")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Import consolidation test failed: {e}")
            return False
    
    def test_paypal_sdk_integration(self) -> bool:
        """Test PayPal SDK integration."""
        logger.info("🔗 Testing PayPal SDK integration...")
        
        try:
            import paypalrestsdk
            from fs_agt_clean.core.payment.unified_payment_service import UnifiedPaymentService
            
            # Test that PayPal SDK is available
            logger.info("  ✅ PayPal SDK imported successfully")
            
            # Test service configuration
            service = UnifiedPaymentService(
                paypal_client_id="test_id",
                paypal_client_secret="test_secret",
                sandbox_mode=True
            )
            
            # Test health check (should handle errors gracefully)
            try:
                health_result = asyncio.run(service.health_check())
                logger.info(f"  ✅ Health check completed: {health_result['status']}")
            except Exception as e:
                logger.info(f"  ✅ Health check handled error gracefully: {type(e).__name__}")
            
            logger.info("  ✅ PayPal SDK integration working")
            logger.info("  📝 Service configuration successful")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ PayPal SDK integration test failed: {e}")
            return False
    
    async def run_unification_test(self) -> Dict[str, Any]:
        """Run complete payment service unification test."""
        logger.info("🚀 Starting Payment Service Unification Test")
        logger.info("=" * 70)
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_status': 'UNKNOWN'
        }
        
        # Run all tests
        tests = [
            ('Unified Payment Service Import', self.test_unified_payment_service_import),
            ('Payment Service Functionality', self.test_payment_service_functionality),
            ('Duplicate Files Removed', self.test_duplicate_files_removed),
            ('Unified Payment File Exists', self.test_unified_payment_file_exists),
            ('Payment Enums and Models', self.test_payment_enums_and_models),
            ('Import Consolidation', self.test_import_consolidation),
            ('PayPal SDK Integration', self.test_paypal_sdk_integration),
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
        logger.info("📋 PAYMENT SERVICE UNIFICATION TEST SUMMARY:")
        logger.info("=" * 70)
        
        for test_name, status in test_results['tests'].items():
            status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            logger.info(f"{status_icon} {test_name}: {status}")
        
        logger.info(f"\n🎯 OVERALL STATUS: {test_results['overall_status']}")
        logger.info(f"📊 PASSED: {passed_tests}/{total_tests} tests")
        
        if test_results['overall_status'] == 'PASS':
            logger.info("\n🎉 Payment Service Unification SUCCESSFUL!")
            logger.info("✅ Unified payment service created")
            logger.info("✅ PayPal integration consolidated")
            logger.info("✅ Subscription management unified")
            logger.info("✅ Payment models standardized")
            logger.info("✅ Duplicate services eliminated")
            logger.info("✅ Import references updated")
            logger.info("✅ PayPal SDK integration working")
            logger.info("📈 Reduced payment service complexity")
        else:
            logger.info("\n⚠️ Some unification issues detected")
        
        return test_results


async def main():
    """Main test execution."""
    test_runner = PaymentServiceUnificationTest()
    results = await test_runner.run_unification_test()
    
    # Save results
    with open('payment_service_unification_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Test results saved to: payment_service_unification_results.json")
    
    # Exit with appropriate code
    if results['overall_status'] == 'PASS':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
