// Core imports
import 'dart:async';
import 'package:dio/dio.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
// Service imports
import 'package:flipsync/core/services/api_service.dart';
import 'package:flipsync/core/services/background/background_task_scheduler.dart';
import 'package:flipsync/core/services/battery/battery_optimization_service.dart';
import 'package:flipsync/core/services/file_sync_service.dart';
import 'package:flipsync/core/services/network/network_optimization_service.dart';
import 'package:flipsync/core/services/sensors/sensor_optimization_service.dart';
import 'package:flipsync/core/storage/offline_storage_service.dart';
import 'package:flipsync/core/network/network_info.dart';
import 'package:flipsync/core/error/error_handler.dart';
import 'package:flipsync/core/utils/logger.dart';
import 'package:mocktail/mocktail.dart';
import 'package:provider/provider.dart';

/// Types of tests that can be run
enum TestTypes { unit, widget, integration }

/// Configuration for the test environment
class TestEnvironmentConfig {
  /// Flag to indicate whether to use the real backend or mock backend.
  /// This is used for toggling between real and mock backends for testing.
  static bool useRealBackend = false;

  /// The URL of the backend API when using the real backend.
  /// This should be the development server when running locally.
  static const String backendUrl = 'https://localhost';

  /// The type of test being run
  static TestTypes testType = TestTypes.unit;

  // Docker backend URL - update this to match your Docker setup
  static const String backendBaseUrl = 'https://localhost';

  // Which test types should use the real backend (when useRealBackend is true)
  static const bool useRealBackendForUnitTests = true; // Changed to true
  static const bool useRealBackendForWidgetTests = false;
  static const bool useRealBackendForIntegrationTests = true;

  // Platform-specific configurations
  static bool get isWebPlatform => kIsWeb;
}

// Base Storage Service class
abstract class StorageService {
  dynamic getItem(String key);
  Future<void> setItem(String key, dynamic value);
  Future<void> removeItem(String key);
}

// Define mock classes using Mocktail - only mocking services that are necessary
class MockAuthService extends Mock implements SimpleAuthService {}

class MockStorageService extends Mock implements StorageService {}

class MockBackgroundTaskScheduler extends Mock implements BackgroundTaskScheduler {}

class MockBatteryOptimizationService extends Mock implements BatteryOptimizationService {}

class MockFileSyncService extends Mock implements FileSyncService {}

class MockNetworkOptimizationService extends Mock implements NetworkOptimizationService {}

class MockSensorOptimizationService extends Mock implements SensorOptimizationService {}

class MockOfflineStorageService extends Mock implements OfflineStorageService {}

// Simple interface for auth to avoid full implementation
abstract class SimpleAuthService {
  Future<bool> get isAuthenticated;
  Map<String, dynamic>? get currentUser;
}

// Simple network state implementation
class NetworkState {
  bool _isOnline = true;
  String? _error;
  final StreamController<bool> _connectionController = StreamController<bool>.broadcast();

  Stream<bool> get connectionStatus => _connectionController.stream;

  bool get isOnline => _isOnline;
  String? get error => _error;

  void setOnline() {
    _isOnline = true;
    _error = null;
    _connectionController.add(true);
  }

  void setOffline() {
    _isOnline = false;
    _connectionController.add(false);
  }

  void setError(String error) {
    _error = error;
  }

  void dispose() {
    _connectionController.close();
  }
}

// Test configuration
void configureTests() {
  TestWidgetsFlutterBinding.ensureInitialized();

  // Register any fallback values needed for Mocktail
  registerFallbackValue(MaterialPageRoute(builder: (_) => Container()));
}

// Call this in your test files to use the global test configuration
void setupTestConfig() {
  configureTests();
}

// Test Data
const testUser = {'id': '1', 'email': 'test@example.com', 'name': 'Test User'};

const testListings = [
  {
    'id': '1',
    'title': 'Test Listing 1',
    'description': 'Description 1',
    'price': 100.0,
  },
  {
    'id': '2',
    'title': 'Test Listing 2',
    'description': 'Description 2',
    'price': 200.0,
  },
];

