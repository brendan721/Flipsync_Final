import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:shared_preferences/shared_preferences.dart';

/// Usability testing framework for FlipSync mobile application
///
/// This framework provides tools and utilities for conducting comprehensive
/// usability testing, including:
/// - Core user flow testing
/// - Accessibility testing
/// - Performance testing
/// - User feedback collection
class UsabilityTestFramework {
  /// Singleton instance
  static final UsabilityTestFramework _instance =
      UsabilityTestFramework._internal();
  factory UsabilityTestFramework() => _instance;
  UsabilityTestFramework._internal();

  /// Test session data
  final Map<String, dynamic> _sessionData = {};
  final List<UsabilityTestResult> _testResults = [];
  final List<PerformanceMetric> _performanceMetrics = [];
  final List<AccessibilityIssue> _accessibilityIssues = [];
  final List<UserFeedback> _userFeedback = [];

  /// Initialize the usability testing framework
  Future<void> initialize() async {
    // Clear previous test data
    _sessionData.clear();
    _testResults.clear();
    _performanceMetrics.clear();
    _accessibilityIssues.clear();
    _userFeedback.clear();

    // Initialize shared preferences for test data storage
    SharedPreferences.setMockInitialValues({});
    await SharedPreferences.getInstance();
  }

  /// Record a user flow test result
  void recordUserFlowTest(UsabilityTestResult result) {
    _testResults.add(result);
  }

  /// Record a performance metric
  void recordPerformanceMetric(PerformanceMetric metric) {
    _performanceMetrics.add(metric);
  }

  /// Record an accessibility issue
  void recordAccessibilityIssue(AccessibilityIssue issue) {
    _accessibilityIssues.add(issue);
  }

  /// Record user feedback
  void recordUserFeedback(UserFeedback feedback) {
    _userFeedback.add(feedback);
  }

  /// Get all test results
  List<UsabilityTestResult> get testResults => List.unmodifiable(_testResults);

  /// Get all performance metrics
  List<PerformanceMetric> get performanceMetrics =>
      List.unmodifiable(_performanceMetrics);

  /// Get all accessibility issues
  List<AccessibilityIssue> get accessibilityIssues =>
      List.unmodifiable(_accessibilityIssues);

  /// Get all user feedback
  List<UserFeedback> get userFeedback => List.unmodifiable(_userFeedback);

  /// Generate a comprehensive usability test report
  String generateReport() {
    final StringBuffer report = StringBuffer();

    report.writeln('# FlipSync Usability Test Report');
    report.writeln('Generated: ${DateTime.now()}');
    report.writeln('\n## User Flow Test Results');

    if (_testResults.isEmpty) {
      report.writeln('No user flow tests recorded.');
    } else {
      for (final result in _testResults) {
        report.writeln(
            '- **${result.testName}**: ${result.passed ? '✅ PASSED' : '❌ FAILED'}');
        report.writeln('  - Description: ${result.description}');
        if (!result.passed) {
          report.writeln('  - Failure reason: ${result.failureReason}');
        }
        report.writeln('  - Duration: ${result.duration.inMilliseconds}ms');
        report.writeln('');
      }
    }

    report.writeln('\n## Performance Metrics');
    if (_performanceMetrics.isEmpty) {
      report.writeln('No performance metrics recorded.');
    } else {
      for (final metric in _performanceMetrics) {
        report.writeln('- **${metric.name}**: ${metric.value} ${metric.unit}');
        report.writeln('  - Context: ${metric.context}');
        report.writeln('  - Threshold: ${metric.threshold} ${metric.unit}');
        final status = metric.value <= metric.threshold
            ? '✅ GOOD'
            : '⚠️ NEEDS IMPROVEMENT';
        report.writeln('  - Status: $status');
        report.writeln('');
      }
    }

    report.writeln('\n## Accessibility Issues');
    if (_accessibilityIssues.isEmpty) {
      report.writeln('No accessibility issues recorded.');
    } else {
      for (final issue in _accessibilityIssues) {
        report.writeln('- **${issue.title}** (${issue.severity.name})');
        report.writeln('  - Location: ${issue.location}');
        report.writeln('  - Description: ${issue.description}');
        report.writeln('  - WCAG Criteria: ${issue.wcagCriteria}');
        report.writeln('  - Recommendation: ${issue.recommendation}');
        report.writeln('');
      }
    }

    report.writeln('\n## User Feedback');
    if (_userFeedback.isEmpty) {
      report.writeln('No user feedback recorded.');
    } else {
      for (final feedback in _userFeedback) {
        report.writeln('- **User ${feedback.userId}** (${feedback.userType})');
        report.writeln('  - Screen: ${feedback.screen}');
        report.writeln('  - Rating: ${feedback.rating}/5');
        report.writeln('  - Comment: "${feedback.comment}"');
        report.writeln('  - Timestamp: ${feedback.timestamp}');
        report.writeln('');
      }
    }

    return report.toString();
  }

  /// Export test results to a file
  Future<void> exportReport(String filePath) async {
    // Implementation would depend on platform capabilities
    // For now, we'll just generate the report
    final report = generateReport();
    print('Report would be saved to: $filePath');
    print(report);
  }
}

/// Represents a usability test result
class UsabilityTestResult {
  final String testName;
  final String description;
  final bool passed;
  final String? failureReason;
  final Duration duration;
  final DateTime timestamp;

  UsabilityTestResult({
    required this.testName,
    required this.description,
    required this.passed,
    this.failureReason,
    required this.duration,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}

/// Represents a performance metric
class PerformanceMetric {
  final String name;
  final double value;
  final String unit;
  final String context;
  final double threshold;
  final DateTime timestamp;

  PerformanceMetric({
    required this.name,
    required this.value,
    required this.unit,
    required this.context,
    required this.threshold,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}

/// Severity level for accessibility issues
enum AccessibilitySeverity { critical, major, minor, suggestion }

/// Represents an accessibility issue
class AccessibilityIssue {
  final String title;
  final String description;
  final String location;
  final AccessibilitySeverity severity;
  final String wcagCriteria;
  final String recommendation;
  final DateTime timestamp;

  AccessibilityIssue({
    required this.title,
    required this.description,
    required this.location,
    required this.severity,
    required this.wcagCriteria,
    required this.recommendation,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}

/// Represents user feedback
class UserFeedback {
  final String userId;
  final String userType;
  final String screen;
  final int rating;
  final String comment;
  final DateTime timestamp;

  UserFeedback({
    required this.userId,
    required this.userType,
    required this.screen,
    required this.rating,
    required this.comment,
    DateTime? timestamp,
  }) : timestamp = timestamp ?? DateTime.now();
}
