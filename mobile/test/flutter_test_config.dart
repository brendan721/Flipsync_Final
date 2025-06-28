import 'dart:async';
import 'package:flutter_test/flutter_test.dart';

Future<void> testExecutable(FutureOr<void> Function() testMain) async {
  // Setup before all tests
  setUpAll(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    // Additional setup code here
  });

  // Run the tests
  await testMain();

  // Cleanup after tests if needed
  tearDownAll(() async {
    // Cleanup code here
  });
}
