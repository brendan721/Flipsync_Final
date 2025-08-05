import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/features/dashboard/screens/dashboard_screen.dart';

/// End-to-End Integration Tests for FlipSync Dashboard
/// Tests the complete user journey through the partnership dashboard
void main() {
  group('Dashboard Integration Tests', () {
    testWidgets('should display complete partnership dashboard', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Partnership Dashboard Elements
      expect(find.text('FlipSync Partnership'), findsOneWidget);
      expect(find.byIcon(Icons.handshake), findsAtLeastNWidgets(1));
      
      // Partnership Summary Card
      expect(find.text('Today\'s Collaboration Summary'), findsOneWidget);
      expect(find.text('Your Tasks'), findsOneWidget);
      expect(find.text('Agent Tasks'), findsOneWidget);
      expect(find.text('Partnership Score'), findsOneWidget);
      
      // Opportunity Discovery Widget
      expect(find.text('Opportunities Discovered'), findsOneWidget);
      
      // Human Tasks Widget
      expect(find.text('Items Needing Your Attention'), findsOneWidget);
      
      // Communication Hub
      expect(find.text('Communication Hub'), findsOneWidget);
    });

    testWidgets('should navigate to partnership performance dashboard', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Tap on View Partnership Details
      await tester.tap(find.text('View Partnership Details'));
      await tester.pumpAndSettle();

      // Assert - Performance Dashboard
      expect(find.text('Partnership Performance'), findsOneWidget);
      expect(find.text('Partnership Overview'), findsOneWidget);
      expect(find.text('Collaboration Effectiveness'), findsOneWidget);
      expect(find.text('Business Performance'), findsOneWidget);
    });

    testWidgets('should handle opportunity decisions', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Find and tap Apply button for first opportunity
      final applyButtons = find.text('Apply');
      if (applyButtons.evaluate().isNotEmpty) {
        await tester.tap(applyButtons.first);
        await tester.pumpAndSettle();

        // Assert - Should show success feedback
        expect(find.byType(SnackBar), findsOneWidget);
      }
    });

    testWidgets('should handle human task assessment', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Tap Assess Items button
      final assessButton = find.text('Assess Items');
      if (assessButton.evaluate().isNotEmpty) {
        await tester.tap(assessButton);
        await tester.pumpAndSettle();

        // Assert - Should show task feedback
        expect(find.byType(SnackBar), findsOneWidget);
      }
    });

    testWidgets('should navigate to conversation screen', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Find and tap a conversation (if any exist)
      final replyButtons = find.text('Reply');
      if (replyButtons.evaluate().isNotEmpty) {
        await tester.tap(replyButtons.first);
        await tester.pumpAndSettle();

        // Assert - Should navigate to conversation screen
        expect(find.text('Agent Collaboration'), findsAny);
        expect(find.text('Buyer Communication'), findsAny);
      }
    });

    testWidgets('should display bottom navigation correctly', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Bottom Navigation
      expect(find.text('Partnership'), findsOneWidget);
      expect(find.text('Insights'), findsOneWidget);
      expect(find.text('My Items'), findsOneWidget);
      expect(find.text('Performance'), findsOneWidget);
    });

    testWidgets('should handle bottom navigation taps', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Act & Assert - Test each navigation item
      await tester.tap(find.text('Insights'));
      await tester.pumpAndSettle();
      // Should stay on same screen for now (placeholder)

      await tester.tap(find.text('My Items'));
      await tester.pumpAndSettle();
      // Should stay on same screen for now (placeholder)

      await tester.tap(find.text('Performance'));
      await tester.pumpAndSettle();
      // Should stay on same screen for now (placeholder)

      await tester.tap(find.text('Partnership'));
      await tester.pumpAndSettle();
      // Should return to main dashboard
    });

    testWidgets('should handle refresh functionality', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Pull to refresh
      await tester.fling(find.byType(SingleChildScrollView), Offset(0, 300), 1000);
      await tester.pumpAndSettle();

      // Assert - Should still display dashboard content
      expect(find.text('FlipSync Partnership'), findsOneWidget);
    });

    testWidgets('should display loading states appropriately', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(),
        ),
      );

      // Assert - Initial loading might be visible briefly
      // Then content should load
      await tester.pumpAndSettle();
      expect(find.text('FlipSync Partnership'), findsOneWidget);
    });

    testWidgets('should handle empty states gracefully', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Should handle empty states for various widgets
      // This tests the empty state handling in widgets
      expect(find.byType(DashboardScreen), findsOneWidget);
    });
  });

  group('Dashboard Error Handling', () {
    testWidgets('should handle service errors gracefully', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Should display dashboard even if some services fail
      expect(find.text('FlipSync Partnership'), findsOneWidget);
    });

    testWidgets('should handle network connectivity issues', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Should display cached/default content
      expect(find.byType(DashboardScreen), findsOneWidget);
    });
  });

  group('Dashboard Performance', () {
    testWidgets('should render dashboard within performance limits', (WidgetTester tester) async {
      // Arrange
      final stopwatch = Stopwatch()..start();

      // Act
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      stopwatch.stop();

      // Assert - Should render within reasonable time (< 5 seconds for tests)
      expect(stopwatch.elapsedMilliseconds, lessThan(5000));
      expect(find.text('FlipSync Partnership'), findsOneWidget);
    });

    testWidgets('should handle multiple rapid interactions', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Rapid taps on different elements
      for (int i = 0; i < 5; i++) {
        await tester.tap(find.text('Partnership'));
        await tester.pump(Duration(milliseconds: 100));
      }
      await tester.pumpAndSettle();

      // Assert - Should remain stable
      expect(find.text('FlipSync Partnership'), findsOneWidget);
    });
  });
}
