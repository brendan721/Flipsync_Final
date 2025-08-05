import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:flipsync/core/widgets/responsive_layout.dart';

import '../test_setup.dart';

void main() {
  setUp(() {
    // Setup GetIt dependencies before each test
    setupTestDependencies();
  });

  tearDown(() {
    // Clean up GetIt after each test
    GetIt.instance.reset();
  });

  group('Responsive Design Tests', () {
    testWidgets('ResponsiveLayout adapts to phone size', (WidgetTester tester) async {
      // Set up a phone-sized screen
      await tester.binding.setSurfaceSize(const Size(375, 667));

      // Build a simple responsive layout
      await tester.pumpWidget(
        MaterialApp(
          home: ResponsiveLayout(
            mobile: Container(key: const Key('mobile')),
            tablet: Container(key: const Key('tablet')),
            desktop: Container(key: const Key('desktop')),
          ),
        ),
      );

      // Verify mobile layout is used
      expect(find.byKey(const Key('mobile')), findsOneWidget);
      expect(find.byKey(const Key('tablet')), findsNothing);
      expect(find.byKey(const Key('desktop')), findsNothing);
    });

    testWidgets('ResponsiveLayout adapts to tablet size', (WidgetTester tester) async {
      // Set up a tablet-sized screen
      await tester.binding.setSurfaceSize(const Size(800, 1024));

      // Build a simple responsive layout
      await tester.pumpWidget(
        MaterialApp(
          home: ResponsiveLayout(
            mobile: Container(key: const Key('mobile')),
            tablet: Container(key: const Key('tablet')),
            desktop: Container(key: const Key('desktop')),
          ),
        ),
      );

      // Verify tablet layout is used
      expect(find.byKey(const Key('tablet')), findsOneWidget);
      expect(find.byKey(const Key('mobile')), findsNothing);
      expect(find.byKey(const Key('desktop')), findsNothing);
    });

    testWidgets('ResponsiveLayout adapts to desktop size', (WidgetTester tester) async {
      // Set up a desktop-sized screen
      await tester.binding.setSurfaceSize(const Size(1400, 900));

      // Build a simple responsive layout
      await tester.pumpWidget(
        MaterialApp(
          home: ResponsiveLayout(
            mobile: Container(key: const Key('mobile')),
            tablet: Container(key: const Key('tablet')),
            desktop: Container(key: const Key('desktop')),
          ),
        ),
      );

      // Verify desktop layout is used
      expect(find.byKey(const Key('desktop')), findsOneWidget);
      expect(find.byKey(const Key('mobile')), findsNothing);
      expect(find.byKey(const Key('tablet')), findsNothing);
    });

    testWidgets('ResponsiveLayout handles null tablet/desktop gracefully', (WidgetTester tester) async {
      // Set up a tablet-sized screen but only provide mobile layout
      await tester.binding.setSurfaceSize(const Size(800, 1024));

      // Build responsive layout with only mobile widget
      await tester.pumpWidget(
        MaterialApp(
          home: ResponsiveLayout(
            mobile: Container(key: const Key('mobile')),
            // tablet and desktop are null
          ),
        ),
      );

      // Verify mobile layout is used as fallback
      expect(find.byKey(const Key('mobile')), findsOneWidget);
    });

    testWidgets('ResponsiveLayout uses correct breakpoints', (WidgetTester tester) async {
      // Test breakpoint at 600px (mobile/tablet boundary)
      await tester.binding.setSurfaceSize(const Size(599, 800));

      await tester.pumpWidget(
        MaterialApp(
          home: ResponsiveLayout(
            mobile: Container(key: const Key('mobile')),
            tablet: Container(key: const Key('tablet')),
          ),
        ),
      );

      // Should use mobile layout
      expect(find.byKey(const Key('mobile')), findsOneWidget);
      expect(find.byKey(const Key('tablet')), findsNothing);

      // Test at 600px exactly (should use tablet)
      await tester.binding.setSurfaceSize(const Size(600, 800));
      await tester.pumpWidget(
        MaterialApp(
          home: ResponsiveLayout(
            mobile: Container(key: const Key('mobile')),
            tablet: Container(key: const Key('tablet')),
          ),
        ),
      );

      // Should use tablet layout
      expect(find.byKey(const Key('tablet')), findsOneWidget);
      expect(find.byKey(const Key('mobile')), findsNothing);
    });
  });
}
