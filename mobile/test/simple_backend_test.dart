import 'package:flutter_test/flutter_test.dart';
import 'package:dio/dio.dart';

void main() {
  group('Simple Backend Connectivity Tests', () {
    late Dio dio;

    setUpAll(() async {
      // Setup Dio with backend URL
      dio = Dio();
      dio.options.baseUrl = 'http://localhost:8080';
      dio.options.headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      };
      dio.options.connectTimeout = const Duration(seconds: 10);
      dio.options.receiveTimeout = const Duration(seconds: 10);
    });

    test('Backend health check should return OK', () async {
      try {
        final response = await dio.get('/api/v1/health');
        expect(response.statusCode, equals(200));
        expect(response.data, isA<Map<String, dynamic>>());
        expect(response.data['status'], equals('ok'));
        print('✅ Backend health check passed: ${response.data}');
      } catch (e) {
        fail('Backend health check failed: $e');
      }
    });

    test('Mobile dashboard endpoint should return valid data', () async {
      try {
        final response = await dio.get('/api/v1/mobile/dashboard');
        expect(response.statusCode, equals(200));
        expect(response.data, isA<Map<String, dynamic>>());
        
        final dashboard = response.data['dashboard'];
        expect(dashboard, isA<Map<String, dynamic>>());
        expect(dashboard['active_agents'], isA<int>());
        expect(dashboard['total_listings'], isA<int>());
        expect(dashboard['pending_orders'], isA<int>());
        expect(dashboard['revenue_today'], isA<num>());
        expect(dashboard['alerts'], isA<List>());
        
        print('✅ Mobile dashboard endpoint test passed: ${dashboard}');
      } catch (e) {
        fail('Mobile dashboard test failed: $e');
      }
    });

    test('Mobile agent status endpoint should return valid data', () async {
      try {
        final response = await dio.get('/api/v1/mobile/agents/status');
        expect(response.statusCode, equals(200));
        expect(response.data, isA<Map<String, dynamic>>());
        
        final data = response.data;
        expect(data['agents'], isA<List>());
        expect(data['total_agents'], isA<int>());
        expect(data['active_agents'], isA<int>());
        expect(data['status'], isA<String>());
        
        print('✅ Mobile agent status endpoint test passed: ${data}');
      } catch (e) {
        fail('Mobile agent status test failed: $e');
      }
    });

    test('Mobile notifications endpoint should return valid data', () async {
      try {
        final response = await dio.get('/api/v1/mobile/notifications');
        expect(response.statusCode, equals(200));
        expect(response.data, isA<Map<String, dynamic>>());
        
        final data = response.data;
        expect(data['notifications'], isA<List>());
        expect(data['unread_count'], isA<int>());
        expect(data['total_count'], isA<int>());
        
        print('✅ Mobile notifications endpoint test passed: ${data}');
      } catch (e) {
        fail('Mobile notifications test failed: $e');
      }
    });

    test('Mobile sync endpoint should work', () async {
      try {
        final response = await dio.post('/api/v1/mobile/sync');
        expect(response.statusCode, equals(200));
        expect(response.data, isA<Map<String, dynamic>>());
        
        final data = response.data;
        expect(data['sync_status'], isA<String>());
        expect(data['timestamp'], isA<String>());
        expect(data['synced_items'], isA<Map>());
        expect(data['next_sync'], isA<String>());
        
        print('✅ Mobile sync endpoint test passed: ${data}');
      } catch (e) {
        fail('Mobile sync test failed: $e');
      }
    });

    test('Mobile settings endpoint should return valid data', () async {
      try {
        final response = await dio.get('/api/v1/mobile/settings');
        expect(response.statusCode, equals(200));
        expect(response.data, isA<Map<String, dynamic>>());
        
        final data = response.data;
        expect(data['settings'], isA<Map<String, dynamic>>());
        expect(data['app_version'], isA<String>());
        expect(data['api_version'], isA<String>());
        
        final settings = data['settings'];
        expect(settings['notifications_enabled'], isA<bool>());
        expect(settings['sync_interval'], isA<int>());
        expect(settings['theme'], isA<String>());
        expect(settings['language'], isA<String>());
        expect(settings['currency'], isA<String>());
        expect(settings['timezone'], isA<String>());
        
        print('✅ Mobile settings endpoint test passed: ${data}');
      } catch (e) {
        fail('Mobile settings test failed: $e');
      }
    });
  });
}
