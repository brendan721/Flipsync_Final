import 'package:flutter_test/flutter_test.dart';

import 'core_user_flow_tests.dart';
import 'accessibility_tests.dart';
import 'performance_tests.dart';
import 'user_feedback_collection.dart';
import 'usability_test_framework.dart';

/// Main runner for all usability tests
///
/// This class orchestrates the execution of all usability tests and
/// generates a comprehensive report of the results.
class UsabilityTestRunner {
  final CoreUserFlowTests _userFlowTests = CoreUserFlowTests();
  final AccessibilityTests _accessibilityTests = AccessibilityTests();
  final PerformanceTests _performanceTests = PerformanceTests();
  final UserFeedbackCollection _feedbackCollection = UserFeedbackCollection();
  final UsabilityTestFramework _framework = UsabilityTestFramework();

  /// Run all usability tests
  Future<void> runAllTests(WidgetTester tester) async {
    print('Starting FlipSync Usability Testing Suite...');

    await _framework.initialize();

    print('\n=== Core User Flow Tests ===');
    await _userFlowTests.runAllTests(tester);

    print('\n=== Accessibility Tests ===');
    await _accessibilityTests.runAllTests(tester);

    print('\n=== Performance Tests ===');
    await _performanceTests.runAllTests(tester);

    print('\n=== User Feedback Collection ===');
    await _feedbackCollection.initialize();
    _feedbackCollection.populateSampleData();
    print(_feedbackCollection.generateFeedbackReport());

    print('\n=== Generating Comprehensive Report ===');
    final report = _framework.generateReport();
    print(report);

    print('\nUsability Testing Suite Completed.');
  }
}

/// Main entry point for running usability tests
void main() {
  final runner = UsabilityTestRunner();

  testWidgets('Run all usability tests', (WidgetTester tester) async {
    await runner.runAllTests(tester);
  });
}
