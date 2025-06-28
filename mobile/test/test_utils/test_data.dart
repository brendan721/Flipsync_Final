import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

/// Test data constants for FlipSync tests
/// Contains test data values, max durations, and expected metrics
class TestData {
  // Authentication test data
  static const String userEmail = 'test@example.com';
  static const String validPassword = 'Password123!';
  static const String invalidPassword = 'wrong';

  // Market trend test data
  static const String expectedTooltipValue = '23.5% increase';

  // Competitor analysis test data
  static const String expectedCompetitorMetric = '78% better than average';

  // Performance metrics test data
  static const String expectedRevenueValue = '42,500';
  static const String expectedConversionRate = '5.3%';
  static const String expectedROI = '237%';

  // Realtime update test data
  static const String realtimeUpdateValue = '237 active users';

  // Custom analysis test data
  static const String expectedCustomAnalysisResult = 'Efficiency: 86%';

  // Performance test maximum thresholds
  static const double maxColdStartDuration = 2000.0; // ms
  static const double maxWarmStartDuration = 800.0; // ms
  static const double maxFrameTime = 16.7; // ms (60fps)
  static const double maxMemoryIncrease = 50.0; // MB
  static const double maxApiResponseTime = 500.0; // ms
  static const double maxBandwidthUsage = 5.0; // MB
  static const double maxDbWriteTime = 100.0; // ms
  static const double maxDbReadTime = 50.0; // ms
  static const double maxBulkOpTime = 5000.0; // ms
  static const double maxBackgroundBatteryDrain = 0.01; // % per minute
  static const double maxActiveBatteryDrain = 0.05; // % per minute
  static const double maxCleanupTime = 500.0; // ms
  static const double maxInitTime = 1500.0; // ms
  static const double maxDependencyLoadTime = 1000.0; // ms

  // UI test thresholds
  static const double maxTapResponseTime = 100.0; // ms
  static const double maxScrollResponseTime = 150.0; // ms
  static const double maxTransitionDuration = 500.0; // ms
  static const double maxFirstPaintTime = 300.0; // ms
  static const double maxTimeToInteractive = 1000.0; // ms
  static const double maxLayoutTime = 200.0; // ms
  static const int maxRebuildCount = 3;
  static const double maxStateUpdateTime = 100.0; // ms
  static const double maxActionLatency = 50.0; // ms
  static const double maxErrorRecoveryTime = 300.0; // ms
  static const double maxReconnectionTime = 1000.0; // ms
  static const double maxEndpointLatency = 300.0; // ms
  static const double maxCpuUsage = 30.0; // %
  static const double maxMemoryUsage = 200.0; // MB
  static const double maxGcPauseTime = 100.0; // ms

  // Device-specific max render times (in ms)
  static const Map<String, double> maxRenderTimePerDevice = {
    'small': 600.0,
    'medium': 800.0,
    'large': 1000.0,
  };

  // Feature test data
  static const Map<String, dynamic> testUserData = {
    'email': userEmail,
    'displayName': 'Test User',
    'preferences': {'theme': 'dark', 'notifications': true},
  };

  static const Map<String, dynamic> testListingData = {
    'title': 'Test Product',
    'description': 'This is a test product listing',
    'price': 99.99,
    'quantity': 10,
    'condition': 'New',
  };

  static const List<String> testCategories = [
    'Electronics',
    'Home & Garden',
    'Fashion',
    'Sports',
    'Collectibles',
  ];

  static const List<String> testConditions = [
    'New',
    'Like New',
    'Very Good',
    'Good',
    'Acceptable',
  ];

  // Mock API response data
  static const Map<String, dynamic> mockAuthResponse = {
    'token': 'mock_auth_token_for_testing',
    'user': {
      'id': 'test_user_123',
      'email': userEmail,
      'displayName': 'Test User',
      'createdAt': '2023-01-01T00:00:00Z',
    },
  };

  static const List<Map<String, dynamic>> mockListingsResponse = [
    {
      'id': 'listing1',
      'title': 'iPhone Test',
      'description': 'Test iPhone listing',
      'price': 499.99,
      'images': ['image1.jpg', 'image2.jpg'],
      'condition': 'Like New',
    },
    {
      'id': 'listing2',
      'title': 'MacBook Test',
      'description': 'Test MacBook listing',
      'price': 1299.99,
      'images': ['image3.jpg', 'image4.jpg'],
      'condition': 'Very Good',
    },
  ];

  static const Map<String, dynamic> mockUserStatsResponse = {
    'listingsCount': 12,
    'viewsCount': 234,
    'salesCount': 8,
    'averageRating': 4.7,
  };

  // Test file paths
  static const String testImagePath = 'assets/test/test_image.jpg';
  static const String testDocumentPath = 'assets/test/test_document.pdf';

  // Test durations
  static const Duration shortDelay = Duration(milliseconds: 300);
  static const Duration mediumDelay = Duration(seconds: 1);
  static const Duration longDelay = Duration(seconds: 3);

  // Navigation paths
  static const String homePath = '/home';
  static const String listingDetailPath = '/listing/:id';
  static const String profilePath = '/profile';
  static const String settingsPath = '/settings';
  static const String analyticsPath = '/analytics';

  // Test dimensions
  static const Size smallPhone = Size(320, 480);
  static const Size mediumPhone = Size(375, 667);
  static const Size largePhone = Size(414, 896);
  static const Size tablet = Size(768, 1024);

  // Theme test colors
  static const Color primaryColor = Color(0xFF2196F3);
  static const Color secondaryColor = Color(0xFFFFC107);
  static const Color errorColor = Color(0xFFE57373);
  static const Color surfaceColor = Colors.white;
  static const Color backgroundColor = Color(0xFFF5F5F5);

  // Accessibility test sizes
  static const double minTouchTarget = 48.0;
  static const double minFontSize = 12.0;
  static const double preferredFontSize = 16.0;

  // Error test messages
  static const String connectionErrorMessage = 'No internet connection';
  static const String authErrorMessage = 'Authentication failed';
  static const String dataLoadErrorMessage = 'Failed to load data';
  static const String serverErrorMessage = 'Server error occurred';

  // Analytics test events
  static const String viewListingEvent = 'view_listing';
  static const String createListingEvent = 'create_listing';
  static const String searchEvent = 'search';
  static const String contactSellerEvent = 'contact_seller';

  // Performance test sample sizes
  static const int smallDatasetSize = 10;
  static const int mediumDatasetSize = 100;
  static const int largeDatasetSize = 1000;
}

// Add a main function to prevent the test runner from failing
// This file is intended as a test data helper, not as a test file itself
void main() {
  group('TestData', () {
    test('This file contains only test data utilities, not tests', () {
      expect(true, isTrue);
    });
  });
}
