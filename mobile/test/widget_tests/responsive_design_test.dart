import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/app.dart';
import 'package:flipsync/core/widgets/responsive_layout.dart';
import 'package:flipsync/features/dashboard/screens/dashboard_screen.dart';
import 'package:flipsync/features/navigation/navigation_service.dart';
import 'package:mocktail/mocktail.dart';

// Mock classes
class MockNavigationService extends Mock implements NavigationService {}

void main() {
  late MockNavigationService mockNavigationService;

  setUp(() {
    mockNavigationService = MockNavigationService();
  });

  group('Responsive Design Tests', () {
    testWidgets('App adapts to phone size', (WidgetTester tester) async {
      // Set up a phone-sized screen
      tester.binding.window.devicePixelRatioTestValue = 2.0;
      tester.binding.window.physicalSizeTestValue = const Size(750, 1334);

      // Build the app
      await tester.pumpWidget(const MyApp());
      await tester.pumpAndSettle();

      // Verify phone layout is used
      expect(find.byType(PhoneLayout), findsOneWidget);
      expect(find.byType(TabletLayout), findsNothing);

      // Verify navigation is at the bottom for phones
      expect(find.byType(BottomNavigationBar), findsOneWidget);
      expect(find.byType(NavigationRail), findsNothing);

      // Reset the test value
      addTearDown(tester.binding.window.clearPhysicalSizeTestValue);
      addTearDown(tester.binding.window.clearDevicePixelRatioTestValue);
    });

    testWidgets('App adapts to tablet size', (WidgetTester tester) async {
      // Set up a tablet-sized screen
      tester.binding.window.devicePixelRatioTestValue = 2.0;
      tester.binding.window.physicalSizeTestValue = const Size(1536, 2048);

      // Build the app
      await tester.pumpWidget(const MyApp());
      await tester.pumpAndSettle();

      // Verify tablet layout is used
      expect(find.byType(TabletLayout), findsOneWidget);
      expect(find.byType(PhoneLayout), findsNothing);

      // Verify navigation is on the side for tablets
      expect(find.byType(NavigationRail), findsOneWidget);
      expect(find.byType(BottomNavigationBar), findsNothing);

      // Reset the test value
      addTearDown(tester.binding.window.clearPhysicalSizeTestValue);
      addTearDown(tester.binding.window.clearDevicePixelRatioTestValue);
    });

    testWidgets('Dashboard adapts to different screen sizes', (WidgetTester tester) async {
      // Test with phone size
      tester.binding.window.devicePixelRatioTestValue = 2.0;
      tester.binding.window.physicalSizeTestValue = const Size(750, 1334);

      // Build the dashboard
      await tester.pumpWidget(
        const MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Verify phone layout (stacked cards)
      final phoneCardCount = find.byType(Card).evaluate().length;

      // Reset and test with tablet size
      addTearDown(tester.binding.window.clearPhysicalSizeTestValue);
      addTearDown(tester.binding.window.clearDevicePixelRatioTestValue);

      tester.binding.window.devicePixelRatioTestValue = 2.0;
      tester.binding.window.physicalSizeTestValue = const Size(1536, 2048);

      // Rebuild the dashboard
      await tester.pumpWidget(
        const MaterialApp(
          home: DashboardScreen(),
        ),
      );
      await tester.pumpAndSettle();

      // Verify tablet layout (grid of cards)
      final tabletCardCount = find.byType(Card).evaluate().length;

      // The number of cards should be the same, but the layout should be different
      expect(phoneCardCount, equals(tabletCardCount));

      // Reset the test value
      addTearDown(tester.binding.window.clearPhysicalSizeTestValue);
      addTearDown(tester.binding.window.clearDevicePixelRatioTestValue);
    });

    testWidgets('Text scales properly with different font sizes', (WidgetTester tester) async {
      // Build the app with normal text scale
      await tester.pumpWidget(
        MediaQuery(
          data: const MediaQueryData(textScaler: TextScaler.linear(1.0)),
          child: const MyApp(),
        ),
      );
      await tester.pumpAndSettle();

      // Find a text widget to measure
      final normalTextSize = tester.getSize(find.byType(Text).first);

      // Rebuild with larger text scale
      await tester.pumpWidget(
        MediaQuery(
          data: const MediaQueryData(textScaler: TextScaler.linear(1.5)),
          child: const MyApp(),
        ),
      );
      await tester.pumpAndSettle();

      // Measure the same text widget
      final largeTextSize = tester.getSize(find.byType(Text).first);

      // Verify text is larger with higher scale factor
      expect(largeTextSize.height, greaterThan(normalTextSize.height));
    });

    testWidgets('Orientation changes are handled correctly', (WidgetTester tester) async {
      // Build the app with portrait orientation
      await tester.pumpWidget(
        MediaQuery(
          data: const MediaQueryData(
            size: Size(375, 667), // iPhone portrait size
          ),
          child: const MyApp(),
        ),
      );
      await tester.pumpAndSettle();

      // Verify portrait layout exists
      expect(find.byType(Scaffold), findsOneWidget);

      // Build the app with landscape orientation
      await tester.pumpWidget(
        MediaQuery(
          data: const MediaQueryData(
            size: Size(667, 375), // iPhone landscape size
          ),
          child: const MyApp(),
        ),
      );
      await tester.pumpAndSettle();

      // Verify landscape layout exists
      expect(find.byType(Scaffold), findsOneWidget);
    });
  });
}

// Mock widgets for testing
class PhoneLayout extends StatelessWidget {
  const PhoneLayout({super.key});

  @override
  Widget build(BuildContext context) {
    return const Placeholder();
  }
}

class TabletLayout extends StatelessWidget {
  const TabletLayout({super.key});

  @override
  Widget build(BuildContext context) {
    return const Placeholder();
  }
}
