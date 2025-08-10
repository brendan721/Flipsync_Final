import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:flipsync_mobile/main.dart' as app;
import 'package:flipsync_mobile/data/repositories/auth_repository.dart';
import 'package:flipsync_mobile/data/repositories/decisions_repository.dart';
import 'package:flipsync_mobile/core/network/api_service.dart';
import 'package:flipsync_mobile/core/network/websocket_service.dart';

import 'user_journey_test.mocks.dart';

@GenerateMocks([AuthRepository, DecisionsRepository, ApiService, WebSocketService])
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('FlipSync User Journey Integration Tests', () {
    late MockAuthRepository mockAuthRepository;
    late MockDecisionsRepository mockDecisionsRepository;
    late MockApiService mockApiService;
    late MockWebSocketService mockWebSocketService;

    setUp(() {
      mockAuthRepository = MockAuthRepository();
      mockDecisionsRepository = MockDecisionsRepository();
      mockApiService = MockApiService();
      mockWebSocketService = MockWebSocketService();
    });

    testWidgets('Complete onboarding flow', (WidgetTester tester) async {
      // Arrange - Mock successful responses
      when(mockAuthRepository.getStoredTokens()).thenAnswer((_) async => null);
      when(
        mockAuthRepository.getEbayOAuthUrl(),
      ).thenAnswer((_) async => 'https://auth.ebay.com/oauth2/authorize?client_id=test');

      // Act - Start the app
      app.main();
      await tester.pumpAndSettle();

      // Assert - Should show welcome page
      expect(find.text('Welcome to FlipSync'), findsOneWidget);
      expect(find.text('4+1 Autonomous Agent Architecture'), findsOneWidget);

      // Act - Tap "Get Started" button
      await tester.tap(find.text('Get Started'));
      await tester.pumpAndSettle();

      // Assert - Should navigate to onboarding
      expect(find.text('Step 1 of 6'), findsOneWidget);
      expect(find.text('Meet Your Autonomous Agents'), findsOneWidget);

      // Act - Complete onboarding steps
      for (int i = 0; i < 6; i++) {
        await tester.tap(find.text('Next'));
        await tester.pumpAndSettle();
      }

      // Assert - Should reach eBay connection step
      expect(find.text('Connect Your eBay Account'), findsOneWidget);
      expect(find.text('Connect to eBay'), findsOneWidget);
    });

    testWidgets('eBay OAuth authentication flow', (WidgetTester tester) async {
      // Arrange - Mock OAuth flow
      when(mockAuthRepository.getStoredTokens()).thenAnswer((_) async => null);
      when(
        mockAuthRepository.getEbayOAuthUrl(),
      ).thenAnswer((_) async => 'https://auth.ebay.com/oauth2/authorize?client_id=test');
      when(mockAuthRepository.exchangeCodeForTokens('test_code', 'test_state')).thenAnswer(
        (_) async => {'access_token': 'test_access_token', 'refresh_token': 'test_refresh_token', 'expires_in': 7200},
      );
      when(mockAuthRepository.storeTokens(any, any, any)).thenAnswer((_) async {});

      // Start app and navigate to OAuth
      app.main();
      await tester.pumpAndSettle();

      // Skip to OAuth step (assuming navigation works)
      await tester.tap(find.text('Get Started'));
      await tester.pumpAndSettle();

      // Navigate through onboarding to OAuth step
      for (int i = 0; i < 6; i++) {
        if (find.text('Next').evaluate().isNotEmpty) {
          await tester.tap(find.text('Next'));
          await tester.pumpAndSettle();
        }
      }

      // Act - Tap "Connect to eBay" button
      if (find.text('Connect to eBay').evaluate().isNotEmpty) {
        await tester.tap(find.text('Connect to eBay'));
        await tester.pumpAndSettle();

        // Assert - Should show OAuth loading or success
        expect(find.byType(CircularProgressIndicator), findsOneWidget);
      }
    });

    testWidgets('Dashboard navigation and agent interaction', (WidgetTester tester) async {
      // Arrange - Mock authenticated state
      when(mockAuthRepository.getStoredTokens()).thenAnswer(
        (_) async => {
          'access_token': 'valid_token',
          'refresh_token': 'valid_refresh_token',
          'expires_at': DateTime.now().add(const Duration(hours: 1)).millisecondsSinceEpoch,
        },
      );
      when(mockAuthRepository.validateToken(any)).thenAnswer((_) async => true);

      final mockDecisions = [
        {
          'id': '1',
          'agent_id': 'content_autonomous_agent',
          'decision_type': 'content_optimization',
          'confidence': 0.95,
          'timestamp': '2024-01-01T00:00:00Z',
        },
      ];
      when(mockDecisionsRepository.getAgentDecisions(any)).thenAnswer((_) async => mockDecisions);
      when(mockDecisionsRepository.getLatestDecisions()).thenAnswer((_) async => mockDecisions);

      // Act - Start app (should go directly to dashboard)
      app.main();
      await tester.pumpAndSettle();

      // Assert - Should show dashboard
      expect(find.text('FlipSync Dashboard'), findsOneWidget);
      expect(find.text('Content Agent'), findsOneWidget);
      expect(find.text('Executive Agent'), findsOneWidget);
      expect(find.text('Logistics Agent'), findsOneWidget);
      expect(find.text('Market Agent'), findsOneWidget);

      // Act - Navigate to Agents page
      await tester.tap(find.byIcon(Icons.psychology));
      await tester.pumpAndSettle();

      // Assert - Should show agents page
      expect(find.text('4+1 Autonomous Agents'), findsOneWidget);

      // Act - Tap on Content Agent
      await tester.tap(find.text('Content Agent'));
      await tester.pumpAndSettle();

      // Assert - Should show agent details or navigate to agent page
      expect(find.text('Content Agent'), findsOneWidget);
    });

    testWidgets('Real-time decision updates via WebSocket', (WidgetTester tester) async {
      // Arrange - Mock WebSocket connection
      when(mockWebSocketService.connectToAgentShowcase()).thenAnswer((_) async => {});
      when(mockWebSocketService.isConnected).thenReturn(true);
      when(mockWebSocketService.messageStream).thenAnswer(
        (_) => Stream.fromIterable([
          {
            'type': 'decision_update',
            'agent_id': 'content_autonomous_agent',
            'decision': {
              'id': '2',
              'decision_type': 'new_optimization',
              'confidence': 0.92,
              'timestamp': DateTime.now().toIso8601String(),
            },
          },
        ]),
      );

      // Mock authenticated state
      when(mockAuthRepository.getStoredTokens()).thenAnswer(
        (_) async => {
          'access_token': 'valid_token',
          'refresh_token': 'valid_refresh_token',
          'expires_at': DateTime.now().add(const Duration(hours: 1)).millisecondsSinceEpoch,
        },
      );
      when(mockAuthRepository.validateToken(any)).thenAnswer((_) async => true);

      // Act - Start app
      app.main();
      await tester.pumpAndSettle();

      // Wait for WebSocket connection and message
      await tester.pump(const Duration(seconds: 2));

      // Assert - Should show real-time update indicator
      expect(find.byIcon(Icons.wifi), findsOneWidget);
      expect(find.text('Live'), findsOneWidget);
    });

    testWidgets('Error handling and recovery', (WidgetTester tester) async {
      // Arrange - Mock network error
      when(mockAuthRepository.getStoredTokens()).thenThrow(Exception('Network error'));

      // Act - Start app
      app.main();
      await tester.pumpAndSettle();

      // Assert - Should show error state
      expect(find.byIcon(Icons.error), findsOneWidget);
      expect(find.text('Network error'), findsOneWidget);

      // Act - Tap retry button
      if (find.text('Retry').evaluate().isNotEmpty) {
        await tester.tap(find.text('Retry'));
        await tester.pumpAndSettle();
      }

      // Assert - Should attempt to recover
      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('Settings and logout flow', (WidgetTester tester) async {
      // Arrange - Mock authenticated state
      when(mockAuthRepository.getStoredTokens()).thenAnswer(
        (_) async => {
          'access_token': 'valid_token',
          'refresh_token': 'valid_refresh_token',
          'expires_at': DateTime.now().add(const Duration(hours: 1)).millisecondsSinceEpoch,
        },
      );
      when(mockAuthRepository.validateToken(any)).thenAnswer((_) async => true);
      when(mockAuthRepository.clearTokens()).thenAnswer((_) async {});

      // Act - Start app
      app.main();
      await tester.pumpAndSettle();

      // Navigate to settings
      await tester.tap(find.byIcon(Icons.settings));
      await tester.pumpAndSettle();

      // Assert - Should show settings page
      expect(find.text('Settings'), findsOneWidget);
      expect(find.text('Partnership Settings'), findsOneWidget);

      // Act - Tap logout
      await tester.tap(find.text('Logout'));
      await tester.pumpAndSettle();

      // Assert - Should return to welcome page
      expect(find.text('Welcome to FlipSync'), findsOneWidget);
    });

    testWidgets('Chat interface interaction', (WidgetTester tester) async {
      // Arrange - Mock authenticated state
      when(mockAuthRepository.getStoredTokens()).thenAnswer(
        (_) async => {
          'access_token': 'valid_token',
          'refresh_token': 'valid_refresh_token',
          'expires_at': DateTime.now().add(const Duration(hours: 1)).millisecondsSinceEpoch,
        },
      );
      when(mockAuthRepository.validateToken(any)).thenAnswer((_) async => true);

      // Act - Start app
      app.main();
      await tester.pumpAndSettle();

      // Navigate to chat
      await tester.tap(find.byIcon(Icons.chat));
      await tester.pumpAndSettle();

      // Assert - Should show chat interface
      expect(find.text('Gemini AI Assistant'), findsOneWidget);
      expect(find.byType(TextField), findsOneWidget);

      // Act - Type a message
      await tester.enterText(find.byType(TextField), 'Hello, how are my agents performing?');
      await tester.tap(find.byIcon(Icons.send));
      await tester.pumpAndSettle();

      // Assert - Should show message in chat
      expect(find.text('Hello, how are my agents performing?'), findsOneWidget);
    });

    testWidgets('Performance monitoring and metrics', (WidgetTester tester) async {
      // Arrange - Mock performance data
      when(mockAuthRepository.getStoredTokens()).thenAnswer(
        (_) async => {
          'access_token': 'valid_token',
          'refresh_token': 'valid_refresh_token',
          'expires_at': DateTime.now().add(const Duration(hours: 1)).millisecondsSinceEpoch,
        },
      );
      when(mockAuthRepository.validateToken(any)).thenAnswer((_) async => true);

      final mockAnalytics = {
        'total_decisions': 150,
        'success_rate': 0.94,
        'average_confidence': 0.89,
        'response_time_ms': 245,
      };

      // Act - Start app
      app.main();
      await tester.pumpAndSettle();

      // Assert - Should show performance metrics
      expect(find.text('150'), findsOneWidget); // Total decisions
      expect(find.text('94%'), findsOneWidget); // Success rate
      expect(find.text('245ms'), findsOneWidget); // Response time

      // Act - Navigate to analytics
      if (find.byIcon(Icons.analytics).evaluate().isNotEmpty) {
        await tester.tap(find.byIcon(Icons.analytics));
        await tester.pumpAndSettle();

        // Assert - Should show detailed analytics
        expect(find.text('Analytics Dashboard'), findsOneWidget);
      }
    });
  });
}
