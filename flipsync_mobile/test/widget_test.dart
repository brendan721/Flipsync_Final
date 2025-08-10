// FlipSync Constants Tests
// Basic tests for app and API constants

import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync_mobile/core/constants/app_constants.dart';
import 'package:flipsync_mobile/core/constants/api_constants.dart';

void main() {
  group('FlipSync Constants Tests', () {
    test('App constants are correctly defined', () {
      expect(AppConstants.appName, 'FlipSync');
      expect(AppConstants.appDescription, '4+1 Autonomous Agent Architecture for eBay Optimization');
      expect(AppConstants.contentAgentName, 'Content Agent');
      expect(AppConstants.executiveAgentName, 'Executive Agent');
      expect(AppConstants.logisticsAgentName, 'Logistics Agent');
      expect(AppConstants.marketAgentName, 'Market Agent');
    });

    test('API constants are correctly defined', () {
      expect(ApiConstants.baseUrl, 'http://174.138.77.110:8000');
      expect(ApiConstants.wsBaseUrl, 'ws://174.138.77.110:8000');
      expect(ApiConstants.contentAgent, 'content_autonomous_agent');
      expect(ApiConstants.executiveAgent, 'executive_autonomous_agent');
      expect(ApiConstants.logisticsAgent, 'logistics_autonomous_agent');
      expect(ApiConstants.marketAgent, 'market_autonomous_agent');
    });

    test('Performance thresholds are reasonable', () {
      expect(AppConstants.goodResponseTime, 100.0);
      expect(AppConstants.warningResponseTime, 500.0);
      expect(AppConstants.criticalResponseTime, 1000.0);
      expect(AppConstants.goodResponseTime < AppConstants.warningResponseTime, true);
      expect(AppConstants.warningResponseTime < AppConstants.criticalResponseTime, true);
    });
  });
}
