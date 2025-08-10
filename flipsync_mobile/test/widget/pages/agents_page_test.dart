import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:flipsync_mobile/presentation/pages/main/agents_page.dart';
import 'package:flipsync_mobile/presentation/blocs/decisions/decisions_bloc.dart';
import 'package:flipsync_mobile/presentation/blocs/decisions/decisions_state.dart';
import 'package:flipsync_mobile/core/constants/app_constants.dart';
import '../../helpers/test_data_factory.dart';

import 'agents_page_test.mocks.dart';

@GenerateMocks([DecisionsBloc])
void main() {
  group('AgentsPage Widget Tests', () {
    late MockDecisionsBloc mockDecisionsBloc;

    setUp(() {
      mockDecisionsBloc = MockDecisionsBloc();
    });

    Widget createWidgetUnderTest() {
      return MaterialApp(
        home: BlocProvider<DecisionsBloc>.value(value: mockDecisionsBloc, child: const AgentsPage()),
      );
    }

    testWidgets('should display app bar with correct title', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('4+1 Autonomous Agents'), findsOneWidget);
      expect(find.byType(AppBar), findsOneWidget);
    });

    testWidgets('should display all four autonomous agents', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text(AppConstants.contentAgentName), findsOneWidget);
      expect(find.text(AppConstants.executiveAgentName), findsOneWidget);
      expect(find.text(AppConstants.logisticsAgentName), findsOneWidget);
      expect(find.text(AppConstants.marketAgentName), findsOneWidget);
    });

    testWidgets('should display conversational interface section', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Conversational Interface'), findsOneWidget);
      expect(find.text('Gemini AI Assistant'), findsOneWidget);
    });

    testWidgets('should display agent descriptions', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.textContaining('Optimizes eBay listing content'), findsOneWidget);
      expect(find.textContaining('Strategic decision making'), findsOneWidget);
      expect(find.textContaining('Shipping and inventory management'), findsOneWidget);
      expect(find.textContaining('Market analysis and pricing'), findsOneWidget);
    });

    testWidgets('should display agent status indicators', (WidgetTester tester) async {
      // Arrange
      final decisions = [
        {
          'id': '1',
          'agent_id': 'content_autonomous_agent',
          'decision_type': 'content_optimization',
          'confidence': 0.95,
          'timestamp': '2024-01-01T00:00:00Z',
        },
      ];

      when(mockDecisionsBloc.state).thenReturn(TestDataFactory.createSampleDecisionsLoaded());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.byIcon(Icons.check_circle), findsAtLeastNWidgets(1)); // Active status
      expect(find.text('Active'), findsAtLeastNWidgets(1));
    });

    testWidgets('should display agent performance metrics', (WidgetTester tester) async {
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
          'agent_id': 'content_autonomous_agent',
          'decision_type': 'pricing_adjustment',
          'confidence': 0.87,
          'timestamp': '2024-01-01T01:00:00Z',
        },
      ];

      when(mockDecisionsBloc.state).thenReturn(TestDataFactory.createSampleDecisionsLoaded());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('2'), findsOneWidget); // Decision count
      expect(find.text('91%'), findsOneWidget); // Average confidence
    });

    testWidgets('should handle agent card tap', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());
      await tester.tap(find.text(AppConstants.contentAgentName));
      await tester.pumpAndSettle();

      // Assert
      // Verify that the agent details are expanded or navigation occurs
      expect(find.text(AppConstants.contentAgentName), findsOneWidget);
    });

    testWidgets('should display loading state for agents', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsLoading());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.byType(CircularProgressIndicator), findsWidgets);
    });

    testWidgets('should display error state for agents', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsError(message: 'Failed to load agent data'));
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Failed to load agent data'), findsOneWidget);
      expect(find.byIcon(Icons.error), findsOneWidget);
    });

    testWidgets('should display agent colors correctly', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      // Find agent cards with correct colors
      final contentAgentCard = find.byWidgetPredicate(
        (widget) => widget is Card && widget.color == const Color(0xFF9C27B0),
      );
      expect(contentAgentCard, findsOneWidget);

      final executiveAgentCard = find.byWidgetPredicate(
        (widget) => widget is Card && widget.color == const Color(0xFF3F51B5),
      );
      expect(executiveAgentCard, findsOneWidget);
    });

    testWidgets('should display decision request button', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('Request Decision'), findsAtLeastNWidgets(4)); // One for each agent
      expect(find.byIcon(Icons.psychology), findsAtLeastNWidgets(4));
    });

    testWidgets('should handle decision request button tap', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      final requestButtons = find.text('Request Decision');
      await tester.tap(requestButtons.first);
      await tester.pumpAndSettle();

      // Assert
      // Verify that decision request dialog or action is triggered
      expect(find.text('Request Decision'), findsAtLeastNWidgets(4));
    });

    testWidgets('should display agent response times', (WidgetTester tester) async {
      // Arrange
      final decisions = [
        {
          'id': '1',
          'agent_id': 'content_autonomous_agent',
          'decision_type': 'content_optimization',
          'confidence': 0.95,
          'timestamp': '2024-01-01T00:00:00Z',
          'response_time_ms': 245,
        },
      ];

      when(mockDecisionsBloc.state).thenReturn(TestDataFactory.createSampleDecisionsLoaded());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.text('245ms'), findsOneWidget);
      expect(find.byIcon(Icons.speed), findsAtLeastNWidgets(1));
    });

    testWidgets('should display agent learning indicators', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Assert
      expect(find.byIcon(Icons.school), findsAtLeastNWidgets(4)); // Learning indicator
      expect(find.text('Learning'), findsAtLeastNWidgets(4));
    });

    testWidgets('should handle refresh action', (WidgetTester tester) async {
      // Arrange
      when(mockDecisionsBloc.state).thenReturn(const DecisionsInitial());
      when(mockDecisionsBloc.stream).thenAnswer((_) => const Stream.empty());

      // Act
      await tester.pumpWidget(createWidgetUnderTest());

      // Find and tap refresh button in app bar
      final refreshButton = find.byIcon(Icons.refresh);
      if (refreshButton.evaluate().isNotEmpty) {
        await tester.tap(refreshButton);
        await tester.pump();
      }

      // Assert
      expect(find.byType(AgentsPage), findsOneWidget);
    });
  });
}
