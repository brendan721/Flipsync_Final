import 'package:flutter_test/flutter_test.dart';
import 'package:dio/dio.dart';
import 'package:mocktail/mocktail.dart';
import 'package:flipsync/core/auth/auth_service.dart';
import 'package:flipsync/core/auth/token_rotation_handler.dart';
import 'package:flipsync/core/network/api_middleware.dart';
import 'package:flipsync/core/network/csrf_interceptor.dart';
import 'package:flipsync/core/state/auth_state.dart';
import 'package:flipsync/core/utils/logger.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'dart:async';
import 'package:get_it/get_it.dart';

// Mock classes
class MockDio extends Mock implements Dio {}

class MockFlutterSecureStorage extends Mock implements FlutterSecureStorage {}

class MockSharedPreferences extends Mock implements SharedPreferences {}

class MockCSRFInterceptor extends Mock implements CSRFInterceptor {}

class MockApiMiddleware extends Mock implements ApiMiddleware {}

class MockAppLogger extends Mock implements AppLogger {}

class MockTokenRotationHandler extends Mock implements TokenRotationHandler {}

class MockRequestInterceptorHandler extends Mock
    implements RequestInterceptorHandler {}

void main() {
  late MockDio mockDio;
  late MockFlutterSecureStorage mockStorage;
  late MockSharedPreferences mockPrefs;
  late MockCSRFInterceptor mockCSRFInterceptor;
  late MockAppLogger mockLogger;
  late AuthService authService;
  late AuthState authState;
  late MockTokenRotationHandler mockTokenRotationHandler;

  setUpAll(() {
    registerFallbackValue(RequestOptions(path: '/test'));
    SharedPreferences.setMockInitialValues({});

    // Register the mock TokenRotationHandler with GetIt
    final getIt = GetIt.instance;
    if (!getIt.isRegistered<TokenRotationHandler>()) {
      getIt.registerSingleton<TokenRotationHandler>(MockTokenRotationHandler());
    }
  });

  tearDownAll(() {
    // Reset GetIt instance
    GetIt.instance.reset();
  });

  setUp(() {
    mockDio = MockDio();
    mockStorage = MockFlutterSecureStorage();
    mockPrefs = MockSharedPreferences();
    mockCSRFInterceptor = MockCSRFInterceptor();
    mockLogger = MockAppLogger();
    mockTokenRotationHandler = MockTokenRotationHandler();

    // Setup basic secure storage behavior
    when(
      () =>
          mockStorage.write(key: any(named: 'key'), value: any(named: 'value')),
    ).thenAnswer((_) async {});
    when(
      () => mockStorage.read(key: any(named: 'key')),
    ).thenAnswer((_) async => null);
    when(
      () => mockStorage.delete(key: any(named: 'key')),
    ).thenAnswer((_) async {});

    // Setup CSRF interceptor mock
    when(() => mockCSRFInterceptor.clearToken()).thenAnswer((_) async {});

    when(
      () => mockCSRFInterceptor.refreshToken(),
    ).thenAnswer((_) async => 'new-csrf-token');

    // Setup token rotation handler mock
    when(
      () => mockTokenRotationHandler.checkAndPerformRotation(),
    ).thenAnswer((_) async => false);

    // Initialize services
    authService = AuthService(
      dio: mockDio,
      storage: mockStorage,
      csrfInterceptor: mockCSRFInterceptor,
    );

    // Mock Auth Service behavior
    when(() => mockDio.post('/auth/logout')).thenAnswer(
      (_) async => Response(
        requestOptions: RequestOptions(path: '/auth/logout'),
        statusCode: 200,
        data: {'success': true},
      ),
    );

    authState = AuthState(authService);
  });

  group('Authentication Integration Tests', () {
    test('Full authentication flow with token refresh', () async {
      // Arrange: Set up login response
      when(
        () => mockDio.post('/auth/login', data: any(named: 'data')),
      ).thenAnswer(
        (_) async => Response(
          requestOptions: RequestOptions(path: '/auth/login'),
          statusCode: 200,
          data: {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
          },
        ),
      );

      // Arrange: Set up refresh token response
      when(
        () => mockDio.post('/auth/refresh', data: any(named: 'data')),
      ).thenAnswer(
        (_) async => Response(
          requestOptions: RequestOptions(path: '/auth/refresh'),
          statusCode: 200,
          data: {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
          },
        ),
      );

      // Act: Login
      final loginSuccess = await authState.login(
        'test@example.com',
        'password123',
      );

      // Assert: Login successful
      expect(loginSuccess, isTrue);
      expect(authState.isAuthenticated, isTrue);
      expect(authState.authToken, isNotNull);

      // Act: Simulate token expiration
      authState.simulateTokenExpiration();
      expect(authState.tokenExpired, isTrue);

      // Act: Refresh token
      final refreshSuccess = await authState.refreshTokenIfNeeded();

      // Assert: Token refreshed successfully
      expect(refreshSuccess, isTrue);
      verify(
        () => mockStorage.write(key: 'access_token', value: 'new_access_token'),
      ).called(1);
      verify(
        () =>
            mockStorage.write(key: 'refresh_token', value: 'new_refresh_token'),
      ).called(1);

      // Act: Logout
      authState.logout();

      // Assert: Logged out successfully
      await untilCalled(() => mockStorage.delete(key: 'access_token'));
      verify(() => mockStorage.delete(key: 'access_token')).called(1);
      verify(() => mockStorage.delete(key: 'refresh_token')).called(1);
      expect(authState.isAuthenticated, isFalse);
      expect(authState.authToken, isNull);
    });

    test('API Middleware handles token refreshing correctly', () async {
      // Arrange: Set up authenticated state
      when(() => mockDio.fetch(any())).thenAnswer(
        (_) async => Response(
          requestOptions: RequestOptions(path: '/agents'),
          statusCode: 200,
          data: {'success': true},
        ),
      );

      // Create middleware with explicit token rotation handler
      final middleware = ApiMiddleware(
        mockDio,
        authState,
        mockCSRFInterceptor,
        tokenRotationHandler: mockTokenRotationHandler,
      );

      // Arrange: Set up token state
      authState.setAuthState(
        isAuthenticated: true,
        authToken: 'expired_token',
        tokenExpiry: DateTime.now().subtract(const Duration(minutes: 5)),
      );

      // Set up refresh behavior
      when(
        () => mockTokenRotationHandler.checkAndPerformRotation(),
      ).thenAnswer((_) async => false);

      // Request options with authentication needed
      final options = RequestOptions(path: '/agents', method: 'GET');

      // Act: Create a handler that will capture the processed options
      final completer = Completer<RequestOptions>();
      final handler = MockRequestInterceptorHandler();

      // Setup the mock handler to complete our completer when next is called
      when(() => handler.next(any())).thenAnswer((invocation) {
        completer.complete(invocation.positionalArguments[0] as RequestOptions);
      });

      // Process the request through middleware
      middleware.onRequest(options, handler);

      // Wait for the middleware to complete
      final processedOptions = await completer.future;

      // Assert: Token refreshed and added to headers
      expect(processedOptions.headers['Authorization'], startsWith('Bearer '));
    });
  });
}