// Test Utilities
class TestWrapper extends StatelessWidget {
  final Widget child;
  final ApiService apiService;
  final SimpleAuthService authService;
  final StorageService storageService;

  const TestWrapper({
    super.key,
    required this.child,
    required this.apiService,
    required this.authService,
    required this.storageService,
  });

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<ApiService>.value(value: apiService),
        Provider<SimpleAuthService>.value(value: authService),
        Provider<StorageService>.value(value: storageService),
      ],
      child: MaterialApp(home: child),
    );
  }
}

// Real API service factory that uses Dio with interceptors to provide test data
ApiService createRealApiService() {
  // Create a real Dio instance
  final dio = Dio();

  // Configure to use real backend if enabled
  if (TestEnvironmentConfig.useRealBackend) {
    dio.options.baseUrl = TestEnvironmentConfig.backendBaseUrl;
    print('🔄 Using REAL backend at ${dio.options.baseUrl}');
  } else {
    print('🔄 Using MOCK backend with test data');

    // When not using real backend, add interceptor to return test data
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          // Let the request continue but it won't actually go to the network
          return handler.next(options);
        },
        onResponse: (response, handler) {
          // Test responses will be created in the error handler
          return handler.next(response);
        },
        onError: (DioException e, handler) {
          // IMPORTANT: Only use mock responses in isolated test environments
          // This interceptor should NEVER affect production builds

          // Check if we're in a test environment and mocking is explicitly enabled
          const bool enableMockResponses =
              bool.fromEnvironment('ENABLE_TEST_MOCKS', defaultValue: false);

          if (!enableMockResponses) {
            // In production or when mocks are disabled, let the real error propagate
            return handler.next(e);
          }

          // Only create mock responses when explicitly enabled for testing
          Response<dynamic> mockResponse;

          if (e.requestOptions.path.contains('/user')) {
            mockResponse = Response(
              data: testUser,
              statusCode: 200,
              requestOptions: e.requestOptions,
            );
          } else if (e.requestOptions.path.contains('/listings')) {
            mockResponse = Response(
              data: testListings,
              statusCode: 200,
              requestOptions: e.requestOptions,
            );
          } else {
            // Default response for other endpoints
            mockResponse = Response(
              data: {'message': 'Test response'},
              statusCode: 200,
              requestOptions: e.requestOptions,
            );
          }

          // Return the mock response only when testing is explicitly enabled
          return handler.resolve(mockResponse);
        },
      ),
    );
  }

  // Create real implementations of required dependencies
  final logger = AppLogger(tag: 'TestApiService');
  final errorHandler = ErrorHandler(logger);

  // Return a real ApiService with the test-configured dependencies
  // This ApiService takes Dio and ErrorHandler as positional parameters
  return ApiService(dio, errorHandler);
}

// Network info implementation for tests
class TestNetworkInfo implements NetworkInfo {
  @override
  Future<bool> get isConnected => Future.value(true);

  @override
  Future<bool> isApiReachable() async {
    return true;
  }
}

// Test Helpers
Future<void> pumpTestWidget(
  WidgetTester tester,
  Widget widget, {
  ApiService? apiService,
  SimpleAuthService? authService,
  StorageService? storageService,
}) async {
  await tester.pumpWidget(
    TestWrapper(
      apiService: apiService ?? createRealApiService(),
      authService: authService ?? MockAuthService(),
      storageService: storageService ?? MockStorageService(),
      child: widget,
    ),
  );
  await tester.pumpAndSettle();
}

// Custom Matchers
Matcher hasErrorText(String errorText) {
  return predicate((dynamic widget) {
    if (widget is! FormField<dynamic>) {
      return false;
    }
    // Use widget.errorText if available, otherwise check decoration.errorText
    final errorValue = widget.toString().contains('errorText: $errorText');
    return errorValue;
  }, 'FormField has error text "$errorText"');
}

