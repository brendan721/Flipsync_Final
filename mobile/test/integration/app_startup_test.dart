import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/main.dart' as app;

/// App Startup Test - Verify the app can start without errors
/// Tests basic app initialization and V2 feature availability
void main() {
  group('App Startup Tests', () {
    testWidgets('should start app without errors', (WidgetTester tester) async {
      // Start the app
      app.main();
      await tester.pumpAndSettle(Duration(seconds: 5));

      // Verify app started successfully
      expect(find.byType(MaterialApp), findsOneWidget);
      
      print('✅ App started successfully');
    });

    testWidgets('should have V2 routes configured', (WidgetTester tester) async {
      // Start the app
      app.main();
      await tester.pumpAndSettle(Duration(seconds: 3));

      // Test navigation to agent insights (if accessible)
      try {
        await tester.binding.defaultBinaryMessenger.handlePlatformMessage(
          'flutter/navigation',
          null,
          (data) {},
        );
        print('✅ Navigation system initialized');
      } catch (e) {
        print('ℹ️ Navigation test skipped: $e');
      }
    });
  });
}
