import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/core/auth/auth_service.dart';
import 'package:mocktail/mocktail.dart';

// Local mock definitions to avoid dependency on non-existent files
class MockDio extends Mock implements Dio {}

class MockFlutterSecureStorage extends Mock implements FlutterSecureStorage {}

// Test helper constants and utilities
class AuthTestHelper {
  static const testAccessToken = 'test_access_token';
  static const testRefreshToken = 'test_refresh_token';
  static const validEmail = 'test@example.com';
  static const validPassword = 'password123';

  static void setupSuccessfulAuth(
      MockDio mockDio, MockFlutterSecureStorage mockStorage) {
    when(() => mockDio.post(
          '/auth/login',
          data: {
            'username': validEmail,
            'password': validPassword,
          },
        )).thenAnswer((_) async => Response(
          data: {
            'access_token': testAccessToken,
            'refresh_token': testRefreshToken,
          },
          statusCode: 200,
          requestOptions: RequestOptions(path: '/auth/login'),
        ));

    when(() => mockStorage.write(
          key: any(named: 'key'),
          value: any(named: 'value'),
        )).thenAnswer((_) async {});
  }

  static void setupFailedAuth(MockDio mockDio) {
    when(() => mockDio.post(
          '/auth/login',
          data: any(named: 'data'),
        )).thenThrow(DioException(
      response: Response(
        statusCode: 401,
        requestOptions: RequestOptions(path: '/auth/login'),
      ),
      requestOptions: RequestOptions(path: '/auth/login'),
      type: DioExceptionType.badResponse,
    ));
  }

  static void verifyAuthSuccess(MockFlutterSecureStorage mockStorage) {
    verify(() => mockStorage.write(key: 'access_token', value: testAccessToken))
        .called(1);
    verify(() =>
            mockStorage.write(key: 'refresh_token', value: testRefreshToken))
        .called(1);
  }
}

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late AuthService authService;
  late MockDio mockDio;
  late MockFlutterSecureStorage mockStorage;

  setUpAll(() {
    registerFallbackValue(RequestOptions(path: ''));
  });

  setUp(() {
    mockDio = MockDio();
    mockStorage = MockFlutterSecureStorage();
    authService = AuthService(dio: mockDio, storage: mockStorage);

    // Setup basic mocks for secureStorage
    when(() => mockStorage.read(key: any(named: 'key')))
        .thenAnswer((_) async => null);
    when(() => mockStorage.write(
        key: any(named: 'key'),
        value: any(named: 'value'))).thenAnswer((_) async => {});
    when(() => mockStorage.delete(key: any(named: 'key')))
        .thenAnswer((_) async => {});
  });

  group('AuthService', () {
    group('login', () {
      test('successful login stores tokens', () async {
        // Arrange
        AuthTestHelper.setupSuccessfulAuth(mockDio, mockStorage);

        // Act
        await authService.login(
            AuthTestHelper.validEmail, AuthTestHelper.validPassword);

        // Assert
        AuthTestHelper.verifyAuthSuccess(mockStorage);
      });

      test('invalid credentials throws AuthException', () async {
        // Arrange
        AuthTestHelper.setupFailedAuth(mockDio);

        // Act & Assert
        expect(
          () => authService.login(AuthTestHelper.validEmail, 'wrong_password'),
          throwsA(isA<AuthException>().having(
              (e) => e.message, 'message', contains('Invalid credentials'))),
        );
      });
    });

    group('logout', () {
      test('logout clears stored tokens', () async {
        // Arrange - setup tokens first
        when(() => mockStorage.read(key: 'access_token'))
            .thenAnswer((_) async => AuthTestHelper.testAccessToken);
        when(() => mockStorage.read(key: 'refresh_token'))
            .thenAnswer((_) async => AuthTestHelper.testRefreshToken);

        // Act
        await authService.logout();

        // Assert
        verify(() => mockStorage.delete(key: 'access_token')).called(1);
        verify(() => mockStorage.delete(key: 'refresh_token')).called(1);
      });
    });

    group('token management', () {
      test('getAccessToken returns stored token', () async {
        // Arrange - Override the default mock to return a test token
        when(() => mockStorage.read(key: 'access_token'))
            .thenAnswer((_) async => AuthTestHelper.testAccessToken);
        when(() => mockStorage.read(key: 'refresh_token'))
            .thenAnswer((_) async => AuthTestHelper.testRefreshToken);

        // Initialize the auth service to load tokens from storage
        await authService.initialize();

        // Act
        final token = await authService.getAccessToken();

        // Assert
        expect(token, AuthTestHelper.testAccessToken);
        verify(() => mockStorage.read(key: 'access_token')).called(1);
      });

      test('refreshTokens updates stored tokens', () async {
        // Setup tokens first for the auth service
        when(() => mockStorage.read(key: 'access_token'))
            .thenAnswer((_) async => 'old_access_token');
        when(() => mockStorage.read(key: 'refresh_token'))
            .thenAnswer((_) async => 'old_refresh_token');

        // Initialize auth service to load the tokens
        await authService.initialize();

        // Setup the refresh token request
        when(() => mockDio.post(
              '/auth/refresh',
              data: {'refresh_token': 'old_refresh_token'},
            )).thenAnswer((_) async => Response(
              data: {
                'access_token': 'new_access_token',
                'refresh_token': 'new_refresh_token',
              },
              statusCode: 200,
              requestOptions: RequestOptions(path: '/auth/refresh'),
            ));

        // Act
        await authService.refreshTokens();

        // Assert
        verify(() => mockStorage.write(
            key: 'access_token', value: 'new_access_token')).called(1);
        verify(() => mockStorage.write(
            key: 'refresh_token', value: 'new_refresh_token')).called(1);
      });

      test('isAuthenticated returns true when tokens exist', () async {
        // Arrange
        when(() => mockStorage.read(key: 'access_token'))
            .thenAnswer((_) async => AuthTestHelper.testAccessToken);
        when(() => mockStorage.read(key: 'refresh_token'))
            .thenAnswer((_) async => AuthTestHelper.testRefreshToken);

        // Act
        final result = await authService.isAuthenticated();

        // Assert
        expect(result, isTrue);
      });

      test('isAuthenticated returns false when tokens do not exist', () async {
        // Arrange
        when(() => mockStorage.read(key: 'access_token'))
            .thenAnswer((_) async => null);
        when(() => mockStorage.read(key: 'refresh_token'))
            .thenAnswer((_) async => null);

        // Act
        final result = await authService.isAuthenticated();

        // Assert
        expect(result, isFalse);
      });
    });
  });
}
