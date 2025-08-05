import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/features/dashboard/presentation/widgets/partnership_summary_card.dart';

void main() {
  group('PartnershipSummaryCard', () {
    testWidgets('should display partnership summary with correct data', (WidgetTester tester) async {
      // Arrange
      const humanTasks = 5;
      const agentTasks = 12;
      const sharedProfit = 127.50;
      const collaborationScore = 0.87;
      bool detailsPressed = false;

      // Act
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PartnershipSummaryCard(
              humanTasks: humanTasks,
              agentTasks: agentTasks,
              sharedProfit: sharedProfit,
              collaborationScore: collaborationScore,
              onViewDetails: () {
                detailsPressed = true;
              },
            ),
          ),
        ),
      );

      // Assert
      expect(find.text('Today\'s Collaboration Summary'), findsOneWidget);
      expect(find.text('Your Tasks'), findsOneWidget);
      expect(find.text('Agent Tasks'), findsOneWidget);
      expect(find.text(humanTasks.toString()), findsOneWidget);
      expect(find.text(agentTasks.toString()), findsOneWidget);
      expect(find.text('+\$${sharedProfit.toStringAsFixed(2)} profit today'), findsOneWidget);
      expect(find.text('87%'), findsOneWidget); // Collaboration score
      expect(find.text('Partnership Score'), findsOneWidget);
    });

    testWidgets('should display correct collaboration score colors', (WidgetTester tester) async {
      // Test high collaboration score (>= 0.8)
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PartnershipSummaryCard(
              humanTasks: 3,
              agentTasks: 8,
              sharedProfit: 100.0,
              collaborationScore: 0.9,
            ),
          ),
        ),
      );

      expect(find.text('90%'), findsOneWidget);
      expect(find.byIcon(Icons.trending_up), findsOneWidget);
    });

    testWidgets('should display medium collaboration score indicators', (WidgetTester tester) async {
      // Test medium collaboration score (0.6 - 0.8)
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PartnershipSummaryCard(
              humanTasks: 3,
              agentTasks: 8,
              sharedProfit: 100.0,
              collaborationScore: 0.7,
            ),
          ),
        ),
      );

      expect(find.text('70%'), findsOneWidget);
      expect(find.byIcon(Icons.trending_flat), findsOneWidget);
    });

    testWidgets('should display low collaboration score indicators', (WidgetTester tester) async {
      // Test low collaboration score (< 0.6)
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PartnershipSummaryCard(
              humanTasks: 3,
              agentTasks: 8,
              sharedProfit: 100.0,
              collaborationScore: 0.5,
            ),
          ),
        ),
      );

      expect(find.text('50%'), findsOneWidget);
      expect(find.byIcon(Icons.trending_down), findsOneWidget);
    });

    testWidgets('should handle onViewDetails callback', (WidgetTester tester) async {
      // Arrange
      bool callbackTriggered = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PartnershipSummaryCard(
              humanTasks: 3,
              agentTasks: 8,
              sharedProfit: 100.0,
              collaborationScore: 0.8,
              onViewDetails: () {
                callbackTriggered = true;
              },
            ),
          ),
        ),
      );

      // Act
      await tester.tap(find.text('View Partnership Details'));
      await tester.pump();

      // Assert
      expect(callbackTriggered, isTrue);
    });

    testWidgets('should not show details button when callback is null', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PartnershipSummaryCard(
              humanTasks: 3,
              agentTasks: 8,
              sharedProfit: 100.0,
              collaborationScore: 0.8,
              // onViewDetails is null
            ),
          ),
        ),
      );

      expect(find.text('View Partnership Details'), findsNothing);
    });

    testWidgets('should display correct task subtitles', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PartnershipSummaryCard(
              humanTasks: 3,
              agentTasks: 8,
              sharedProfit: 100.0,
              collaborationScore: 0.8,
            ),
          ),
        ),
      );

      expect(find.text('items to assess'), findsOneWidget);
      expect(find.text('optimizations done'), findsOneWidget);
    });

    testWidgets('should display partnership icons correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PartnershipSummaryCard(
              humanTasks: 3,
              agentTasks: 8,
              sharedProfit: 100.0,
              collaborationScore: 0.8,
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.handshake), findsOneWidget);
      expect(find.byIcon(Icons.person), findsOneWidget);
      expect(find.byIcon(Icons.psychology), findsOneWidget);
    });

    testWidgets('should handle zero values gracefully', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PartnershipSummaryCard(
              humanTasks: 0,
              agentTasks: 0,
              sharedProfit: 0.0,
              collaborationScore: 0.0,
            ),
          ),
        ),
      );

      expect(find.text('0'), findsNWidgets(2)); // humanTasks and agentTasks
      expect(find.text('0%'), findsOneWidget); // collaboration score
      expect(find.text('+\$0.00 profit today'), findsOneWidget);
    });

    testWidgets('should handle large numbers correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: PartnershipSummaryCard(
              humanTasks: 999,
              agentTasks: 1234,
              sharedProfit: 9999.99,
              collaborationScore: 1.0,
            ),
          ),
        ),
      );

      expect(find.text('999'), findsOneWidget);
      expect(find.text('1234'), findsOneWidget);
      expect(find.text('+\$9999.99 profit today'), findsOneWidget);
      expect(find.text('100%'), findsOneWidget);
    });
  });
}
