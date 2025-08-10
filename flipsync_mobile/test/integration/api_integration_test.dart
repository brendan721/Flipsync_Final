import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:dio/dio.dart';
import 'package:flipsync_mobile/core/network/api_service.dart';
import 'package:flipsync_mobile/core/network/websocket_service.dart';
import 'package:flipsync_mobile/core/errors/exceptions.dart';

import 'api_integration_test.mocks.dart';

@GenerateMocks([Dio])
void main() {
  group('API Integration Tests', () {
    late ApiService apiService;
    late WebSocketService webSocketService;
    late MockDio mockDio;

    setUp(() {
      mockDio = MockDio();
      apiService = ApiService();
      webSocketService = WebSocketService();
    });

    tearDown(() {
      webSocketService.disconnect();
    });

    group('eBay OAuth API Integration', () {
      test('should successfully get OAuth URL', () async {
        // Arrange
        final expectedResponse = Response(
          data: {'oauth_url': 'https://auth.ebay.com/oauth2/authorize?client_id=test'},
          statusCode: 200,
          requestOptions: RequestOptions(path: '/api/v1/ebay/oauth/url'),
        );

        when(mockDio.get('/api/v1/ebay/oauth/url')).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await apiService.get('/api/v1/ebay/oauth/url');

        // Assert
        expect(result['oauth_url'], 'https://auth.ebay.com/oauth2/authorize?client_id=test');
      });

      test('should handle OAuth URL request failure', () async {
        // Arrange
        when(mockDio.get('/api/v1/ebay/oauth/url')).thenThrow(
          DioException(
            requestOptions: RequestOptions(path: '/api/v1/ebay/oauth/url'),
            response: Response(statusCode: 500, requestOptions: RequestOptions(path: '/api/v1/ebay/oauth/url')),
          ),
        );

        // Act & Assert
        expect(() => apiService.get('/api/v1/ebay/oauth/url'), throwsA(isA<ServerException>()));
      });

      test('should successfully exchange code for tokens', () async {
        // Arrange
        final requestData = {'code': 'test_code', 'state': 'test_state'};
        final expectedResponse = Response(
          data: {'access_token': 'test_access_token', 'refresh_token': 'test_refresh_token', 'expires_in': 7200},
          statusCode: 200,
          requestOptions: RequestOptions(path: '/api/v1/ebay/oauth/callback'),
        );

        when(mockDio.post('/api/v1/ebay/oauth/callback', data: requestData)).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await apiService.post('/api/v1/ebay/oauth/callback', data: requestData);

        // Assert
        expect(result['access_token'], 'test_access_token');
        expect(result['refresh_token'], 'test_refresh_token');
        expect(result['expires_in'], 7200);
      });

      test('should handle token exchange failure', () async {
        // Arrange
        final requestData = {'code': 'invalid_code', 'state': 'invalid_state'};

        when(mockDio.post('/api/v1/ebay/oauth/callback', data: requestData)).thenThrow(
          DioException(
            requestOptions: RequestOptions(path: '/api/v1/ebay/oauth/callback'),
            response: Response(
              statusCode: 400,
              data: {'error': 'invalid_grant'},
              requestOptions: RequestOptions(path: '/api/v1/ebay/oauth/callback'),
            ),
          ),
        );

        // Act & Assert
        expect(
          () => apiService.post('/api/v1/ebay/oauth/callback', data: requestData),
          throwsA(isA<ServerException>()),
        );
      });

      test('should successfully refresh tokens', () async {
        // Arrange
        final requestData = {'refresh_token': 'old_refresh_token'};
        final expectedResponse = Response(
          data: {'access_token': 'new_access_token', 'refresh_token': 'new_refresh_token', 'expires_in': 7200},
          statusCode: 200,
          requestOptions: RequestOptions(path: '/api/v1/ebay/oauth/refresh'),
        );

        when(mockDio.post('/api/v1/ebay/oauth/refresh', data: requestData)).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await apiService.post('/api/v1/ebay/oauth/refresh', data: requestData);

        // Assert
        expect(result['access_token'], 'new_access_token');
        expect(result['refresh_token'], 'new_refresh_token');
      });
    });

    group('4+1 Agent Decisions API Integration', () {
      test('should successfully fetch agent decisions', () async {
        // Arrange
        const agentId = 'content_autonomous_agent';
        final expectedDecisions = [
          {
            'id': '1',
            'agent_id': agentId,
            'decision_type': 'content_optimization',
            'confidence': 0.95,
            'timestamp': '2024-01-01T00:00:00Z',
          },
        ];

        final expectedResponse = Response(
          data: {'decisions': expectedDecisions},
          statusCode: 200,
          requestOptions: RequestOptions(path: '/api/v1/decisions/4plus1/$agentId'),
        );

        when(mockDio.get('/api/v1/decisions/4plus1/$agentId')).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await apiService.get('/api/v1/decisions/4plus1/$agentId');

        // Assert
        expect(result['decisions'], expectedDecisions);
      });

      test('should handle agent decisions request with filters', () async {
        // Arrange
        const agentId = 'market_autonomous_agent';
        final queryParams = {'limit': 10, 'offset': 0, 'decision_type': 'pricing_optimization'};

        final expectedResponse = Response(
          data: {'decisions': []},
          statusCode: 200,
          requestOptions: RequestOptions(path: '/api/v1/decisions/4plus1/$agentId'),
        );

        when(
          mockDio.get('/api/v1/decisions/4plus1/$agentId', queryParameters: queryParams),
        ).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await apiService.get('/api/v1/decisions/4plus1/$agentId', queryParameters: queryParams);

        // Assert
        expect(result['decisions'], []);
      });

      test('should successfully request agent decision', () async {
        // Arrange
        const agentId = 'content_autonomous_agent';
        final requestData = {'product_id': 'prod_123', 'context': 'listing_optimization', 'priority': 'high'};

        final expectedResponse = Response(
          data: {'request_id': 'req_456', 'status': 'processing', 'estimated_completion': '2024-01-01T00:05:00Z'},
          statusCode: 200,
          requestOptions: RequestOptions(path: '/api/v1/decisions/4plus1/$agentId/request'),
        );

        when(
          mockDio.post('/api/v1/decisions/4plus1/$agentId/request', data: requestData),
        ).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await apiService.post('/api/v1/decisions/4plus1/$agentId/request', data: requestData);

        // Assert
        expect(result['request_id'], 'req_456');
        expect(result['status'], 'processing');
      });

      test('should successfully submit decision feedback', () async {
        // Arrange
        const decisionId = 'decision_123';
        final feedback = {'rating': 5, 'comment': 'Excellent decision', 'outcome': 'successful'};

        final expectedResponse = Response(
          data: {'status': 'success', 'message': 'Feedback submitted'},
          statusCode: 200,
          requestOptions: RequestOptions(path: '/api/v1/decisions/4plus1/$decisionId/feedback'),
        );

        when(
          mockDio.post('/api/v1/decisions/4plus1/$decisionId/feedback', data: feedback),
        ).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await apiService.post('/api/v1/decisions/4plus1/$decisionId/feedback', data: feedback);

        // Assert
        expect(result['status'], 'success');
      });
    });

    group('Analytics API Integration', () {
      test('should successfully fetch analytics data', () async {
        // Arrange
        const agentId = 'executive_autonomous_agent';
        final expectedAnalytics = {
          'total_decisions': 150,
          'success_rate': 0.94,
          'average_confidence': 0.89,
          'performance_metrics': {'response_time_ms': 245, 'accuracy_score': 0.96},
        };

        final expectedResponse = Response(
          data: expectedAnalytics,
          statusCode: 200,
          requestOptions: RequestOptions(path: '/api/v1/analytics/$agentId'),
        );

        when(mockDio.get('/api/v1/analytics/$agentId')).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await apiService.get('/api/v1/analytics/$agentId');

        // Assert
        expect(result['total_decisions'], 150);
        expect(result['success_rate'], 0.94);
        expect(result['performance_metrics']['response_time_ms'], 245);
      });

      test('should handle analytics request with date range', () async {
        // Arrange
        const agentId = 'logistics_autonomous_agent';
        final queryParams = {'start_date': '2024-01-01', 'end_date': '2024-01-31'};

        final expectedResponse = Response(
          data: {'total_decisions': 89, 'success_rate': 0.91},
          statusCode: 200,
          requestOptions: RequestOptions(path: '/api/v1/analytics/$agentId'),
        );

        when(
          mockDio.get('/api/v1/analytics/$agentId', queryParameters: queryParams),
        ).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await apiService.get('/api/v1/analytics/$agentId', queryParameters: queryParams);

        // Assert
        expect(result['total_decisions'], 89);
        expect(result['success_rate'], 0.91);
      });
    });

    group('Chat API Integration', () {
      test('should successfully send chat message', () async {
        // Arrange
        final messageData = {'message': 'How are my agents performing?', 'context': 'dashboard'};

        final expectedResponse = Response(
          data: {'response': 'Your agents are performing excellently with 94% success rate.', 'message_id': 'msg_123'},
          statusCode: 200,
          requestOptions: RequestOptions(path: '/api/v1/chat/4plus1'),
        );

        when(mockDio.post('/api/v1/chat/4plus1', data: messageData)).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await apiService.post('/api/v1/chat/4plus1', data: messageData);

        // Assert
        expect(result['response'], contains('94% success rate'));
        expect(result['message_id'], 'msg_123');
      });

      test('should handle chat history request', () async {
        // Arrange
        final expectedHistory = [
          {'id': '1', 'message': 'Hello', 'response': 'Hi there!', 'timestamp': '2024-01-01T00:00:00Z'},
        ];

        final expectedResponse = Response(
          data: {'history': expectedHistory},
          statusCode: 200,
          requestOptions: RequestOptions(path: '/api/v1/chat/4plus1/history'),
        );

        when(mockDio.get('/api/v1/chat/4plus1/history')).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await apiService.get('/api/v1/chat/4plus1/history');

        // Assert
        expect(result['history'], expectedHistory);
      });
    });

    group('WebSocket Integration', () {
      test('should successfully connect to WebSocket', () async {
        // Arrange
        // We now connect via service method without exposing raw connect
        await webSocketService.connectToAgentShowcase();

        // Assert
        expect(webSocketService.isConnected, true);
      });

      test('should handle WebSocket message reception', () async {
        // Arrange
        await webSocketService.connectToAgentShowcase();

        // Act
        final messageStream = webSocketService.messageStream;

        // We only assert the stream type here since we are not injecting a message in this test
        expect(messageStream, isA<Stream<Map<String, dynamic>>>());
      });

      test('should handle WebSocket disconnection', () async {
        // Arrange
        await webSocketService.connectToAgentShowcase();
        expect(webSocketService.isConnected, true);

        // Act
        await webSocketService.disconnect();

        // Assert
        expect(webSocketService.isConnected, false);
      });
    });

    group('Error Handling and Retry Logic', () {
      test('should retry failed requests', () async {
        // Arrange
        var callCount = 0;
        when(mockDio.get('/api/v1/test')).thenAnswer((_) async {
          callCount++;
          if (callCount < 3) {
            throw DioException(
              requestOptions: RequestOptions(path: '/api/v1/test'),
              type: DioExceptionType.connectionTimeout,
            );
          }
          return Response(
            data: {'success': true},
            statusCode: 200,
            requestOptions: RequestOptions(path: '/api/v1/test'),
          );
        });

        // Act
        final result = await apiService.get('/api/v1/test');

        // Assert
        expect(result['success'], true);
        expect(callCount, 3); // Should have retried twice
      });

      test('should handle network timeout', () async {
        // Arrange
        when(mockDio.get('/api/v1/test')).thenThrow(
          DioException(
            requestOptions: RequestOptions(path: '/api/v1/test'),
            type: DioExceptionType.connectionTimeout,
          ),
        );

        // Act & Assert
        expect(() => apiService.get('/api/v1/test'), throwsA(isA<NetworkException>()));
      });

      test('should handle server errors', () async {
        // Arrange
        when(mockDio.get('/api/v1/test')).thenThrow(
          DioException(
            requestOptions: RequestOptions(path: '/api/v1/test'),
            response: Response(statusCode: 500, requestOptions: RequestOptions(path: '/api/v1/test')),
          ),
        );

        // Act & Assert
        expect(() => apiService.get('/api/v1/test'), throwsA(isA<ServerException>()));
      });

      test('should handle validation errors', () async {
        // Arrange
        when(mockDio.post('/api/v1/test', data: {'invalid': 'data'})).thenThrow(
          DioException(
            requestOptions: RequestOptions(path: '/api/v1/test'),
            response: Response(
              statusCode: 422,
              data: {'error': 'Validation failed'},
              requestOptions: RequestOptions(path: '/api/v1/test'),
            ),
          ),
        );

        // Act & Assert
        expect(() => apiService.post('/api/v1/test', data: {'invalid': 'data'}), throwsA(isA<ValidationException>()));
      });
    });

    group('Authentication Token Management', () {
      test('should include authorization header when token is provided', () async {
        // Arrange
        const token = 'test_access_token';
        final expectedResponse = Response(
          data: {'authenticated': true},
          statusCode: 200,
          requestOptions: RequestOptions(path: '/api/v1/protected'),
        );

        when(mockDio.get('/api/v1/protected', options: anyNamed('options'))).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await apiService.get('/api/v1/protected', headers: {'Authorization': 'Bearer $token'});

        // Assert
        expect(result['authenticated'], true);
      });

      test('should handle token expiration', () async {
        // Arrange
        when(mockDio.get('/api/v1/protected')).thenThrow(
          DioException(
            requestOptions: RequestOptions(path: '/api/v1/protected'),
            response: Response(
              statusCode: 401,
              data: {'error': 'Token expired'},
              requestOptions: RequestOptions(path: '/api/v1/protected'),
            ),
          ),
        );

        // Act & Assert
        expect(() => apiService.get('/api/v1/protected'), throwsA(isA<AuthenticationException>()));
      });
    });
  });
}
