import 'dart:async';
import 'package:flutter_test/flutter_test.dart';
import 'package:dio/dio.dart';
import 'package:mocktail/mocktail.dart';
import 'package:flipsync/core/auth/auth_service.dart';
import 'package:flipsync/core/auth/token_rotation_handler.dart';
import 'package:flipsync/core/network/api_middleware.dart';
import 'package:flipsync/core/network/csrf_interceptor.dart';
import 'package:flipsync/core/network/api_client.dart';
import 'package:flipsync/core/state/auth_state.dart';
import 'package:flipsync/core/utils/logger.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:get_it/get_it.dart';

// Mock classes
class MockDio extends Mock implements Dio {}

class MockFlutterSecureStorage extends Mock implements FlutterSecureStorage {}

class MockSharedPreferences extends Mock implements SharedPreferences {}

class MockCSRFInterceptor extends Mock implements CSRFInterceptor {}

class MockApiClient extends Mock implements ApiClient {}

class MockAppLogger extends Mock implements AppLogger {}

class MockTokenRotationHandler extends Mock implements TokenRotationHandler {}

class MockRequestInterceptorHandler extends Mock
    implements RequestInterceptorHandler {}

class MockResponseInterceptorHandler extends Mock
    implements ResponseInterceptorHandler {}

class MockErrorInterceptorHandler extends Mock
    implements ErrorInterceptorHandler {}

