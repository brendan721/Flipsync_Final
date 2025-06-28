class TestData {
  // Authentication
  static const String validEmail = 'test@example.com';
  static const String validPassword = 'Test123!@#';
  static const String invalidEmail = 'invalid@example';
  static const String invalidPassword = '123';

  // Listings
  static const String listingTitle = 'Test Product';
  static const String listingDescription = 'A test product description';
  static const String listingPrice = '99.99';
  static const String listingQuantity = '10';
  static const String updatedListingTitle = 'Updated Test Product';
  static const String offlineUpdateTitle = 'Offline Update';
  static const String minPrice = '50';
  static const String maxPrice = '150';
  static const String searchQuery = 'test';
  static const String searchResultTitle = 'Test Search Result';

  // Analytics
  static const String expectedTooltipValue = '150.00';
  static const String expectedCompetitorMetric = '85%';
  static const String expectedRevenueValue = '\$10,000';
  static const String expectedConversionRate = '2.5%';
  static const String expectedROI = '150%';
  static const String realtimeUpdateValue = '160.00';
  static const String expectedCustomAnalysisResult = '75.5';

  // Performance Thresholds
  static const Duration maxColdStartDuration = Duration(seconds: 2);
  static const Duration maxWarmStartDuration = Duration(milliseconds: 800);
  static const double maxFrameTime = 16.0; // ms
  static const int maxMemoryIncrease = 50000000; // 50MB
  static const double maxApiResponseTime = 300.0; // ms
  static const int maxBandwidthUsage = 2000000; // 2MB
  static const double maxDbWriteTime = 10.0; // ms
  static const double maxDbReadTime = 5.0; // ms
  static const double maxBulkOpTime = 2000.0; // ms
  static const double maxBackgroundBatteryDrain = 0.2; // % per hour
  static const double maxActiveBatteryDrain = 1.0; // % per hour
  static const double maxCleanupTime = 200.0; // ms
  static const double maxInitTime = 1000.0; // ms
  static const double maxDependencyLoadTime = 500.0; // ms

  // Security
  static const String testEncryptionKey = 'test_key_12345';
  static const String testInitVector = 'test_iv_12345';
  static const Duration sessionTimeout = Duration(minutes: 30);
  static const int maxLoginAttempts = 5;
  static const Duration lockoutDuration = Duration(minutes: 15);

  // UI Response Thresholds
  static const Duration maxTapResponseTime = Duration(milliseconds: 100);
  static const Duration maxScrollResponseTime = Duration(milliseconds: 16);
  static const Duration maxTransitionDuration = Duration(milliseconds: 300);
  static const double minFps = 58.0;

  // Render Performance Thresholds
  static const Duration maxFirstPaintTime = Duration(milliseconds: 500);
  static const Duration maxTimeToInteractive = Duration(seconds: 1);
  static const Duration maxLayoutTime = Duration(milliseconds: 16);
  static const int maxRebuildCount = 3;
  static const Duration maxRenderTime = Duration(milliseconds: 16);

  // State Management Thresholds
  static const Duration maxStateUpdateTime = Duration(milliseconds: 16);
  static const Duration maxActionLatency = Duration(milliseconds: 100);
  static const int maxStateChanges = 5;

  // Error Handling Thresholds
  static const Duration maxErrorRecoveryTime = Duration(seconds: 1);
  static const double minErrorRecoveryRate = 0.99;
  static const int maxErrorRetries = 3;

  // Network Reliability Thresholds
  static const double minConnectionStability = 0.99;
  static const Duration maxReconnectionTime = Duration(seconds: 2);
  static const Duration maxEndpointLatency = Duration(milliseconds: 300);
  static const int maxDropoutCount = 1;

  // Resource Usage Thresholds
  static const double maxCpuUsage = 0.8; // 80%
  static const double maxMemoryUsage = 0.7; // 70%
  static const double maxDiskUsage = 0.5; // 50%
  static const double maxNetworkUsage = 0.6; // 60%
  static const Duration maxGcPauseTime = Duration(milliseconds: 50);

  // Cross-Device Thresholds
  static const Map<String, double> maxRenderTimePerDevice = {
    'iPhone 13': 16.0,
    'Pixel 6': 16.0,
    'Samsung S21': 16.0,
    'iPad Pro': 20.0,
    'Tablet': 20.0,
  };

  // Accessibility Thresholds
  static const double minContrastRatio = 4.5;
  static const double minTouchTargetSize = 44.0; // pixels
  static const Duration maxScreenReaderDelay = Duration(milliseconds: 100);

  // Test Device Configurations
  static const List<Map<String, dynamic>> testDevices = [
    {
      'name': 'iPhone 13',
      'resolution': '1170x2532',
      'dpr': 3.0,
      'platform': 'iOS',
    },
    {
      'name': 'Pixel 6',
      'resolution': '1080x2400',
      'dpr': 2.75,
      'platform': 'Android',
    },
    {
      'name': 'Samsung S21',
      'resolution': '1440x3200',
      'dpr': 3.0,
      'platform': 'Android',
    },
    {
      'name': 'iPad Pro',
      'resolution': '2048x2732',
      'dpr': 2.0,
      'platform': 'iOS',
    },
  ];

  // UI Test Scenarios
  static const List<Map<String, dynamic>> uiTestScenarios = [
    {
      'name': 'Login Flow',
      'steps': [
        'Enter Email',
        'Enter Password',
        'Submit Form',
        'Verify Dashboard',
      ],
      'expectedDuration': Duration(seconds: 2),
    },
    {
      'name': 'Listing Creation',
      'steps': [
        'Open Create Form',
        'Fill Details',
        'Upload Images',
        'Submit Listing',
      ],
      'expectedDuration': Duration(seconds: 3),
    },
    {
      'name': 'Analytics Dashboard',
      'steps': [
        'Load Dashboard',
        'Switch Time Ranges',
        'Filter Data',
        'Export Report',
      ],
      'expectedDuration': Duration(seconds: 2),
    },
  ];

  // Error Scenarios
  static const List<Map<String, dynamic>> errorScenarios = [
    {
      'type': 'Network Error',
      'action': 'API Request',
      'expectedMessage': 'Connection failed. Please try again.',
      'recoverySteps': ['Retry', 'Check Connection', 'Clear Cache'],
    },
    {
      'type': 'Validation Error',
      'action': 'Form Submit',
      'expectedMessage': 'Please check your input.',
      'recoverySteps': ['Show Error', 'Highlight Fields', 'Clear Form'],
    },
    {
      'type': 'State Error',
      'action': 'Data Update',
      'expectedMessage': 'Unable to update. Please refresh.',
      'recoverySteps': ['Reload Data', 'Reset State', 'Log Error'],
    },
  ];

  // Test Data Sets
  static const List<Map<String, dynamic>> testListings = [
    {
      'id': '1',
      'title': 'Product 1',
      'price': 99.99,
      'quantity': 10,
    },
    {
      'id': '2',
      'title': 'Product 2',
      'price': 149.99,
      'quantity': 5,
    },
    {
      'id': '3',
      'title': 'Product 3',
      'price': 49.99,
      'quantity': 20,
    },
  ];

  static const List<Map<String, dynamic>> testMarketData = [
    {
      'date': '2024-01-01',
      'value': 100.0,
      'volume': 1000,
    },
    {
      'date': '2024-01-02',
      'value': 105.0,
      'volume': 1200,
    },
    {
      'date': '2024-01-03',
      'value': 103.0,
      'volume': 900,
    },
  ];

  static const List<Map<String, dynamic>> testCompetitors = [
    {
      'name': 'Competitor A',
      'price': 95.0,
      'quality': 85,
      'market_share': 0.3,
    },
    {
      'name': 'Competitor B',
      'price': 110.0,
      'quality': 90,
      'market_share': 0.25,
    },
    {
      'name': 'Competitor C',
      'price': 85.0,
      'quality': 75,
      'market_share': 0.2,
    },
  ];

  static const List<Map<String, dynamic>> testPerformance = [
    {
      'metric': 'revenue',
      'value': 10000.0,
      'trend': [9000.0, 9500.0, 10000.0],
    },
    {
      'metric': 'conversion',
      'value': 2.5,
      'trend': [2.2, 2.3, 2.5],
    },
    {
      'metric': 'roi',
      'value': 150.0,
      'trend': [140.0, 145.0, 150.0],
    },
  ];
}
