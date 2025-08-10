import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:flipsync_mobile/data/repositories/decisions_repository.dart';
import 'package:flipsync_mobile/core/network/api_service.dart';
import 'package:flipsync_mobile/core/errors/exceptions.dart';

import '../../../test/unit/repositories/auth_repository_test.mocks.dart';

@GenerateMocks([ApiService])
void main() {
  group('DecisionsRepository Tests', () {
    late DecisionsRepository decisionsRepository;
    late MockApiService mockApiService;

    setUp(() {
      mockApiService = MockApiService();
      decisionsRepository = DecisionsRepository(mockApiService);
    });

    group('Agent Decisions', () {
      test('should fetch agent decisions successfully', () async {
        // Arrange
        const agentId = 'content_autonomous_agent';
        final expectedDecisions = [
          {
            'id': '1',
            'agent_id': agentId,
            'decision_type': 'content_optimization',
            'confidence': 0.95,
            'timestamp': '2024-01-01T00:00:00Z',
            'data': {'title': 'Optimized Title', 'description': 'Optimized Description'},
          },
          {
            'id': '2',
            'agent_id': agentId,
            'decision_type': 'pricing_adjustment',
            'confidence': 0.87,
            'timestamp': '2024-01-01T01:00:00Z',
            'data': {'old_price': 29.99, 'new_price': 34.99},
          },
        ];

        when(
          mockApiService.get('/api/v1/decisions/4plus1/$agentId'),
        ).thenAnswer((_) async => {'decisions': expectedDecisions});

        // Act
        final result = await decisionsRepository.getAgentDecisions(agentId);

        // Assert
        expect(result, expectedDecisions);
        verify(mockApiService.get('/api/v1/decisions/4plus1/$agentId')).called(1);
      });

      test('should fetch decisions with filters', () async {
        // Arrange
        const agentId = 'market_autonomous_agent';
        const limit = 10;
        const offset = 0;
        const decisionType = 'pricing_optimization';

        final expectedDecisions = [
          {
            'id': '3',
            'agent_id': agentId,
            'decision_type': decisionType,
            'confidence': 0.92,
            'timestamp': '2024-01-01T02:00:00Z',
            'data': {'strategy': 'competitive_pricing'},
          },
        ];

        when(
          mockApiService.get(
            '/api/v1/decisions/4plus1/$agentId',
            queryParameters: {'limit': limit, 'offset': offset, 'decision_type': decisionType},
          ),
        ).thenAnswer((_) async => {'decisions': expectedDecisions});

        // Act
        final result = await decisionsRepository.getAgentDecisions(
          agentId,
          limit: limit,
          offset: offset,
          decisionType: decisionType,
        );

        // Assert
        expect(result, expectedDecisions);
        verify(
          mockApiService.get(
            '/api/v1/decisions/4plus1/$agentId',
            queryParameters: {'limit': limit, 'offset': offset, 'decision_type': decisionType},
          ),
        ).called(1);
      });

      test('should throw ServerException when fetching decisions fails', () async {
        // Arrange
        const agentId = 'invalid_agent';
        when(
          mockApiService.get('/api/v1/decisions/4plus1/$agentId'),
        ).thenThrow(const ServerException('Agent not found'));

        // Act & Assert
        expect(() => decisionsRepository.getAgentDecisions(agentId), throwsA(isA<ServerException>()));
      });
    });

    group('Decision Analytics', () {
      test('should fetch decision analytics successfully', () async {
        // Arrange
        const agentId = 'executive_autonomous_agent';
        final expectedAnalytics = {
          'total_decisions': 150,
          'success_rate': 0.94,
          'average_confidence': 0.89,
          'decision_types': {'strategic_planning': 45, 'resource_allocation': 35, 'performance_optimization': 70},
          'performance_metrics': {'response_time_ms': 245, 'accuracy_score': 0.96, 'efficiency_rating': 0.91},
        };

        when(
          mockApiService.get('/api/v1/decisions/4plus1/$agentId/analytics'),
        ).thenAnswer((_) async => expectedAnalytics);

        // Act
        final result = await decisionsRepository.getDecisionAnalytics(agentId: agentId);

        // Assert
        expect(result, expectedAnalytics);
        verify(mockApiService.getDecisionAnalytics(agentId: agentId, timeRangeHours: 24)).called(1);
      });

      test('should fetch analytics with time range', () async {
        // Arrange
        const agentId = 'logistics_autonomous_agent';
        const startDate = '2024-01-01';
        const endDate = '2024-01-31';

        final expectedAnalytics = {'total_decisions': 89, 'success_rate': 0.91, 'average_confidence': 0.85};

        when(
          mockApiService.get(
            '/api/v1/decisions/4plus1/$agentId/analytics',
            queryParameters: {'start_date': startDate, 'end_date': endDate},
          ),
        ).thenAnswer((_) async => expectedAnalytics);

        // Act
        final result = await decisionsRepository.getDecisionAnalytics(agentId: agentId, timeRangeHours: 24 * 30);

        // Assert
        expect(result, expectedAnalytics);
        verify(
          mockApiService.get(
            '/api/v1/decisions/4plus1/$agentId/analytics',
            queryParameters: {'start_date': startDate, 'end_date': endDate},
          ),
        ).called(1);
      });
    });

    group('Decision Submission', () {
      test('should submit decision feedback successfully', () async {
        // Arrange
        const decisionId = 'decision_123';
        const feedback = {'rating': 5, 'comment': 'Excellent decision', 'outcome': 'successful'};

        when(
          mockApiService.post('/api/v1/decisions/4plus1/$decisionId/feedback', data: feedback),
        ).thenAnswer((_) async => {'status': 'success', 'message': 'Feedback submitted'});

        // Act
        final result = await decisionsRepository.submitDecisionFeedback(decisionId, feedback);

        // Assert
        expect(result['status'], 'success');
        verify(mockApiService.post('/api/v1/decisions/4plus1/$decisionId/feedback', data: feedback)).called(1);
      });

      test('should request agent decision successfully', () async {
        // Arrange
        const agentId = 'content_autonomous_agent';
        final requestData = {'product_id': 'prod_123', 'context': 'listing_optimization', 'priority': 'high'};

        final expectedResponse = {
          'request_id': 'req_456',
          'status': 'processing',
          'estimated_completion': '2024-01-01T00:05:00Z',
        };

        when(
          mockApiService.post('/api/v1/decisions/4plus1/$agentId/request', data: requestData),
        ).thenAnswer((_) async => expectedResponse);

        // Act
        final result = await decisionsRepository.requestAgentDecision(agentId, requestData);

        // Assert
        expect(result, expectedResponse);
        verify(mockApiService.post('/api/v1/decisions/4plus1/$agentId/request', data: requestData)).called(1);
      });
    });

    group('Real-time Decision Updates', () {
      test('should fetch latest decisions successfully', () async {
        // Arrange
        final expectedDecisions = [
          {
            'id': '4',
            'agent_id': 'market_autonomous_agent',
            'decision_type': 'market_analysis',
            'confidence': 0.88,
            'timestamp': '2024-01-01T03:00:00Z',
            'is_new': true,
          },
        ];

        when(
          mockApiService.get('/api/v1/decisions/4plus1/latest'),
        ).thenAnswer((_) async => {'decisions': expectedDecisions});

        // Act
        final result = await decisionsRepository.getLatestDecisions();

        // Assert
        expect(result, expectedDecisions);
        verify(mockApiService.get('/api/v1/decisions/4plus1/latest')).called(1);
      });

      test('should fetch decision status successfully', () async {
        // Arrange
        const requestId = 'req_456';
        final expectedStatus = {
          'request_id': requestId,
          'status': 'completed',
          'decision': {'id': '5', 'confidence': 0.93, 'result': 'optimization_complete'},
        };

        when(mockApiService.get('/api/v1/decisions/4plus1/status/$requestId')).thenAnswer((_) async => expectedStatus);

        // Act
        final result = await decisionsRepository.getDecisionStatus(requestId);

        // Assert
        expect(result, expectedStatus);
        verify(mockApiService.get('/api/v1/decisions/4plus1/status/$requestId')).called(1);
      });
    });

    group('Error Handling', () {
      test('should handle network errors gracefully', () async {
        // Arrange
        const agentId = 'content_autonomous_agent';
        when(mockApiService.get('/api/v1/decisions/4plus1/$agentId')).thenThrow(NetworkException('Connection timeout'));

        // Act & Assert
        expect(() => decisionsRepository.getAgentDecisions(agentId), throwsA(isA<NetworkException>()));
      });

      test('should handle server errors gracefully', () async {
        // Arrange
        const agentId = 'content_autonomous_agent';
        when(
          mockApiService.get('/api/v1/decisions/4plus1/$agentId'),
        ).thenThrow(ServerException('Internal server error'));

        // Act & Assert
        expect(() => decisionsRepository.getAgentDecisions(agentId), throwsA(isA<ServerException>()));
      });

      test('should handle validation errors gracefully', () async {
        // Arrange
        const decisionId = 'invalid_decision';
        final feedback = {'rating': 10}; // Invalid rating

        when(
          mockApiService.post('/api/v1/decisions/4plus1/$decisionId/feedback', data: feedback),
        ).thenThrow(const ValidationException.simple('Invalid rating value'));

        // Act & Assert
        expect(
          () => decisionsRepository.submitDecisionFeedback(decisionId, feedback),
          throwsA(isA<ValidationException>()),
        );
      });
    });
  });
}
