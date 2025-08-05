// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';

import 'package:flipsync/app.dart';
import 'package:flipsync/features/navigation/navigation_service.dart';
import 'test_setup.dart';

void main() {
  setUp(() {
    // Setup GetIt dependencies before each test
    setupTestDependencies();
  });

  tearDown(() {
    // Clean up GetIt after each test
    GetIt.instance.reset();
  });

  testWidgets('FlipSync app smoke test', (tester) async {
    // Verify dependencies are registered
    expect(GetIt.instance.isRegistered<NavigationService>(), isTrue);

    // Build our app and trigger a frame.
    await tester.pumpWidget(const App());

    // Verify that the app loads without crashing
    expect(find.byType(MaterialApp), findsOneWidget);
  });
}
