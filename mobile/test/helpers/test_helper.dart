import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';

/// Initialize test environment
Future<void> initializeTestEnvironment() async {
  TestWidgetsFlutterBinding.ensureInitialized();

  // Set up Hive for testing using a unique temporary directory
  final tempDir = await Directory.systemTemp.createTemp('flipsync_test_');
  Hive.init(tempDir.path);
}

/// Clean up test environment
Future<void> cleanupTestEnvironment() async {
  try {
    await Hive.close();
  } catch (e) {
    // Ignore cleanup errors in tests
    print('Warning: Failed to close Hive: $e');
  }
}

/// Test wrapper that handles initialization and cleanup
Future<void> testWithEnvironment(
    String description, Future<void> Function() testBody) async {
  test(description, () async {
    await initializeTestEnvironment();
    try {
      await testBody();
    } finally {
      await cleanupTestEnvironment();
    }
  });
}

/// Group wrapper that handles initialization and cleanup
void groupWithEnvironment(String description, void Function() groupBody) {
  group(description, () {
    setUpAll(() async {
      await initializeTestEnvironment();
    });

    setUp(() async {

      // Ensure we have a fresh Hive instance for each test
      await cleanupTestEnvironment();
      await initializeTestEnvironment();
    });

    tearDown(() async {
      // Clean up after each test
      await cleanupTestEnvironment();
    });

    tearDownAll(() async {
      await cleanupTestEnvironment();
    });

    groupBody();
  });
}