// Test Priority Groups
enum TestPriority {
  P0, // Critical - Must pass for production
  P1, // High - Required for initial release
  P2, // Medium - Important but not blocking
  P3, // Low - Nice to have
}

// Test Categories
enum TestCategory { CORE, INTEGRATION, UI, PERFORMANCE, SECURITY }

// Test Group Configuration
class TestGroup {
  final String name;
  final TestPriority priority;
  final TestCategory category;
  final List<String> dependencies;

  const TestGroup({
    required this.name,
    required this.priority,
    required this.category,
    this.dependencies = const [],
  });
}

// Production Critical Test Groups
const productionCriticalTests = {
  'auth': TestGroup(
    name: 'Authentication',
    priority: TestPriority.P0,
    category: TestCategory.CORE,
  ),
  'sync': TestGroup(
    name: 'Data Synchronization',
    priority: TestPriority.P0,
    category: TestCategory.CORE,
    dependencies: ['auth'],
  ),
  'background': TestGroup(
    name: 'Background Tasks',
    priority: TestPriority.P0,
    category: TestCategory.CORE,
    dependencies: ['sync'],
  ),
  'storage': TestGroup(
    name: 'Storage Management',
    priority: TestPriority.P0,
    category: TestCategory.CORE,
  ),
  'error': TestGroup(
    name: 'Error Recovery',
    priority: TestPriority.P0,
    category: TestCategory.CORE,
    dependencies: ['sync', 'background'],
  ),
};

// Test Environment Configuration
class TestEnvironment {
  final bool isProduction;
  final TestPriority minimumPriority;
  final Set<TestCategory> enabledCategories;

  const TestEnvironment({
    this.isProduction = false,
    this.minimumPriority = TestPriority.P3,
    this.enabledCategories = const {
      TestCategory.CORE,
      TestCategory.INTEGRATION,
      TestCategory.UI,
      TestCategory.PERFORMANCE,
      TestCategory.SECURITY,
    },
  });

  static const production = TestEnvironment(
    isProduction: true,
    minimumPriority: TestPriority.P0,
    enabledCategories: {TestCategory.CORE, TestCategory.SECURITY},
  );

  static const staging = TestEnvironment(
    isProduction: false,
    minimumPriority: TestPriority.P1,
    enabledCategories: {
      TestCategory.CORE,
      TestCategory.INTEGRATION,
      TestCategory.SECURITY,
    },
  );

  static const development = TestEnvironment(
    isProduction: false,
    minimumPriority: TestPriority.P2,
  );
}

// Enhanced Test Setup
void setupTestEnvironment([
  TestEnvironment environment = const TestEnvironment(),
]) {
  TestWidgetsFlutterBinding.ensureInitialized();

  // Set up real ApiService with test data
  final apiService = createRealApiService();

  // Set up default auth state
  final mockAuthService = MockAuthService();
  when(() => mockAuthService.isAuthenticated).thenAnswer((_) async => false);
  when(() => mockAuthService.currentUser).thenReturn(null);

  // Set up storage mocks
  final mockStorageService = MockStorageService();
  when(() => mockStorageService.getItem(any())).thenReturn(null);

  // Set up network state
  final networkState = NetworkState();

  // Configure test environment
  if (environment.isProduction) {
    // Additional production-specific setup
    setupSecurityTests();
    setupPerformanceMonitoring();
  }
}

// Production-specific test helpers
void setupSecurityTests() {
  // Security-specific test configuration
}

void setupPerformanceMonitoring() {
  // Performance monitoring setup
}

// Unit Test Helpers
void setupUnitTest() {
  TestWidgetsFlutterBinding.ensureInitialized();
}

// Add a main function to prevent the test runner from failing
// This file is intended as a configuration helper, not as a test file itself
void main() {
  group('TestConfig', () {
    test('This file contains only configuration and helpers, not tests', () {
      expect(true, isTrue);
    });
  });
}
