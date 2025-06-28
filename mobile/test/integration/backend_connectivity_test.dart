import 'package:dio/dio.dart';
import 'package:flipsync/core/config/environment.dart';
import 'package:flipsync/core/error/error_handler.dart';
import 'package:flipsync/core/services/mobile_api_service.dart';
import 'package:flipsync/core/utils/logger.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('Backend Connectivity Tests', () {
    late Dio dio;
    late MobileApiService apiService;
    late ErrorHandler errorHandler;
    late AppLogger logger;

    setUpAll(() async {
      // Initialize environment configuration
      await EnvironmentConfig.initialize(Environment.dev);

      // Setup dependencies
      logger = AppLogger(tag: 'Test');
      errorHandler = ErrorHandler(logger);

      // Setup Dio with backend URL
      dio = Dio();
      dio.options.baseUrl = EnvironmentConfig.apiBaseUrl;
      dio.options.headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };

      // Create API service
      apiService = MobileApiService(dio, errorHandler);
    });

    test('Backend health check should return OK', () async {
      try {
        final response = await dio.get('/api/v1/health');
        expect(response.statusCode, equals(200));
        expect(response.data['status'], equals('ok'));
        print('✅ Backend health check passed');
      } catch (e) {
        fail('Backend health check failed: $e');
      }
    });

    test('Mobile dashboard endpoint should return valid data', () async {
      try {
        final dashboardData = await apiService.getDashboard();
        expect(dashboardData.activeAgents, isA<int>());
        expect(dashboardData.totalListings, isA<int>());
        expect(dashboardData.pendingOrders, isA<int>());
        expect(dashboardData.revenueToday, isA<double>());
        expect(dashboardData.alerts, isA<List>());
        print('✅ Mobile dashboard endpoint test passed');
      } catch (e) {
        fail('Mobile dashboard test failed: $e');
      }
    });

    test('Mobile agent status endpoint should return valid data', () async {
      try {
        final agentStatus = await apiService.getAgentStatus();
        expect(agentStatus.agents, isA<List>());
        expect(agentStatus.totalAgents, isA<int>());
        expect(agentStatus.activeAgents, isA<int>());
        expect(agentStatus.status, isA<String>());
        print('✅ Mobile agent status endpoint test passed');
      } catch (e) {
        fail('Mobile agent status test failed: $e');
      }
    });

    test('Mobile notifications endpoint should return valid data', () async {
      try {
        final notifications = await apiService.getNotifications();
        expect(notifications.notifications, isA<List>());
        expect(notifications.unreadCount, isA<int>());
        expect(notifications.totalCount, isA<int>());
        print('✅ Mobile notifications endpoint test passed');
      } catch (e) {
        fail('Mobile notifications test failed: $e');
      }
    });

    test('Mobile sync endpoint should work', () async {
      try {
        final syncResponse = await apiService.performSync();
        expect(syncResponse.syncStatus, isA<String>());
        expect(syncResponse.timestamp, isA<String>());
        expect(syncResponse.syncedItems, isA<Map>());
        expect(syncResponse.nextSync, isA<String>());
        print('✅ Mobile sync endpoint test passed');
      } catch (e) {
        fail('Mobile sync test failed: $e');
      }
    });

    test('Mobile settings endpoint should return valid data', () async {
      try {
        final settings = await apiService.getSettings();
        expect(settings.settings, isA<MobileSettings>());
        expect(settings.appVersion, isA<String>());
        expect(settings.apiVersion, isA<String>());
        print('✅ Mobile settings endpoint test passed');
      } catch (e) {
        fail('Mobile settings test failed: $e');
      }
    });
  });
}