void main() {
  late MockDio mockDio;
  late MockFlutterSecureStorage mockStorage;
  late MockSharedPreferences mockPrefs;
  late MockCSRFInterceptor mockCSRFInterceptor;
  late MockAppLogger mockLogger;
  late AuthService authService;
  late AuthState authState;
  late ApiMiddleware apiMiddleware;
  late MockApiClient mockApiClient;
  late MockTokenRotationHandler mockTokenRotationHandler;

  setUpAll(() {
    registerFallbackValue(RequestOptions(path: '/test'));
    registerFallbackValue(RequestInterceptorHandler());
    registerFallbackValue(ResponseInterceptorHandler());
    registerFallbackValue(ErrorInterceptorHandler());
    registerFallbackValue(
      DioException(requestOptions: RequestOptions(path: '/test')),
    );
    SharedPreferences.setMockInitialValues({});

    // Register the mock TokenRotationHandler with GetIt
    final getIt = GetIt.instance;
    if (!getIt.isRegistered<TokenRotationHandler>()) {
      getIt.registerSingleton<TokenRotationHandler>(MockTokenRotationHandler());
    }
  });

  tearDownAll(() {
    // Reset GetIt instance
    final getIt = GetIt.instance;
    getIt.reset();
  });

  setUp(() {
    mockDio = MockDio();
    mockStorage = MockFlutterSecureStorage();
    mockPrefs = MockSharedPreferences();
    mockCSRFInterceptor = MockCSRFInterceptor();
    mockLogger = MockAppLogger();
    mockApiClient = MockApiClient();
    mockTokenRotationHandler = MockTokenRotationHandler();

    // Setup basic storage behavior
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

    // Setup basic prefs behavior
    when(() => mockPrefs.setString(any(), any())).thenAnswer((_) async => true);
    when(() => mockPrefs.getString(any())).thenReturn(null);
    when(() => mockPrefs.remove(any())).thenAnswer((_) async => true);

    // Setup CSRF interceptor
    when(() => mockCSRFInterceptor.clearToken()).thenAnswer((_) async {});
    when(
      () => mockCSRFInterceptor.refreshToken(),
    ).thenAnswer((_) async => 'test-csrf-token');

    // Setup token rotation handler
    when(
      () => mockTokenRotationHandler.checkAndPerformRotation(),
    ).thenAnswer((_) async => false);

    // Initialize services
    authService = AuthService(
      dio: mockDio,
      storage: mockStorage,
      csrfInterceptor: mockCSRFInterceptor,
    );

    authState = AuthState(authService);

    apiMiddleware = ApiMiddleware(
      mockDio,
      authState,
      mockCSRFInterceptor,
      tokenRotationHandler: mockTokenRotationHandler,
    );
  });

  group('Authentication API Integration', () {
    test('Full authentication flow with API client', () async {
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
            'user': {'id': 'user123', 'email': 'test@example.com'},
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

      // Arrange: Set up an API request that will need authentication
      when(
        () => mockDio.get(
          any(),
          options: any(named: 'options'),
          queryParameters: any(named: 'queryParameters'),
        ),
      ).thenAnswer(
        (_) async => Response(
          requestOptions: RequestOptions(path: '/some/endpoint'),
          statusCode: 200,
          data: {'success': true},
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

      // Act: Make the API middleware process a request
      final originalOptions = RequestOptions(
        path: '/some/endpoint',
        method: 'GET',
      );

      // Setup a handler that captures the processed options
      final completer = Completer<RequestOptions>();
      final handler = MockRequestInterceptorHandler();

      when(() => handler.next(any())).thenAnswer((invocation) {
        completer.complete(invocation.positionalArguments[0] as RequestOptions);
      });

      // Process request through middleware
      apiMiddleware.onRequest(originalOptions, handler);
      final processedOptions = await completer.future;

      // Assert: Auth header was added
      expect(
        processedOptions.headers['Authorization'],
        'Bearer test_access_token',
      );

      // Act: Simulate token expiration
      authState.simulateTokenExpiration();
      expect(authState.tokenExpired, isTrue);

      // Setup a new handler for the expired token scenario
      final expiredCompleter = Completer<RequestOptions>();
      final expiredHandler = MockRequestInterceptorHandler();

      when(() => expiredHandler.next(any())).thenAnswer((invocation) {
        expiredCompleter.complete(
          invocation.positionalArguments[0] as RequestOptions,
        );
      });

      // Process another request through middleware with expired token
      apiMiddleware.onRequest(originalOptions, expiredHandler);
      final refreshedOptions = await expiredCompleter.future;

      // Assert: Token was refreshed and new token is used
      verify(
        () =>
            mockStorage.write(key: 'access_token', value: any(named: 'value')),
      ).called(greaterThan(0));
      expect(refreshedOptions.headers['Authorization'], isNotNull);

      // Mock logout response
      when(
        () => mockDio.post('/auth/logout', options: any(named: 'options')),
      ).thenAnswer(
        (_) async => Response(
          requestOptions: RequestOptions(path: '/auth/logout'),
          statusCode: 200,
          data: {'success': true},
        ),
      );

      // Act: Logout
      authState.logout();

      // Assert: Logged out successfully
      await untilCalled(() => mockStorage.delete(key: 'access_token'));
      verify(() => mockStorage.delete(key: 'access_token')).called(1);
      verify(() => mockStorage.delete(key: 'refresh_token')).called(1);
      expect(authState.isAuthenticated, isFalse);
      expect(authState.authToken, isNull);
    });

    test('API middleware handles unauthorized responses correctly', () async {
      // Setup auth state with a token
      when(
        () => mockStorage.read(key: 'access_token'),
      ).thenAnswer((_) async => 'valid_token');

      // Set auth state to authenticated
      authState.setAuthState(
        isAuthenticated: true,
        authToken: 'valid_token',
        tokenExpiry: DateTime.now().add(const Duration(hours: 1)),
      );

      // Setup a 401 response
      final unauthorizedResponse = Response(
        requestOptions: RequestOptions(path: '/some/endpoint'),
        statusCode: 401,
        data: {'message': 'Unauthorized'},
      );

      // Setup a handler to track the error handling
      final errorHandler = MockErrorInterceptorHandler();
      final errorCompleter = Completer<DioException>();

      when(() => errorHandler.next(any())).thenAnswer((invocation) {
        errorCompleter.complete(
          invocation.positionalArguments[0] as DioException,
        );
      });

      // Create error to process
      final error = DioException(
        requestOptions: RequestOptions(path: '/some/endpoint'),
        response: unauthorizedResponse,
        type: DioExceptionType.badResponse,
      );

      // Process the error through middleware
      apiMiddleware.onError(error, errorHandler);
      await errorCompleter.future;

      // Verify auth state was cleared on 401
      await untilCalled(() => mockStorage.delete(key: 'access_token'));
      verify(() => mockStorage.delete(key: 'access_token')).called(1);
      expect(authState.isAuthenticated, isFalse);
    });
  });
}
