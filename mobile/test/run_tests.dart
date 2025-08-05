import 'dart:io';
import 'package:args/args.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'test_config.dart'; // Import the test config

Future<void> main(List<String> arguments) async {
  final parser =
      ArgParser()
        ..addFlag('unit', help: 'Run unit tests', defaultsTo: true)
        ..addFlag('widget', help: 'Run widget tests', defaultsTo: true)
        ..addFlag(
          'integration',
          help: 'Run integration tests',
          defaultsTo: false,
        )
        ..addFlag(
          'coverage',
          help: 'Generate coverage report',
          defaultsTo: true,
        )
        ..addFlag(
          'real-backend',
          help: 'Use real backend from Docker',
          defaultsTo: false,
        )
        ..addFlag(
          'verbose',
          abbr: 'v',
          help: 'Verbose output',
          defaultsTo: false,
        );

  final args = parser.parse(arguments);

  // Configure test environment
  TestEnvironmentConfig.useRealBackend = args['real-backend'];

  // Print configuration
  if (TestEnvironmentConfig.useRealBackend) {
    print('\n🔥 TESTS WILL USE REAL BACKEND 🔥');
    print('Backend URL: ${TestEnvironmentConfig.backendBaseUrl}');
    print('Make sure your Docker backend is running!\n');
  } else {
    print('\nTests will use mock backend with predefined test data\n');
  }

  // Create test output directory if it doesn't exist, but only on non-web platforms
  if (!kIsWeb) {
    Directory('test_output').createSync(recursive: true);
  }

  int exitCode = 0;
  final stopwatch = Stopwatch()..start();

  try {
    // Run unit tests
    if (args['unit']) {
      print('\nRunning unit tests...');
      exitCode = await _runTests(
        'test/unit',
        coverage: args['coverage'],
        verbose: args['verbose'],
      );
      if (exitCode != 0) throw Exception('Unit tests failed');
    }

    // Run widget tests
    if (args['widget']) {
      print('\nRunning widget tests...');
      exitCode = await _runTests(
        'test/widget_tests',
        coverage: args['coverage'],
        verbose: args['verbose'],
      );
      if (exitCode != 0) throw Exception('Widget tests failed');
    }

    // Run integration tests
    if (args['integration']) {
      print('\nRunning integration tests...');
      exitCode = await _runTests(
        'integration_test',
        coverage: args['coverage'],
        verbose: args['verbose'],
        isIntegration: true,
      );
      if (exitCode != 0) throw Exception('Integration tests failed');
    }

    // Generate coverage report if requested
    if (args['coverage'] && !kIsWeb) {
      await _generateCoverageReport();
    }
  } catch (e) {
    print('\n❌ Error: $e');
    exitCode = 1;
  } finally {
    stopwatch.stop();
    print('\nTotal time: ${stopwatch.elapsed.inSeconds} seconds');

    // Write test summary only on non-web platforms
    if (!kIsWeb) {
      final summary = '''
Test Summary
===========
Time: ${stopwatch.elapsed.inSeconds}s
Exit Code: $exitCode
Unit Tests: ${args['unit'] ? '✓' : '-'}
Widget Tests: ${args['widget'] ? '✓' : '-'}
Integration Tests: ${args['integration'] ? '✓' : '-'}
Coverage Report: ${args['coverage'] ? '✓' : '-'}
Real Backend: ${args['real-backend'] ? '✓' : '-'}
''';

      File('test_output/test_summary.txt').writeAsStringSync(summary);
    }
  }

  exit(exitCode);
}

Future<int> _runTests(
  String directory, {
  bool coverage = false,
  bool verbose = false,
  bool isIntegration = false,
}) async {
  if (kIsWeb) {
    // For web platform, we can't use Process.run
    print('Cannot run full test suite on web platform.');
    print('Please run individual tests or use a native platform.');
    return 1;
  }

  final args = [
    'test',
    if (isIntegration) '--flavor=development',
    if (coverage) '--coverage',
    if (verbose) '-v',
    directory,
  ];

  final result = await Process.run('flutter', args);
  print(result.stdout);
  if (result.stderr.toString().isNotEmpty) {
    print(result.stderr);
  }

  return result.exitCode;
}

Future<void> _generateCoverageReport() async {
  if (kIsWeb) return; // Skip on web platform

  print('\nGenerating coverage report...');

  // Combine coverage data
  await Process.run('lcov', [
    '--add-tracefile',
    'coverage/lcov.info',
    '--output-file',
    'coverage/lcov_combined.info',
  ]);

  // Generate HTML report
  await Process.run('genhtml', [
    'coverage/lcov_combined.info',
    '--output-directory',
    'coverage/html',
  ]);

  print('Coverage report generated at coverage/html/index.html');
}
