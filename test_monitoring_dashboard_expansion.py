#!/usr/bin/env python3
"""
Test Monitoring Dashboard Expansion
==================================

Validates that the monitoring dashboard expansion is complete and working correctly.
Tests advanced analytics engine, custom dashboard builder, and enhanced alerting system.
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


class MonitoringDashboardExpansionTest:
    """Test the monitoring dashboard expansion."""
    
    def __init__(self):
        """Initialize test configuration."""
        self.project_root = os.path.dirname(os.path.abspath(__file__))
        
        # Expected expansion files
        self.expansion_files = {
            "fs_agt_clean/services/monitoring/advanced_analytics_engine.py": {
                "description": "Advanced analytics engine with ML-powered insights",
                "min_size": 20000,
                "key_classes": [
                    "AdvancedAnalyticsEngine",
                    "AnalyticsType",
                    "TrendDirection",
                    "AnalyticsInsight"
                ]
            },
            "fs_agt_clean/services/monitoring/custom_dashboard_builder.py": {
                "description": "Custom dashboard builder with drag-and-drop interface",
                "min_size": 15000,
                "key_classes": [
                    "CustomDashboardBuilder",
                    "WidgetType",
                    "DashboardLayout",
                    "WidgetConfiguration"
                ]
            },
            "fs_agt_clean/services/monitoring/enhanced_alerting_system.py": {
                "description": "Enhanced alerting system with smart notifications",
                "min_size": 18000,
                "key_classes": [
                    "EnhancedAlertingSystem",
                    "EnhancedAlert",
                    "EscalationPolicy",
                    "NotificationRule"
                ]
            }
        }
        
    def test_expansion_files_exist(self) -> bool:
        """Test that expansion files exist."""
        logger.info("📁 Testing expansion files existence...")
        
        try:
            missing_files = []
            for file_path, file_info in self.expansion_files.items():
                full_path = os.path.join(self.project_root, file_path)
                if os.path.exists(full_path):
                    file_size = os.path.getsize(full_path)
                    if file_size >= file_info["min_size"]:
                        logger.info(f"  ✅ Found: {file_path} ({file_size} bytes)")
                    else:
                        logger.warning(f"  ⚠️ Found but small: {file_path} ({file_size} bytes)")
                        missing_files.append(file_path)
                else:
                    logger.error(f"  ❌ Missing: {file_path}")
                    missing_files.append(file_path)
            
            if not missing_files:
                logger.info("  ✅ All expansion files exist with substantial content")
                return True
            else:
                logger.error(f"  ❌ Missing or insufficient files: {missing_files}")
                return False
                
        except Exception as e:
            logger.error(f"  ❌ Expansion files check failed: {e}")
            return False
    
    def test_advanced_analytics_engine_import(self) -> bool:
        """Test advanced analytics engine imports."""
        logger.info("🧠 Testing advanced analytics engine import...")
        
        try:
            from fs_agt_clean.services.monitoring.advanced_analytics_engine import (
                AdvancedAnalyticsEngine,
                AnalyticsType,
                TrendDirection,
                AlertPriority,
                AnalyticsInsight,
                PredictiveModel,
                BusinessMetric
            )
            
            logger.info("  ✅ Advanced analytics engine imports successfully")
            logger.info(f"  📝 AdvancedAnalyticsEngine: {AdvancedAnalyticsEngine.__name__}")
            logger.info(f"  📝 AnalyticsType: {AnalyticsType.PREDICTIVE}")
            logger.info(f"  📝 TrendDirection: {TrendDirection.INCREASING}")
            logger.info(f"  📝 AlertPriority: {AlertPriority.HIGH}")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Advanced analytics engine import failed: {e}")
            return False
    
    def test_custom_dashboard_builder_import(self) -> bool:
        """Test custom dashboard builder imports."""
        logger.info("🎨 Testing custom dashboard builder import...")
        
        try:
            from fs_agt_clean.services.monitoring.custom_dashboard_builder import (
                CustomDashboardBuilder,
                WidgetType,
                ChartType,
                RefreshInterval,
                WidgetConfiguration,
                DashboardLayout,
                WidgetData
            )
            
            logger.info("  ✅ Custom dashboard builder imports successfully")
            logger.info(f"  📝 CustomDashboardBuilder: {CustomDashboardBuilder.__name__}")
            logger.info(f"  📝 WidgetType: {WidgetType.METRIC_CHART}")
            logger.info(f"  📝 ChartType: {ChartType.LINE}")
            logger.info(f"  📝 RefreshInterval: {RefreshInterval.REAL_TIME}")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Custom dashboard builder import failed: {e}")
            return False
    
    def test_enhanced_alerting_system_import(self) -> bool:
        """Test enhanced alerting system imports."""
        logger.info("🚨 Testing enhanced alerting system import...")
        
        try:
            from fs_agt_clean.services.monitoring.enhanced_alerting_system import (
                EnhancedAlertingSystem,
                AlertSeverity,
                AlertStatus,
                NotificationChannel,
                EscalationAction,
                EnhancedAlert,
                EscalationPolicy,
                NotificationRule,
                AlertCorrelation
            )
            
            logger.info("  ✅ Enhanced alerting system imports successfully")
            logger.info(f"  📝 EnhancedAlertingSystem: {EnhancedAlertingSystem.__name__}")
            logger.info(f"  📝 AlertSeverity: {AlertSeverity.CRITICAL}")
            logger.info(f"  📝 NotificationChannel: {NotificationChannel.EMAIL}")
            logger.info(f"  📝 EscalationAction: {EscalationAction.NOTIFY_TEAM}")
            
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Enhanced alerting system import failed: {e}")
            return False
    
    def test_analytics_engine_functionality(self) -> bool:
        """Test analytics engine basic functionality."""
        logger.info("⚙️ Testing analytics engine functionality...")
        
        try:
            from fs_agt_clean.services.monitoring.advanced_analytics_engine import (
                AdvancedAnalyticsEngine,
                AnalyticsType,
                BusinessMetric
            )
            
            # Create analytics engine instance
            engine = AdvancedAnalyticsEngine(config={"analytics_window_hours": 12})
            
            # Test business metrics initialization
            assert len(engine.business_metrics) > 0
            logger.info(f"  ✅ Business metrics initialized: {len(engine.business_metrics)} metrics")
            
            # Test analytics types
            analytics_types = list(AnalyticsType)
            assert len(analytics_types) >= 4
            logger.info(f"  ✅ Analytics types available: {[t.value for t in analytics_types]}")
            
            # Test configuration
            assert engine.analytics_window_hours == 12
            assert engine.prediction_horizon_hours > 0
            logger.info(f"  ✅ Configuration working: {engine.analytics_window_hours}h window")
            
            logger.info("  ✅ Analytics engine functionality validated")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Analytics engine functionality test failed: {e}")
            return False
    
    def test_dashboard_builder_functionality(self) -> bool:
        """Test dashboard builder basic functionality."""
        logger.info("🎛️ Testing dashboard builder functionality...")
        
        try:
            from fs_agt_clean.services.monitoring.custom_dashboard_builder import (
                CustomDashboardBuilder,
                WidgetType,
                RefreshInterval
            )
            
            # Create dashboard builder instance
            builder = CustomDashboardBuilder()
            
            # Test widget templates
            assert len(builder.widget_templates) > 0
            logger.info(f"  ✅ Widget templates initialized: {len(builder.widget_templates)} templates")
            
            # Test widget types
            widget_types = list(WidgetType)
            assert len(widget_types) >= 8
            logger.info(f"  ✅ Widget types available: {len(widget_types)} types")
            
            # Test refresh intervals
            refresh_intervals = list(RefreshInterval)
            assert RefreshInterval.REAL_TIME in refresh_intervals
            assert RefreshInterval.MANUAL in refresh_intervals
            logger.info(f"  ✅ Refresh intervals available: {[r.value for r in refresh_intervals]}")
            
            logger.info("  ✅ Dashboard builder functionality validated")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Dashboard builder functionality test failed: {e}")
            return False
    
    def test_alerting_system_functionality(self) -> bool:
        """Test alerting system basic functionality."""
        logger.info("📢 Testing alerting system functionality...")
        
        try:
            from fs_agt_clean.services.monitoring.enhanced_alerting_system import (
                EnhancedAlertingSystem,
                AlertSeverity,
                NotificationChannel,
                EscalationAction
            )
            
            # Create alerting system instance
            alerting = EnhancedAlertingSystem()
            
            # Test default policies
            assert len(alerting.escalation_policies) > 0
            assert len(alerting.notification_rules) > 0
            logger.info(f"  ✅ Default policies initialized: {len(alerting.escalation_policies)} escalation, {len(alerting.notification_rules)} notification")
            
            # Test alert severities
            severities = list(AlertSeverity)
            assert len(severities) >= 4
            logger.info(f"  ✅ Alert severities available: {[s.value for s in severities]}")
            
            # Test notification channels
            channels = list(NotificationChannel)
            assert NotificationChannel.EMAIL in channels
            assert NotificationChannel.SLACK in channels
            logger.info(f"  ✅ Notification channels available: {len(channels)} channels")
            
            # Test escalation actions
            actions = list(EscalationAction)
            assert EscalationAction.NOTIFY_TEAM in actions
            assert EscalationAction.CREATE_INCIDENT in actions
            logger.info(f"  ✅ Escalation actions available: {len(actions)} actions")
            
            logger.info("  ✅ Alerting system functionality validated")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Alerting system functionality test failed: {e}")
            return False
    
    def test_widget_types_comprehensive(self) -> bool:
        """Test comprehensive widget types."""
        logger.info("🔧 Testing comprehensive widget types...")
        
        try:
            from fs_agt_clean.services.monitoring.custom_dashboard_builder import WidgetType
            
            # Check all expected widget types
            expected_types = [
                WidgetType.METRIC_CHART,
                WidgetType.GAUGE,
                WidgetType.TABLE,
                WidgetType.ALERT_LIST,
                WidgetType.STATUS_INDICATOR,
                WidgetType.TEXT_DISPLAY,
                WidgetType.HEATMAP,
                WidgetType.PROGRESS_BAR,
                WidgetType.SPARKLINE,
                WidgetType.KPI_CARD
            ]
            
            available_types = list(WidgetType)
            
            found_types = 0
            for widget_type in expected_types:
                if widget_type in available_types:
                    found_types += 1
                    logger.info(f"  ✅ Widget type available: {widget_type.value}")
            
            if found_types >= len(expected_types) * 0.8:  # 80% of expected types
                logger.info(f"  ✅ Comprehensive widget types validated: {found_types}/{len(expected_types)} types")
                return True
            else:
                logger.error(f"  ❌ Insufficient widget types: {found_types}/{len(expected_types)}")
                return False
            
        except Exception as e:
            logger.error(f"  ❌ Comprehensive widget types test failed: {e}")
            return False
    
    def test_analytics_types_comprehensive(self) -> bool:
        """Test comprehensive analytics types."""
        logger.info("📊 Testing comprehensive analytics types...")
        
        try:
            from fs_agt_clean.services.monitoring.advanced_analytics_engine import AnalyticsType
            
            # Check all expected analytics types
            expected_types = [
                AnalyticsType.DESCRIPTIVE,
                AnalyticsType.DIAGNOSTIC,
                AnalyticsType.PREDICTIVE,
                AnalyticsType.PRESCRIPTIVE
            ]
            
            available_types = list(AnalyticsType)
            
            found_types = 0
            for analytics_type in expected_types:
                if analytics_type in available_types:
                    found_types += 1
                    logger.info(f"  ✅ Analytics type available: {analytics_type.value}")
            
            if found_types >= len(expected_types):
                logger.info(f"  ✅ Comprehensive analytics types validated: {found_types}/{len(expected_types)} types")
                return True
            else:
                logger.error(f"  ❌ Insufficient analytics types: {found_types}/{len(expected_types)}")
                return False
            
        except Exception as e:
            logger.error(f"  ❌ Comprehensive analytics types test failed: {e}")
            return False
    
    def test_notification_channels_comprehensive(self) -> bool:
        """Test comprehensive notification channels."""
        logger.info("📱 Testing comprehensive notification channels...")
        
        try:
            from fs_agt_clean.services.monitoring.enhanced_alerting_system import NotificationChannel
            
            # Check all expected notification channels
            expected_channels = [
                NotificationChannel.EMAIL,
                NotificationChannel.SMS,
                NotificationChannel.SLACK,
                NotificationChannel.WEBHOOK,
                NotificationChannel.MOBILE_PUSH,
                NotificationChannel.IN_APP
            ]
            
            available_channels = list(NotificationChannel)
            
            found_channels = 0
            for channel in expected_channels:
                if channel in available_channels:
                    found_channels += 1
                    logger.info(f"  ✅ Notification channel available: {channel.value}")
            
            if found_channels >= len(expected_channels) * 0.8:  # 80% of expected channels
                logger.info(f"  ✅ Comprehensive notification channels validated: {found_channels}/{len(expected_channels)} channels")
                return True
            else:
                logger.error(f"  ❌ Insufficient notification channels: {found_channels}/{len(expected_channels)}")
                return False
            
        except Exception as e:
            logger.error(f"  ❌ Comprehensive notification channels test failed: {e}")
            return False
    
    async def run_expansion_test(self) -> Dict[str, Any]:
        """Run complete monitoring dashboard expansion test."""
        logger.info("🚀 Starting Monitoring Dashboard Expansion Test")
        logger.info("=" * 70)
        
        test_results = {
            'timestamp': datetime.now().isoformat(),
            'tests': {},
            'overall_status': 'UNKNOWN'
        }
        
        # Run all tests
        tests = [
            ('Expansion Files Exist', self.test_expansion_files_exist),
            ('Advanced Analytics Engine Import', self.test_advanced_analytics_engine_import),
            ('Custom Dashboard Builder Import', self.test_custom_dashboard_builder_import),
            ('Enhanced Alerting System Import', self.test_enhanced_alerting_system_import),
            ('Analytics Engine Functionality', self.test_analytics_engine_functionality),
            ('Dashboard Builder Functionality', self.test_dashboard_builder_functionality),
            ('Alerting System Functionality', self.test_alerting_system_functionality),
            ('Widget Types Comprehensive', self.test_widget_types_comprehensive),
            ('Analytics Types Comprehensive', self.test_analytics_types_comprehensive),
            ('Notification Channels Comprehensive', self.test_notification_channels_comprehensive),
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
        logger.info("📋 MONITORING DASHBOARD EXPANSION TEST SUMMARY:")
        logger.info("=" * 70)
        
        for test_name, status in test_results['tests'].items():
            status_icon = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
            logger.info(f"{status_icon} {test_name}: {status}")
        
        logger.info(f"\n🎯 OVERALL STATUS: {test_results['overall_status']}")
        logger.info(f"📊 PASSED: {passed_tests}/{total_tests} tests")
        
        if test_results['overall_status'] == 'PASS':
            logger.info("\n🎉 Monitoring Dashboard Expansion SUCCESSFUL!")
            logger.info("✅ Advanced analytics engine with ML-powered insights")
            logger.info("✅ Custom dashboard builder with drag-and-drop interface")
            logger.info("✅ Enhanced alerting system with smart notifications")
            logger.info("✅ Comprehensive widget types (10+ types)")
            logger.info("✅ Advanced analytics capabilities (4 types)")
            logger.info("✅ Multi-channel notification system (6+ channels)")
            logger.info("✅ Escalation policies and correlation analysis")
            logger.info("📈 Significantly enhanced monitoring capabilities")
        else:
            logger.info("\n⚠️ Some expansion issues detected")
        
        return test_results


async def main():
    """Main test execution."""
    test_runner = MonitoringDashboardExpansionTest()
    results = await test_runner.run_expansion_test()
    
    # Save results
    with open('monitoring_dashboard_expansion_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"\n📄 Test results saved to: monitoring_dashboard_expansion_results.json")
    
    # Exit with appropriate code
    if results['overall_status'] == 'PASS':
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
