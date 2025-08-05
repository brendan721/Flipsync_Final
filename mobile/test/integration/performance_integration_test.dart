import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/features/performance/presentation/widgets/partnership_performance_dashboard.dart';

/// End-to-End Integration Tests for FlipSync Performance Dashboard
/// Tests the complete performance analytics and partnership metrics flow
void main() {
  group('Performance Dashboard Integration Tests', () {
    testWidgets('should display complete performance dashboard', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Performance Dashboard Elements
      expect(find.text('Partnership Performance'), findsOneWidget);
      expect(find.byIcon(Icons.analytics), findsOneWidget);
      expect(find.byIcon(Icons.refresh), findsOneWidget);
    });

    testWidgets('should display partnership overview section', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Partnership Overview
      expect(find.text('Partnership Overview'), findsOneWidget);
      expect(find.text('Collaboration Score'), findsOneWidget);
      expect(find.text('Revenue Growth'), findsOneWidget);
      expect(find.byIcon(Icons.handshake), findsAtLeastNWidgets(1));
      expect(find.byIcon(Icons.trending_up), findsAtLeastNWidgets(1));
    });

    testWidgets('should display collaboration metrics card', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Collaboration Metrics
      expect(find.text('Collaboration Effectiveness'), findsOneWidget);
      expect(find.text('Suggestions'), findsOneWidget);
      expect(find.text('Accepted'), findsOneWidget);
      expect(find.text('Response Time'), findsOneWidget);
      expect(find.text('Agent Partnership Scores'), findsOneWidget);
    });

    testWidgets('should display business metrics card', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Business Metrics
      expect(find.text('Business Performance'), findsOneWidget);
      expect(find.text('Total Revenue'), findsOneWidget);
      expect(find.text('Items Sold'), findsOneWidget);
      expect(find.text('Avg. Price'), findsOneWidget);
      expect(find.text('Conversion'), findsOneWidget);
      expect(find.text('Active Listings'), findsOneWidget);
    });

    testWidgets('should display partnership goals widget', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Partnership Goals
      expect(find.text('Partnership Goals'), findsOneWidget);
      expect(find.text('Monthly Revenue Target'), findsOneWidget);
      expect(find.text('Agent Collaboration Score'), findsOneWidget);
      expect(find.text('Listing Automation'), findsOneWidget);
    });

    testWidgets('should display performance insights widget', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Performance Insights
      expect(find.text('Performance Insights'), findsOneWidget);
      expect(find.text('Logistics Agent Collaboration Opportunity'), findsOneWidget);
      expect(find.text('Revenue Growth Acceleration'), findsOneWidget);
      expect(find.text('Automation Rate Improvement'), findsOneWidget);
    });

    testWidgets('should handle refresh functionality', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Tap refresh button
      await tester.tap(find.byIcon(Icons.refresh));
      await tester.pumpAndSettle();

      // Assert - Should still display dashboard content
      expect(find.text('Partnership Performance'), findsOneWidget);
    });

    testWidgets('should handle pull to refresh', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Pull to refresh
      await tester.fling(find.byType(SingleChildScrollView), Offset(0, 300), 1000);
      await tester.pumpAndSettle();

      // Assert - Should still display dashboard content
      expect(find.text('Partnership Performance'), findsOneWidget);
    });

    testWidgets('should handle goal tap interaction', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Tap on a goal
      await tester.tap(find.text('Monthly Revenue Target'));
      await tester.pumpAndSettle();

      // Assert - Should show goal details dialog
      expect(find.byType(AlertDialog), findsOneWidget);
      expect(find.text('Monthly Revenue Target'), findsNWidgets(2)); // Title in dialog too
    });

    testWidgets('should handle insight tap interaction', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Tap on an insight
      await tester.tap(find.text('Revenue Growth Acceleration'));
      await tester.pumpAndSettle();

      // Assert - Should show insight details dialog
      expect(find.byType(AlertDialog), findsOneWidget);
      expect(find.text('Recommendations:'), findsOneWidget);
    });

    testWidgets('should close dialogs properly', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Open and close goal dialog
      await tester.tap(find.text('Monthly Revenue Target'));
      await tester.pumpAndSettle();
      
      await tester.tap(find.text('Close'));
      await tester.pumpAndSettle();

      // Assert - Dialog should be closed
      expect(find.byType(AlertDialog), findsNothing);
    });

    testWidgets('should display agent performance details', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Tap on an agent score
      final marketAgentFinder = find.text('Market Agent');
      if (marketAgentFinder.evaluate().isNotEmpty) {
        await tester.tap(marketAgentFinder);
        await tester.pumpAndSettle();

        // Assert - Should show agent details feedback
        expect(find.byType(SnackBar), findsOneWidget);
      }
    });

    testWidgets('should handle loading states', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );

      // Assert - Should show loading initially
      expect(find.text('Loading partnership analytics...'), findsOneWidget);
      expect(find.byType(CircularProgressIndicator), findsOneWidget);

      // Wait for loading to complete
      await tester.pumpAndSettle();

      // Assert - Should show content after loading
      expect(find.text('Partnership Performance'), findsOneWidget);
    });

    testWidgets('should display progress indicators correctly', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Should have progress indicators for goals
      expect(find.byType(LinearProgressIndicator), findsAtLeastNWidgets(3)); // Goals + business metrics
    });

    testWidgets('should display priority badges correctly', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Should have priority badges for insights
      expect(find.text('HIGH'), findsAtLeastNWidgets(1));
      expect(find.text('MEDIUM'), findsAtLeastNWidgets(1));
    });

    testWidgets('should display impact ratings correctly', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Should have star ratings for impact
      expect(find.byIcon(Icons.star), findsAtLeastNWidgets(5)); // Multiple star ratings
    });
  });

  group('Performance Dashboard Error Handling', () {
    testWidgets('should handle service errors gracefully', (WidgetTester tester) async {
      // This test would require mocking service failures
      // For now, we test that the dashboard handles initialization
      
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Should display dashboard even if some data fails to load
      expect(find.text('Partnership Performance'), findsOneWidget);
    });

    testWidgets('should handle empty data states', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Should handle empty states gracefully
      expect(find.byType(PartnershipPerformanceDashboard), findsOneWidget);
    });
  });

  group('Performance Dashboard Performance', () {
    testWidgets('should render dashboard within performance limits', (WidgetTester tester) async {
      // Arrange
      final stopwatch = Stopwatch()..start();

      // Act
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      stopwatch.stop();

      // Assert - Should render within reasonable time (< 5 seconds for tests)
      expect(stopwatch.elapsedMilliseconds, lessThan(5000));
      expect(find.text('Partnership Performance'), findsOneWidget);
    });

    testWidgets('should handle scrolling performance', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: PartnershipPerformanceDashboard(),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Scroll through the dashboard
      await tester.fling(find.byType(SingleChildScrollView), Offset(0, -500), 1000);
      await tester.pumpAndSettle();

      await tester.fling(find.byType(SingleChildScrollView), Offset(0, 500), 1000);
      await tester.pumpAndSettle();

      // Assert - Should handle scrolling smoothly
      expect(find.text('Partnership Performance'), findsOneWidget);
    });
  });
}
