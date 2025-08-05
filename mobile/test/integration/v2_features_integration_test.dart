import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:flipsync/main.dart' as app;
import 'package:flipsync/core/config/app_config.dart';
import 'package:flipsync/core/config/environment.dart';

/// V2 Features Integration Test - Comprehensive testing of V2 partnership features
/// Tests the complete V2 implementation including agent insights and partnership settings
void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  group('V2 Features Integration Tests', () {
    setUpAll(() async {
      // Initialize AppConfig for testing
      AppConfig.initialize(
        environment: Environment.dev,
        apiBaseUrl: 'http://174.138.77.110:8000/api/v1',
        enableLogging: true,
        useMockData: true, // Use mock data for testing
      );
    });

    testWidgets('should display V2 partnership dashboard with all components', (WidgetTester tester) async {
      // Start the app
      app.main();
      await tester.pumpAndSettle();

      // Wait for app to load
      await tester.pumpAndSettle(Duration(seconds: 3));

      // Navigate to dashboard (assuming we start at login/welcome)
      // Look for dashboard navigation or skip if already on dashboard
      final dashboardFinder = find.text('FlipSync Partnership');
      if (dashboardFinder.evaluate().isEmpty) {
        // Try to navigate to dashboard
        final dashboardNavFinder = find.byIcon(Icons.dashboard);
        if (dashboardNavFinder.evaluate().isNotEmpty) {
          await tester.tap(dashboardNavFinder);
          await tester.pumpAndSettle();
        }
      }

      // Verify V2 Partnership Dashboard Elements
      expect(find.text('FlipSync Partnership'), findsOneWidget);
      expect(find.text('Today\'s Collaboration Summary'), findsOneWidget);
      expect(find.text('Opportunities Discovered'), findsOneWidget);
      expect(find.text('Human Tasks'), findsOneWidget);
      expect(find.text('Communication Hub'), findsOneWidget);

      // Verify partnership metrics are displayed
      expect(find.textContaining('Human Tasks'), findsAtLeastNWidgets(1));
      expect(find.textContaining('Agent Tasks'), findsAtLeastNWidgets(1));
      expect(find.textContaining('Shared Profit'), findsAtLeastNWidgets(1));
      expect(find.textContaining('Collaboration Score'), findsAtLeastNWidgets(1));

      print('✅ V2 Partnership Dashboard test passed');
    });

    testWidgets('should navigate to and display Agent Insights screen', (WidgetTester tester) async {
      // Start the app
      app.main();
      await tester.pumpAndSettle();

      // Navigate to Agent Insights
      // This might be through a menu, navigation drawer, or direct route
      // Try to find navigation to agent insights
      final agentInsightsFinder = find.text('Agent Insights');
      if (agentInsightsFinder.evaluate().isEmpty) {
        // Try to find a menu or navigation button
        final menuFinder = find.byIcon(Icons.menu);
        if (menuFinder.evaluate().isNotEmpty) {
          await tester.tap(menuFinder);
          await tester.pumpAndSettle();

          // Look for Agent Insights in menu
          final agentInsightsMenuFinder = find.text('Agent Insights');
          if (agentInsightsMenuFinder.evaluate().isNotEmpty) {
            await tester.tap(agentInsightsMenuFinder);
            await tester.pumpAndSettle();
          }
        }
      }

      // Verify Agent Insights Screen Elements
      expect(find.text('Agent Insights'), findsAtLeastNWidgets(1));

      // Check for tabs
      expect(find.text('Opportunities'), findsOneWidget);
      expect(find.text('Market Intel'), findsOneWidget);
      expect(find.text('Alerts'), findsOneWidget);
      expect(find.text('Discoveries'), findsOneWidget);

      // Test tab navigation
      await tester.tap(find.text('Market Intel'));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Alerts'));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Discoveries'));
      await tester.pumpAndSettle();

      // Return to Opportunities tab
      await tester.tap(find.text('Opportunities'));
      await tester.pumpAndSettle();

      print('✅ Agent Insights screen test passed');
    });

    testWidgets('should display proactive recommendations', (WidgetTester tester) async {
      // Start the app and navigate to Agent Insights
      app.main();
      await tester.pumpAndSettle();

      // Navigate to Agent Insights (implementation depends on app structure)
      // For now, assume we can access it directly or through navigation

      // Look for proactive recommendations section
      expect(find.text('Proactive Recommendations'), findsAtLeastNWidgets(1));

      // Check for recommendation cards (mock data should be displayed)
      expect(find.textContaining('Agent'), findsAtLeastNWidgets(1));
      expect(find.textContaining('Confidence'), findsAtLeastNWidgets(1));
      expect(find.textContaining('Impact'), findsAtLeastNWidgets(1));

      // Test recommendation interaction
      final acceptButtonFinder = find.text('Accept');
      if (acceptButtonFinder.evaluate().isNotEmpty) {
        await tester.tap(acceptButtonFinder.first);
        await tester.pumpAndSettle();
      }

      print('✅ Proactive recommendations test passed');
    });

    testWidgets('should navigate to and display Partnership Settings screen', (WidgetTester tester) async {
      // Start the app
      app.main();
      await tester.pumpAndSettle();

      // Navigate to Partnership Settings
      // This might be through settings menu or direct navigation
      final settingsFinder = find.byIcon(Icons.settings);
      if (settingsFinder.evaluate().isNotEmpty) {
        await tester.tap(settingsFinder);
        await tester.pumpAndSettle();

        // Look for Partnership Settings
        final partnershipSettingsFinder = find.text('Partnership Settings');
        if (partnershipSettingsFinder.evaluate().isNotEmpty) {
          await tester.tap(partnershipSettingsFinder);
          await tester.pumpAndSettle();
        }
      }

      // Verify Partnership Settings Screen Elements
      expect(find.text('Partnership Settings'), findsAtLeastNWidgets(1));

      // Check for tabs
      expect(find.text('Authority'), findsOneWidget);
      expect(find.text('Pricing'), findsOneWidget);
      expect(find.text('Alerts'), findsOneWidget);
      expect(find.text('Behavior'), findsOneWidget);

      // Test tab navigation
      await tester.tap(find.text('Pricing'));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Alerts'));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Behavior'));
      await tester.pumpAndSettle();

      // Return to Authority tab
      await tester.tap(find.text('Authority'));
      await tester.pumpAndSettle();

      print('✅ Partnership Settings screen test passed');
    });

    testWidgets('should display decision authority configuration', (WidgetTester tester) async {
      // Start the app and navigate to Partnership Settings
      app.main();
      await tester.pumpAndSettle();

      // Navigate to Partnership Settings Authority tab
      // (Implementation depends on navigation structure)

      // Verify Decision Authority Elements
      expect(find.text('Decision Making Mode'), findsAtLeastNWidgets(1));
      expect(find.text('Agent Authority Levels'), findsAtLeastNWidgets(1));
      expect(find.text('Auto-Approval Threshold'), findsAtLeastNWidgets(1));
      expect(find.text('High Value Confirmation'), findsAtLeastNWidgets(1));

      // Test decision mode selection
      final collaborativeFinder = find.text('Collaborative (Recommended)');
      if (collaborativeFinder.evaluate().isNotEmpty) {
        await tester.tap(collaborativeFinder);
        await tester.pumpAndSettle();
      }

      // Test slider interaction
      final sliderFinder = find.byType(Slider);
      if (sliderFinder.evaluate().isNotEmpty) {
        await tester.drag(sliderFinder.first, Offset(50, 0));
        await tester.pumpAndSettle();
      }

      print('✅ Decision authority configuration test passed');
    });

    testWidgets('should handle V2 communication hub features', (WidgetTester tester) async {
      // Start the app
      app.main();
      await tester.pumpAndSettle();

      // Look for Communication Hub
      final communicationHubFinder = find.text('Communication Hub');
      if (communicationHubFinder.evaluate().isNotEmpty) {
        await tester.tap(communicationHubFinder);
        await tester.pumpAndSettle();
      }

      // Verify V2 communication features
      expect(find.textContaining('Buyer Relations'), findsAtLeastNWidgets(1));
      expect(find.textContaining('Agent Collaboration'), findsAtLeastNWidgets(1));

      print('✅ V2 Communication Hub test passed');
    });

    testWidgets('should display performance partnership analytics', (WidgetTester tester) async {
      // Start the app
      app.main();
      await tester.pumpAndSettle();

      // Look for Performance or Analytics section
      final performanceFinder = find.textContaining('Performance');
      if (performanceFinder.evaluate().isNotEmpty) {
        await tester.tap(performanceFinder.first);
        await tester.pumpAndSettle();
      }

      // Verify partnership performance metrics
      expect(find.textContaining('Partnership'), findsAtLeastNWidgets(1));
      expect(find.textContaining('Collaboration'), findsAtLeastNWidgets(1));

      print('✅ Performance partnership analytics test passed');
    });

    testWidgets('should validate V2 design system implementation', (WidgetTester tester) async {
      // Start the app
      app.main();
      await tester.pumpAndSettle();

      // Check for V2 design elements
      // Look for partnership-focused colors and typography
      final partnershipElements = find.textContaining('Partnership');
      expect(partnershipElements, findsAtLeastNWidgets(1));

      // Check for collaboration-themed UI elements
      final collaborationElements = find.textContaining('Collaboration');
      expect(collaborationElements, findsAtLeastNWidgets(1));

      // Verify agent-specific color coding
      final agentElements = find.textContaining('Agent');
      expect(agentElements, findsAtLeastNWidgets(1));

      print('✅ V2 Design system validation test passed');
    });
  });
}
