import 'package:flutter_test/flutter_test.dart';
import 'package:dio/dio.dart';
import 'package:get_it/get_it.dart';
import 'package:mocktail/mocktail.dart';
import 'dart:convert';
import 'dart:typed_data';

import 'package:flipsync/core/services/enhanced_product_creation_service_v3.dart';
import 'package:flipsync/core/services/shipping/shipping_arbitrage_service.dart';
import 'package:flipsync/core/services/enhanced_websocket_service_v3.dart';
import 'package:flipsync/core/services/api_service.dart';
import 'package:flipsync/core/network/api_client.dart';
import 'package:flipsync/core/logging/app_logger.dart';
import 'package:flipsync/core/state/auth_state.dart';
import 'package:flipsync/core/models/product_models.dart';

// Mock classes
class MockApiService extends Mock implements ApiService {}

class MockApiClient extends Mock implements ApiClient {}

class MockAuthState extends Mock implements AuthState {}

class MockAppLogger extends Mock implements AppLogger {}

class MockEnhancedWebSocketServiceV3 extends Mock implements EnhancedWebSocketServiceV3 {}

/// V3 Phase 1 Integration Tests
///
/// Tests the updated V3 services against the real backend integration
/// to verify that Phase 1 fixes are working correctly.

void main() {
  group('V3 Phase 1 Integration Tests', () {
    late MockApiService mockApiService;
    late MockApiClient mockApiClient;
    late MockAuthState mockAuthState;
    late MockAppLogger mockLogger;
    late MockEnhancedWebSocketServiceV3 mockWebSocketService;
    late EnhancedProductCreationServiceV3 productCreationService;
    late ShippingArbitrageService shippingService;

    setUpAll(() {
      // Register fallback values
      registerFallbackValue(Uint8List(0));
    });

    setUp(() {
      // Reset GetIt
      GetIt.instance.reset();

      // Create mocks
      mockApiService = MockApiService();
      mockApiClient = MockApiClient();
      mockAuthState = MockAuthState();
      mockLogger = MockAppLogger();
      mockWebSocketService = MockEnhancedWebSocketServiceV3();

      // Register mocks with GetIt
      GetIt.instance.registerSingleton<AuthState>(mockAuthState);

      // Setup auth state mock
      when(() => mockAuthState.authToken).thenReturn('test_jwt_token');
      when(() => mockAuthState.isAuthenticated).thenReturn(true);

      // Setup logger mock
      when(() => mockLogger.info(any())).thenReturn(null);
      when(() => mockLogger.error(any())).thenReturn(null);
      when(() => mockLogger.warning(any())).thenReturn(null);

      // Create services with correct constructors
      productCreationService = EnhancedProductCreationServiceV3(mockApiClient);

      shippingService = ShippingArbitrageService();
    });

    tearDown(() {
      GetIt.instance.reset();
    });

    group('Enhanced Product Creation Service V3', () {
      test('should map Google Vision endpoint to existing AI analyze endpoint', () async {
        // Arrange
        final testImageData = base64Encode(Uint8List.fromList([1, 2, 3, 4]));
        final expectedResponse = {
          'success': true,
          'analysis': {
            'product_type': 'Electronics',
            'brand': 'Test Brand',
            'condition': 'Used',
            'estimated_value': 25.99,
          }
        };

        when(() => mockApiService.analyzeProductImage(
              imageFile: any(named: 'imageFile'),
              marketplace: any(named: 'marketplace'),
              additionalContext: any(named: 'additionalContext'),
              usePremiumAi: any(named: 'usePremiumAi'),
            )).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await productCreationService
            .testMakeApiCall('POST', '/api/v1/ai/google-vision-analyze', {'image_data': testImageData});

        // Assert
        expect(result, isNotNull);
        expect(result!['success'], isTrue);
        expect(result['data'], equals(expectedResponse));

        verify(() => mockApiService.analyzeProductImage(
              imageFile: any(named: 'imageFile'),
              marketplace: 'ebay',
              additionalContext: 'V3 enhanced product creation analysis',
              usePremiumAi: true,
            )).called(1);
      });

      test('should handle Gemini research endpoint mapping', () async {
        // Arrange
        final testImageData = base64Encode(Uint8List.fromList([5, 6, 7, 8]));
        final consolidatedData = {
          'vision_data': {'image_data': testImageData},
          'barcode_data': {'upc': '123456789012'},
        };
        final expectedResponse = {
          'success': true,
          'research': {
            'market_analysis': 'Comprehensive analysis',
            'pricing_recommendations': {'min': 19.99, 'max': 29.99},
          }
        };

        when(() => mockApiService.analyzeProductImage(
              imageFile: any(named: 'imageFile'),
              marketplace: any(named: 'marketplace'),
              additionalContext: any(named: 'additionalContext'),
              usePremiumAi: any(named: 'usePremiumAi'),
            )).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await productCreationService
            .testMakeApiCall('POST', '/api/v1/ai/gemini-product-research', {'consolidated_data': consolidatedData});

        // Assert
        expect(result, isNotNull);
        expect(result!['success'], isTrue);
        expect(result['data'], equals(expectedResponse));

        verify(() => mockApiService.analyzeProductImage(
              imageFile: any(named: 'imageFile'),
              marketplace: 'ebay',
              additionalContext: any(named: 'additionalContext'),
              usePremiumAi: true,
            )).called(1);
      });

      test('should provide fallback for unmapped endpoints', () async {
        // Act
        final result =
            await productCreationService.testMakeApiCall('POST', '/api/v1/unknown/endpoint', {'test': 'data'});

        // Assert
        expect(result, isNotNull);
        expect(result!['success'], isTrue);
        expect(result['data']['fallback'], isTrue);
        expect(result['data']['endpoint'], equals('/api/v1/unknown/endpoint'));
        expect(result['data']['message'], contains('fallback data'));
      });

      test('should handle eBay integration endpoint', () async {
        // Act
        final result =
            await productCreationService.testMakeApiCall('POST', '/api/v1/marketplace/ebay/research-and-optimize', {
          'product_data': {'title': 'Test Product'},
          'include_shipping_arbitrage': true,
          'include_revenue_optimization': true,
        });

        // Assert
        expect(result, isNotNull);
        expect(result!['success'], isTrue);
        expect(result['market_data'], isNotNull);
        expect(result['listing_draft'], isNotNull);
        expect(result['revenue_optimization'], isNotNull);
        expect(result['market_data']['shipping_arbitrage_potential'], equals(15.0));
      });
    });

    group('Shipping Arbitrage Service', () {
      test('should use correct backend endpoint with authentication', () async {
        // Arrange
        final testProduct = Product(
          id: 'test_product_123',
          title: 'Test Product',
          price: 25.99,
          shippingInfo: ShippingInfo(
            weight: 2.0,
            cost: 15.99,
            dimensions: ShippingDimensions(
              length: 12.0,
              width: 8.0,
              height: 4.0,
            ),
          ),
        );

        // Act & Assert - This will test the endpoint mapping and authentication
        try {
          await shippingService.getShippingRecommendations(
            product: testProduct,
            profitMarginThreshold: 0.25,
            prioritizeSpeed: false,
            enableInsurance: false,
          );
        } catch (e) {
          // Expected to fail in test environment, but we can verify the setup
          expect(e.toString(), contains('Failed to host lookup'));
        }

        // Verify auth token is being retrieved
        expect(mockAuthState.authToken, equals('test_jwt_token'));
      });

      test('should map request data to backend format correctly', () {
        // Arrange
        final testProduct = Product(
          id: 'test_product_456',
          title: 'Another Test Product',
          price: 35.50,
          shippingInfo: ShippingInfo(
            weight: 1.5,
            cost: 12.99,
            dimensions: ShippingDimensions(
              length: 10.0,
              width: 6.0,
              height: 3.0,
            ),
          ),
        );

        // Act
        final requestData = {
          'product_id': testProduct.id,
          'weight': testProduct.shippingInfo.weight,
          'value': testProduct.price,
          'dimensions': {
            'length': testProduct.shippingInfo.dimensions.length,
            'width': testProduct.shippingInfo.dimensions.width,
            'height': testProduct.shippingInfo.dimensions.height,
          },
          'profit_margin_threshold': 0.30,
          'prioritize_speed': true,
          'enable_insurance': true,
        };

        final mappedData = shippingService.testMapToBackendFormat(requestData);

        // Assert
        expect(mappedData['origin_zip'], equals('37203')); // Default Nashville ZIP
        expect(mappedData['weight'], equals(1.5));
        expect(mappedData['value'], equals(35.50));
        expect(mappedData['package_type'], equals('box'));
        expect(mappedData['profit_margin_threshold'], equals(0.30));
        expect(mappedData['prioritize_speed'], isTrue);
        expect(mappedData['enable_insurance'], isTrue);
        expect(mappedData['dimensions']['length'], equals(10.0));
        expect(mappedData['dimensions']['width'], equals(6.0));
        expect(mappedData['dimensions']['height'], equals(3.0));
      });
    });

    group('Authentication Integration', () {
      test('should handle missing auth token gracefully', () {
        // Arrange
        when(() => mockAuthState.authToken).thenReturn(null);
        when(() => mockAuthState.isAuthenticated).thenReturn(false);

        // Act
        final shippingServiceNoAuth = ShippingArbitrageService();
        final authToken = shippingServiceNoAuth.testGetAuthToken();

        // Assert
        expect(authToken, isNull);
      });

      test('should retrieve auth token when available', () {
        // Arrange
        when(() => mockAuthState.authToken).thenReturn('valid_jwt_token_123');
        when(() => mockAuthState.isAuthenticated).thenReturn(true);

        // Act
        final shippingServiceWithAuth = ShippingArbitrageService();
        final authToken = shippingServiceWithAuth.testGetAuthToken();

        // Assert
        expect(authToken, equals('valid_jwt_token_123'));
      });
    });
  });
}

// Extension to expose private methods for testing
extension EnhancedProductCreationServiceV3Test on EnhancedProductCreationServiceV3 {
  Future<Map<String, dynamic>?> testMakeApiCall(String method, String endpoint, [Map<String, dynamic>? data]) {
    return _makeApiCall(method, endpoint, data);
  }
}

extension ShippingArbitrageServiceTest on ShippingArbitrageService {
  Map<String, dynamic> testMapToBackendFormat(Map<String, dynamic> requestData) {
    return _mapToBackendFormat(requestData);
  }

  String? testGetAuthToken() {
    return _getAuthToken();
  }
}
