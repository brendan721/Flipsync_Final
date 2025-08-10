import 'package:flutter_test/flutter_test.dart';
import 'package:bloc_test/bloc_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:flipsync_mobile/presentation/blocs/decisions/decisions_bloc.dart';
import 'package:flipsync_mobile/presentation/blocs/decisions/decisions_event.dart';
import 'package:flipsync_mobile/presentation/blocs/decisions/decisions_state.dart';
import 'package:flipsync_mobile/data/repositories/decisions_repository.dart';
import 'package:flipsync_mobile/core/network/websocket_service.dart';
import 'package:flipsync_mobile/core/errors/exceptions.dart';
import 'package:flipsync_mobile/data/models/decision_model.dart';
import '../../helpers/test_data_factory.dart';

import 'decisions_bloc_test.mocks.dart';

@GenerateMocks([DecisionsRepository, WebSocketService])
void main() {
  group('DecisionsBloc Tests', () {
    late DecisionsBloc decisionsBloc;
    late MockDecisionsRepository mockDecisionsRepository;
    late MockWebSocketService mockWebSocketService;

    setUp(() {
      mockDecisionsRepository = MockDecisionsRepository();
      mockWebSocketService = MockWebSocketService();
      decisionsBloc = DecisionsBloc(mockDecisionsRepository, mockWebSocketService);
    });

    tearDown(() {
      decisionsBloc.close();
    });

    test('initial state is DecisionsInitial', () {
      expect(decisionsBloc.state, const DecisionsInitial());
    });

    group('DecisionsLoadRequested', () {
      blocTest<DecisionsBloc, DecisionsState>(
        'emits [DecisionsLoading, DecisionsLoaded] when decisions are loaded successfully',
        build: () {
          final decisions = [
            {
              'id': '1',
              'agent_id': 'content_autonomous_agent',
              'decision_type': 'content_optimization',
              'confidence': 0.95,
              'timestamp': '2024-01-01T00:00:00Z',
            },
            {
              'id': '2',
              'agent_id': 'content_autonomous_agent',
              'decision_type': 'pricing_adjustment',
              'confidence': 0.87,
              'timestamp': '2024-01-01T01:00:00Z',
            },
          ];
          when(
            mockDecisionsRepository.getAgentDecisions('content_autonomous_agent'),
          ).thenAnswer((_) async => decisions);
          return decisionsBloc;
        },
        act: (bloc) => bloc.add(const DecisionsLoadRequested(agentId: 'content_autonomous_agent')),
        expect: () => [
          const DecisionsLoading(),
          TestDataFactory.createSampleDecisionsLoaded(
            decisions: TestDataFactory.createSampleDecisionsList(count: 2, agentId: 'content_autonomous_agent'),
          ),
        ],
        verify: (_) {
          verify(mockDecisionsRepository.getAgentDecisions('content_autonomous_agent')).called(1);
        },
      );

      blocTest<DecisionsBloc, DecisionsState>(
        'emits [DecisionsLoading, DecisionsError] when loading decisions fails',
        build: () {
          when(
            mockDecisionsRepository.getAgentDecisions('invalid_agent'),
          ).thenThrow(const ServerException('Agent not found'));
          return decisionsBloc;
        },
        act: (bloc) => bloc.add(const DecisionsLoadRequested(agentId: 'invalid_agent')),
        expect: () => [const DecisionsLoading(), const DecisionsError(message: 'Agent not found')],
        verify: (_) {
          verify(mockDecisionsRepository.getAgentDecisions('invalid_agent')).called(1);
        },
      );
    });

    group('DecisionsLoadRequested (Analytics)', () {
      blocTest<DecisionsBloc, DecisionsState>(
        'emits [DecisionsLoading, DecisionAnalyticsLoaded] when analytics are loaded successfully',
        build: () {
          final analytics = {
            'total_decisions': 150,
            'success_rate': 0.94,
            'average_confidence': 0.89,
            'decision_types': {'content_optimization': 45, 'pricing_adjustment': 35, 'listing_enhancement': 70},
          };
          when(
            mockDecisionsRepository.getDecisionAnalytics(agentId: 'content_autonomous_agent'),
          ).thenAnswer((_) async => analytics);
          return decisionsBloc;
        },
        act: (bloc) => bloc.add(const DecisionAnalyticsLoadRequested(agentId: 'content_autonomous_agent')),
        expect: () => [
          const DecisionsLoading(),
          DecisionAnalyticsLoaded(
            analytics: const {
              'total_decisions': 150,
              'success_rate': 0.94,
              'average_confidence': 0.89,
              'decision_types': {'content_optimization': 45, 'pricing_adjustment': 35, 'listing_enhancement': 70},
            },
            lastUpdated: DateTime.parse('2024-01-01T00:00:00Z'),
          ),
        ],
        verify: (_) {
          verify(mockDecisionsRepository.getDecisionAnalytics(agentId: 'content_autonomous_agent')).called(1);
        },
      );

      blocTest<DecisionsBloc, DecisionsState>(
        'emits [DecisionsLoading, DecisionsError] when loading analytics fails',
        build: () {
          when(
            mockDecisionsRepository.getDecisionAnalytics(agentId: 'content_autonomous_agent'),
          ).thenThrow(const ServerException('Analytics service unavailable'));
          return decisionsBloc;
        },
        act: (bloc) => bloc.add(const DecisionsLoadRequested(agentId: 'content_autonomous_agent')),
        expect: () => [const DecisionsLoading(), const DecisionsError(message: 'Analytics service unavailable')],
        verify: (_) {
          verify(mockDecisionsRepository.getDecisionAnalytics(agentId: 'content_autonomous_agent')).called(1);
        },
      );
    });

    group('RequestAgentDecision', () {
      blocTest<DecisionsBloc, DecisionsState>(
        'emits [DecisionsLoading, DecisionRequested] when decision request is successful',
        build: () {
          final requestData = {'product_id': 'prod_123', 'context': 'listing_optimization', 'priority': 'high'};
          final response = {
            'request_id': 'req_456',
            'status': 'processing',
            'estimated_completion': '2024-01-01T00:05:00Z',
          };
          when(
            mockDecisionsRepository.requestAgentDecision('content_autonomous_agent', requestData),
          ).thenAnswer((_) async => response);
          return decisionsBloc;
        },
        act: (bloc) => bloc.add(const DecisionsLoadRequested(agentId: 'content_autonomous_agent')),
        expect: () => [
          const DecisionsLoading(),
          TestDataFactory.createSampleDecisionsLoaded(
            decisions: TestDataFactory.createSampleDecisionsList(count: 1, agentId: 'content_autonomous_agent'),
          ),
        ],
        verify: (_) {
          verify(
            mockDecisionsRepository.requestAgentDecision('content_autonomous_agent', {
              'product_id': 'prod_123',
              'context': 'listing_optimization',
              'priority': 'high',
            }),
          ).called(1);
        },
      );

      blocTest<DecisionsBloc, DecisionsState>(
        'emits [DecisionsLoading, DecisionsError] when decision request fails',
        build: () {
          final requestData = {'product_id': 'invalid_product', 'context': 'invalid_context'};
          when(
            mockDecisionsRepository.requestAgentDecision('content_autonomous_agent', requestData),
          ).thenThrow(const ValidationException('Invalid request data', {}));
          return decisionsBloc;
        },
        act: (bloc) => bloc.add(const DecisionsLoadRequested(agentId: 'content_autonomous_agent')),
        expect: () => [const DecisionsLoading(), const DecisionsError(message: 'Invalid request data')],
        verify: (_) {
          verify(
            mockDecisionsRepository.requestAgentDecision('content_autonomous_agent', {
              'product_id': 'invalid_product',
              'context': 'invalid_context',
            }),
          ).called(1);
        },
      );
    });

    group('SubmitDecisionFeedback', () {
      blocTest<DecisionsBloc, DecisionsState>(
        'emits [DecisionsLoading, DecisionFeedbackSubmitted] when feedback is submitted successfully',
        build: () {
          final feedback = {'rating': 5, 'comment': 'Excellent decision', 'outcome': 'successful'};
          final response = {'status': 'success', 'message': 'Feedback submitted successfully'};
          when(
            mockDecisionsRepository.submitDecisionFeedback('decision_123', feedback),
          ).thenAnswer((_) async => response);
          return decisionsBloc;
        },
        act: (bloc) => bloc.add(const DecisionsRefreshRequested()),
        expect: () => [const DecisionsLoading(), TestDataFactory.createSampleDecisionsLoaded()],
        verify: (_) {
          verify(
            mockDecisionsRepository.submitDecisionFeedback('decision_123', {
              'rating': 5,
              'comment': 'Excellent decision',
              'outcome': 'successful',
            }),
          ).called(1);
        },
      );

      blocTest<DecisionsBloc, DecisionsState>(
        'emits [DecisionsLoading, DecisionsError] when feedback submission fails',
        build: () {
          final feedback = {'rating': 10}; // Invalid rating
          when(
            mockDecisionsRepository.submitDecisionFeedback('decision_123', feedback),
          ).thenThrow(const ValidationException('Invalid rating value', {}));
          return decisionsBloc;
        },
        act: (bloc) => bloc.add(const DecisionsRefreshRequested()),
        expect: () => [const DecisionsLoading(), const DecisionsError(message: 'Invalid rating value')],
        verify: (_) {
          verify(mockDecisionsRepository.submitDecisionFeedback('decision_123', {'rating': 10})).called(1);
        },
      );
    });

    group('DecisionsLoadRequested (Latest)', () {
      blocTest<DecisionsBloc, DecisionsState>(
        'emits [DecisionsLoading, LatestDecisionsLoaded] when latest decisions are loaded successfully',
        build: () {
          final latestDecisions = [
            {
              'id': '3',
              'agent_id': 'market_autonomous_agent',
              'decision_type': 'market_analysis',
              'confidence': 0.88,
              'timestamp': '2024-01-01T03:00:00Z',
              'is_new': true,
            },
          ];
          when(mockDecisionsRepository.getLatestDecisions()).thenAnswer((_) async => latestDecisions);
          return decisionsBloc;
        },
        act: (bloc) => bloc.add(const DecisionsLoadRequested()),
        expect: () => [
          const DecisionsLoading(),
          TestDataFactory.createSampleDecisionsLoaded(
            decisions: TestDataFactory.createSampleDecisionsList(count: 1, agentId: 'market_autonomous_agent'),
          ),
        ],
        verify: (_) {
          verify(mockDecisionsRepository.getLatestDecisions()).called(1);
        },
      );
    });

    group('Error Handling', () {
      blocTest<DecisionsBloc, DecisionsState>(
        'handles network errors gracefully',
        build: () {
          when(
            mockDecisionsRepository.getAgentDecisions('content_autonomous_agent'),
          ).thenThrow(NetworkException('Connection timeout'));
          return decisionsBloc;
        },
        act: (bloc) => bloc.add(const DecisionsLoadRequested(agentId: 'content_autonomous_agent')),
        expect: () => [const DecisionsLoading(), const DecisionsError(message: 'Connection timeout')],
      );

      blocTest<DecisionsBloc, DecisionsState>(
        'handles server errors gracefully',
        build: () {
          when(
            mockDecisionsRepository.getAgentDecisions('content_autonomous_agent'),
          ).thenThrow(ServerException('Internal server error'));
          return decisionsBloc;
        },
        act: (bloc) => bloc.add(const DecisionsLoadRequested(agentId: 'content_autonomous_agent')),
        expect: () => [const DecisionsLoading(), const DecisionsError(message: 'Internal server error')],
      );

      blocTest<DecisionsBloc, DecisionsState>(
        'handles validation errors gracefully',
        build: () {
          when(
            mockDecisionsRepository.getAgentDecisions(''),
          ).thenThrow(const ValidationException('Agent ID cannot be empty', {}));
          return decisionsBloc;
        },
        act: (bloc) => bloc.add(const DecisionsLoadRequested(agentId: '')),
        expect: () => [const DecisionsLoading(), const DecisionsError(message: 'Agent ID cannot be empty')],
      );
    });
  });
}
