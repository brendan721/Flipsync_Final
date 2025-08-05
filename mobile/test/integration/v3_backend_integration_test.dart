import 'package:flutter_test/flutter_test.dart';
import 'package:dio/dio.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import 'dart:convert';
import 'dart:async';

/// V3 Backend Integration Tests
///
/// Tests the current V3 Flutter services against the production backend
/// to identify functional vs non-functional integrations.
///
/// Backend: http://174.138.77.110:8000
/// WebSocket: ws://174.138.77.110:8000/ws/flipsync

class V3BackendIntegrationTest {
  static const String baseUrl = 'http://174.138.77.110:8000';
  static const String wsUrl = 'ws://174.138.77.110:8000/ws/flipsync';

  late Dio dio;

  void setUp() {
    dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 10),
    ));
  }
}

void main() {
  group('V3 Backend Integration Tests', () {
    late V3BackendIntegrationTest testHelper;

    setUpAll(() {
      testHelper = V3BackendIntegrationTest();
      testHelper.setUp();
    });

    group('Core Infrastructure Tests', () {
      test('Backend health check', () async {
        try {
          final response = await testHelper.dio.get('/api/v1/health');
          expect(response.statusCode, 200);
          print('✅ Backend is healthy: ${response.data}');
        } catch (e) {
          print('❌ Backend health check failed: $e');
          fail('Backend is not accessible');
        }
      });

      test('Agent status endpoint', () async {
        try {
          final response = await testHelper.dio.get('/api/v1/agents/status');
          expect(response.statusCode, 200);
          expect(response.data, isA<Map>());
          print('✅ Agent status endpoint working: ${response.data}');
        } catch (e) {
          print('❌ Agent status endpoint failed: $e');
          fail('Agent status endpoint not working');
        }
      });

      test('WebSocket connection', () async {
        try {
          final channel = WebSocketChannel.connect(Uri.parse(V3BackendIntegrationTest.wsUrl));

          // Test connection
          final completer = Completer<bool>();
          late StreamSubscription subscription;

          subscription = channel.stream.listen(
            (message) {
              print('✅ WebSocket message received: $message');
              subscription.cancel();
              channel.sink.close();
              completer.complete(true);
            },
            onError: (error) {
              print('❌ WebSocket error: $error');
              subscription.cancel();
              channel.sink.close();
              completer.complete(false);
            },
          );

          // Send test message
          channel.sink.add(json.encode({'type': 'test', 'message': 'V3 integration test'}));

          final result = await completer.future.timeout(
            const Duration(seconds: 5),
            onTimeout: () {
              subscription.cancel();
              channel.sink.close();
              return false;
            },
          );

          expect(result, true);
        } catch (e) {
          print('❌ WebSocket connection failed: $e');
          fail('WebSocket not accessible');
        }
      });
    });

    group('V3 Missing Endpoints Tests', () {
      test('User profile endpoints (MISSING)', () async {
        // Test /api/v1/users/profile
        try {
          await testHelper.dio.get('/api/v1/users/profile');
          fail('Expected 404 but got success');
        } catch (e) {
          if (e is DioException && e.response?.statusCode == 404) {
            print('❌ CONFIRMED MISSING: /api/v1/users/profile');
          } else {
            print('❌ Unexpected error: $e');
          }
        }

        // Test /api/v1/users/preferences
        try {
          await testHelper.dio.get('/api/v1/users/preferences');
          fail('Expected 404 but got success');
        } catch (e) {
          if (e is DioException && e.response?.statusCode == 404) {
            print('❌ CONFIRMED MISSING: /api/v1/users/preferences');
          } else {
            print('❌ Unexpected error: $e');
          }
        }
      });

      test('Opportunity endpoints (MISSING)', () async {
        final endpoints = [
          '/api/v1/opportunities/trending/liquidation',
          '/api/v1/opportunities/liquidation',
          '/api/v1/opportunities/thrifting',
          '/api/v1/opportunities/miscellaneous',
        ];

        for (final endpoint in endpoints) {
          try {
            await testHelper.dio.get(endpoint);
            fail('Expected 404 but got success for $endpoint');
          } catch (e) {
            if (e is DioException && e.response?.statusCode == 404) {
              print('❌ CONFIRMED MISSING: $endpoint');
            } else {
              print('❌ Unexpected error for $endpoint: $e');
            }
          }
        }
      });

      test('Physical assessment endpoints (MISSING)', () async {
        final endpoints = [
          '/api/v1/assessment/start',
          '/api/v1/products/specifications/test',
          '/api/v1/products/identify',
        ];

        for (final endpoint in endpoints) {
          try {
            await testHelper.dio.post(endpoint, data: {});
            fail('Expected 404 but got success for $endpoint');
          } catch (e) {
            if (e is DioException && e.response?.statusCode == 404) {
              print('❌ CONFIRMED MISSING: $endpoint');
            } else {
              print('❌ Unexpected error for $endpoint: $e');
            }
          }
        }
      });

      test('Shipping arbitrage V3 endpoints (MISSING)', () async {
        final endpoints = [
          '/api/v1/shipping/zones/12345',
          '/api/v1/shipping/arbitrage',
          '/api/v1/shipping/shippo/poly',
        ];

        for (final endpoint in endpoints) {
          try {
            await testHelper.dio.get(endpoint);
            fail('Expected 404 but got success for $endpoint');
          } catch (e) {
            if (e is DioException && e.response?.statusCode == 404) {
              print('❌ CONFIRMED MISSING: $endpoint');
            } else {
              print('❌ Unexpected error for $endpoint: $e');
            }
          }
        }
      });

      test('Enhanced product creation endpoints (MISSING)', () async {
        final endpoints = [
          '/api/v1/product-creation/analyze-image',
          '/api/v1/product-creation/barcode-lookup',
          '/api/v1/product-creation/publish-listing',
        ];

        for (final endpoint in endpoints) {
          try {
            await testHelper.dio.post(endpoint, data: {});
            fail('Expected 404 but got success for $endpoint');
          } catch (e) {
            if (e is DioException && e.response?.statusCode == 404) {
              print('❌ CONFIRMED MISSING: $endpoint');
            } else {
              print('❌ Unexpected error for $endpoint: $e');
            }
          }
        }
      });

      test('External advertising endpoints (MISSING)', () async {
        final endpoints = [
          '/api/v1/advertising/boost-listing',
          '/api/v1/advertising/campaigns',
          '/api/v1/advertising/revenue-tracking',
        ];

        for (final endpoint in endpoints) {
          try {
            await testHelper.dio.get(endpoint);
            fail('Expected 404 but got success for $endpoint');
          } catch (e) {
            if (e is DioException && e.response?.statusCode == 404) {
              print('❌ CONFIRMED MISSING: $endpoint');
            } else {
              print('❌ Unexpected error for $endpoint: $e');
            }
          }
        }
      });

      test('AI-Powered optimization score endpoints (MISSING)', () async {
        final endpoints = [
          '/api/v1/optimization/score/test-user',
          '/api/v1/optimization/opportunities/test-user',
        ];

        for (final endpoint in endpoints) {
          try {
            await testHelper.dio.get(endpoint);
            fail('Expected 404 but got success for $endpoint');
          } catch (e) {
            if (e is DioException && e.response?.statusCode == 404) {
              print('❌ CONFIRMED MISSING: $endpoint');
            } else {
              print('❌ Unexpected error for $endpoint: $e');
            }
          }
        }
      });
    });

    group('Existing Endpoints Tests', () {
      test('AI analyze product endpoint (EXISTS - needs POST)', () async {
        try {
          await testHelper.dio
              .post('/api/v1/ai/analyze-product', data: {'image_data': 'test_base64_data', 'product_context': 'test'});
          print('✅ AI analyze product endpoint working');
        } catch (e) {
          if (e is DioException) {
            if (e.response?.statusCode == 405) {
              print('⚠️ AI analyze product endpoint exists but method not allowed');
            } else if (e.response?.statusCode == 422) {
              print('⚠️ AI analyze product endpoint exists but validation failed');
            } else {
              print('❌ AI analyze product endpoint error: ${e.response?.statusCode}');
            }
          }
        }
      });

      test('Revenue shipping calculate endpoint (EXISTS - needs auth)', () async {
        try {
          await testHelper.dio.post('/api/v1/shipping/arbitrage',
              data: {'origin_zip': '12345', 'destination_zip': '67890', 'weight': 1.0, 'package_type': 'box'});
          print('✅ Revenue shipping calculate endpoint working');
        } catch (e) {
          if (e is DioException) {
            if (e.response?.statusCode == 401) {
              print('⚠️ Revenue shipping calculate endpoint exists but needs auth');
            } else if (e.response?.statusCode == 422) {
              print('⚠️ Revenue shipping calculate endpoint exists but validation failed');
            } else {
              print('❌ Revenue shipping calculate endpoint error: ${e.response?.statusCode}');
            }
          }
        }
      });
    });
  });
}
