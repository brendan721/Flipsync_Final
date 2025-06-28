import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:mocktail/mocktail.dart';
import 'package:flutter_test/flutter_test.dart';

// Define mocks with Mocktail
class MockDio extends Mock implements Dio {}

class MockFlutterSecureStorage extends Mock implements FlutterSecureStorage {}

// Create a simplified interface based on what we need from AuthService
abstract class SimpleAuthService {
  Future<bool> get isAuthenticated;
  Map<String, dynamic>? get currentUser;
  Future<void> login(String email, String password);
  Future<void> logout();
}

// Mock the simplified interface instead
class MockAuthService extends Mock implements SimpleAuthService {}

/// Helper for authentication-related tests
class AuthTestHelper {
  final MockAuthService mockAuthService;

  AuthTestHelper({MockAuthService? authService})
    : mockAuthService = authService ?? MockAuthService();

  /// Set up the mock auth service for a logged-in user state
  void setupLoggedInUser() {
    when(() => mockAuthService.isAuthenticated).thenAnswer((_) async => true);
    when(
      () => mockAuthService.currentUser,
    ).thenReturn({'id': '1', 'email': 'test@example.com', 'name': 'Test User'});
  }

  /// Set up the mock auth service for a logged-out user state
  void setupLoggedOutUser() {
    when(() => mockAuthService.isAuthenticated).thenAnswer((_) async => false);
    when(() => mockAuthService.currentUser).thenReturn(null);
  }

  /// Set up the mock auth service to simulate a successful login
  void setupSuccessfulLogin() {
    when(
      () => mockAuthService.login(any<String>(), any<String>()),
    ).thenAnswer((_) async {});
  }

  /// Set up the mock auth service to simulate a failed login
  void setupFailedLogin() {
    when(
      () => mockAuthService.login(any<String>(), any<String>()),
    ).thenThrow(Exception('Invalid credentials'));
  }

  static const testAccessToken = 'test_access_token';
  static const testRefreshToken = 'test_refresh_token';
  static const testUser = {
    'id': '1',
    'name': 'Test User',
    'email': 'test@example.com',
  };

  static void setupSuccessfulAuth(
    MockDio mockDio,
    MockFlutterSecureStorage mockStorage,
  ) {
    when(
      () => mockDio.post(
        '/auth/login',
        data: {'email': 'test@example.com', 'password': 'password123'},
      ),
    ).thenAnswer(
      (_) async => Response(
        data: {
          'access_token': testAccessToken,
          'refresh_token': testRefreshToken,
          'user': testUser,
        },
        statusCode: 200,
        requestOptions: RequestOptions(),
      ),
    );

    when(
      () => mockStorage.write(
        key: any<String>(named: 'key'),
        value: any<String>(named: 'value'),
      ),
    ).thenAnswer((_) async {});
  }

  static void setupFailedAuth(MockDio mockDio) {
    when(
      () => mockDio.post(
        '/auth/login',
        data: any<Map<String, dynamic>>(named: 'data'),
      ),
    ).thenThrow(
      DioException(
        requestOptions: RequestOptions(),
        response: Response(
          statusCode: 401,
          data: {'message': 'Invalid credentials'},
          requestOptions: RequestOptions(),
        ),
      ),
    );
  }

  static void verifyAuthSuccess(MockFlutterSecureStorage mockStorage) {
    verify(
      () => mockStorage.write(key: 'access_token', value: testAccessToken),
    ).called(1);
    verify(
      () => mockStorage.write(key: 'refresh_token', value: testRefreshToken),
    ).called(1);
  }

  static void setupMockDio(MockDio mockDio) {
    // Update any when() calls to use Mocktail lambda style
    // Example: when(mockDio.post(any)).thenAnswer(...) becomes:
    // when(() => mockDio.post(any())).thenAnswer(...)
  }

  static void setupMockStorage(MockFlutterSecureStorage mockStorage) {
    // Update any when() calls to use Mocktail lambda style
    // Example: when(mockStorage.read(key: anyNamed('key'))).thenAnswer(...) becomes:
    // when(() => mockStorage.read(key: any())).thenAnswer(...)
  }
}

// Add a main function to prevent the test runner from failing
// This file is intended as an auth test helper, not as a test file itself
void main() {
  group('AuthTestHelper', () {
    test('This file contains only auth test helper utilities, not tests', () {
      expect(true, isTrue);
    });
  });
}
