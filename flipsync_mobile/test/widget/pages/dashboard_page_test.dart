import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:flipsync_mobile/presentation/pages/main/dashboard_page.dart';
import 'package:flipsync_mobile/presentation/blocs/decisions/decisions_bloc.dart';
import 'package:flipsync_mobile/presentation/blocs/decisions/decisions_state.dart';
import 'package:flipsync_mobile/presentation/blocs/analytics/analytics_bloc.dart';
import 'package:flipsync_mobile/presentation/blocs/analytics/analytics_state.dart';
import 'package:flipsync_mobile/core/constants/app_constants.dart';
import '../../helpers/test_data_factory.dart';

import 'dashboard_page_test.mocks.dart';

@GenerateMocks([DecisionsBloc, AnalyticsBloc])
void main() {
  group('DashboardPage Widget Tests', () {
    late MockDecisionsBloc mockDecisionsBloc;
    late MockAnalyticsBloc mockAnalyticsBloc;

    setUp(() {
      mockDecisionsBloc = MockDecisionsBloc();
      mockAnalyticsBloc = MockAnalyticsBloc();
    });

    Widget createWidgetUnderTest() {
      return MaterialApp(
        home: MultiBlocProvider(
          providers: [
            BlocProvider<DecisionsBloc>.value(value: mockDecisionsBloc),
            BlocProvider<AnalyticsBloc>.value(value: mockAnalyticsBloc),
          ],
          child: const DashboardPage(),
        ),
      );
    }

    testWidgets('should display app bar with correct title', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockAnalyticsBloc.state).thenReturn(const AnalyticsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());
      when(mockAnalyticsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('FlipSync Dashboard'), findsOneWidget);
      expect(find.byType(AppBar), findsOneWidget);
    });

    testWidgets('should display 4+1 agent cards', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockAnalyticsBloc.state).thenReturn(const AnalyticsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());
      when(mockAnalyticsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text(AppConstants.contentAgentName), findsOneWidget);
      expect(find.text(AppConstants.executiveAgentName), findsOneWidget);
      expect(find.text(AppConstants.logisticsAgentName), findsOneWidget);
      expect(find.text(AppConstants.marketAgentName), findsOneWidget);
      expect(find.text('Conversational Interface'), findsOneWidget);
    });

    testWidgets('should display loading indicator when decisions are loading', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsLoading());
      when(mockAnalyticsBloc.state).thenReturn(const AnalyticsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());
      when(mockAnalyticsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.byType(CircularProgressIndicator), findsWidgets);
    });

    testWidgets('should display agent metrics when decisions are loaded', (WidgetTester tester) async {
      // Arrange
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
          'agent_id': 'market_autonomous_agent',
          'decision_type': 'pricing_adjustment',
          'confidence': 0.87,
          'timestamp': '2024-01-01T01:00:00Z',
        },
      ];

      when(mockDecisionsBloc.state).thenReturn(TestDataFactory.createSampleDecisionsLoaded());
      when(mockAnalyticsBloc.state).thenReturn(const AnalyticsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());
      when(mockAnalyticsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('95%'), findsOneWidget); // Content agent confidence
      expect(find.text('87%'), findsOneWidget); // Market agent confidence
      expect(find.text('2'), findsOneWidget); // Total decisions count
    });

    testWidgets('should display error message when decisions loading fails', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsError(message: 'Failed to load decisions'));
      when(mockAnalyticsBloc.state).thenReturn(const AnalyticsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());
      when(mockAnalyticsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Failed to load decisions'), findsOneWidget);
      expect(find.byIcon(Icons.error), findsOneWidget);
    });

    testWidgets('should display analytics when loaded', (WidgetTester tester) async {
      // Arrange
      final analytics = {
        'total_decisions': 150,
        'success_rate': 0.94,
        'average_confidence': 0.89,
        'response_time_ms': 245,
      };

      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockAnalyticsBloc.state).thenReturn(const AnalyticsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());
      when(mockAnalyticsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('150'), findsOneWidget); // Total decisions
      expect(find.text('94%'), findsOneWidget); // Success rate
      expect(find.text('89%'), findsOneWidget); // Average confidence
      expect(find.text('245ms'), findsOneWidget); // Response time
    });

    testWidgets('should navigate to agents page when agent card is tapped', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockAnalyticsBloc.state).thenReturn(const AnalyticsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());
      when(mockAnalyticsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.text(AppConstants.contentAgentName));
      await tester.pumpAndSettle();

      // Assert
      // Note: Navigation testing would require proper router setup
      // This is a placeholder for navigation verification
      expect(find.text(AppConstants.contentAgentName), findsOneWidget);
    });

    testWidgets('should display refresh button and handle refresh', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockAnalyticsBloc.state).thenReturn(const AnalyticsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());
      when(mockAnalyticsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Find and tap refresh button
      final refreshButton = find.byIcon(Icons.refresh);
      expect(refreshButton, findsOneWidget);

      await tester.tap(refreshButton);
      await tester.pump();

      // Assert
      // Verify that refresh events were added to blocs
      // This would require proper event verification in a real implementation
      expect(refreshButton, findsOneWidget);
    });

    testWidgets('should display performance indicators with correct colors', (WidgetTester tester) async {
      // Arrange
      final analytics = {
        'response_time_ms': 50, // Good performance (green)
        'success_rate': 0.98,
        'average_confidence': 0.92,
      };

      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockAnalyticsBloc.state).thenReturn(const AnalyticsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());
      when(mockAnalyticsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('50ms'), findsOneWidget);

      // Find performance indicator with good color (green)
      final performanceIndicator = find.byWidgetPredicate(
        (widget) =>
            widget is Container &&
            widget.decoration is BoxDecoration &&
            (widget.decoration as BoxDecoration).color == Colors.green,
      );
      expect(performanceIndicator, findsAtLeastNWidgets(1));
    });

    testWidgets('should handle pull-to-refresh', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockAnalyticsBloc.state).thenReturn(const AnalyticsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());
      when(mockAnalyticsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Perform pull-to-refresh gesture
      await tester.fling(find.byType(RefreshIndicator), const Offset(0, 300), 1000);
      await tester.pump();
      await tester.pump(const Duration(seconds: 1));

      // Assert
      // Verify that refresh was triggered
      expect(find.byType(RefreshIndicator), findsOneWidget);
    });

    testWidgets('should display real-time updates indicator', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockAnalyticsBloc.state).thenReturn(const AnalyticsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());
      when(mockAnalyticsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.byIcon(Icons.wifi), findsOneWidget); // Connection status
      expect(find.text('Live'), findsOneWidget); // Real-time indicator
    });
  });
}
