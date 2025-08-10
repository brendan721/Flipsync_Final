import 'package:flutter_test/flutter_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flipsync_mobile/data/repositories/auth_repository.dart';
import 'package:flipsync_mobile/core/network/api_service.dart';
import 'package:flipsync_mobile/core/errors/exceptions.dart';

import 'auth_repository_test.mocks.dart';

@GenerateMocks([ApiService, SharedPreferences])
void main() {
  group('AuthRepository Tests', () {
    late AuthRepository authRepository;
    late MockApiService mockApiService;
    late MockSharedPreferences mockSharedPreferences;

    setUp(() {
      mockApiService = MockApiService();
      mockSharedPreferences = MockSharedPreferences();
      authRepository = AuthRepository(mockApiService);

      // Mock SharedPreferences.getInstance()
      SharedPreferences.setMockInitialValues({});
    });

    group('eBay OAuth', () {
      test('should return OAuth URL when getEbayOAuthUrl succeeds', () async {
        // Arrange
        const expectedUrl = 'https://auth.ebay.com/oauth2/authorize?client_id=test&redirect_uri=test';
        when(mockApiService.get('/api/v1/ebay/oauth/url')).thenAnswer((_) async => {'oauth_url': expectedUrl});

        // Act
        final result = await authRepository.getEbayOAuthUrl();

        // Assert
        expect(result, expectedUrl);
        verify(mockApiService.get('/api/v1/ebay/oauth/url')).called(1);
      });

      test('should throw ServerException when getEbayOAuthUrl fails', () async {
        // Arrange
        when(mockApiService.get('/api/v1/ebay/oauth/url')).thenThrow(const ServerException('Failed to get OAuth URL'));

        // Act & Assert
        expect(() => authRepository.getEbayOAuthUrl(), throwsA(isA<ServerException>()));
      });

      test('should exchange code for tokens successfully', () async {
        // Arrange
        const code = 'test_code';
        const state = 'test_state';
        final expectedTokens = {
          'access_token': 'test_access_token',
          'refresh_token': 'test_refresh_token',
          'expires_in': 7200,
        };

        when(
          mockApiService.post('/api/v1/ebay/oauth/callback', data: {'code': code, 'state': state}),
        ).thenAnswer((_) async => expectedTokens);

        // Act
        final result = await authRepository.exchangeCodeForTokens(code, state);

        // Assert
        expect(result, expectedTokens);
        verify(mockApiService.post('/api/v1/ebay/oauth/callback', data: {'code': code, 'state': state})).called(1);
      });

      test('should refresh eBay tokens successfully', () async {
        // Arrange
        const refreshToken = 'test_refresh_token';
        final expectedTokens = {
          'access_token': 'new_access_token',
          'refresh_token': 'new_refresh_token',
          'expires_in': 7200,
        };

        when(
          mockApiService.post('/api/v1/ebay/oauth/refresh', data: {'refresh_token': refreshToken}),
        ).thenAnswer((_) async => expectedTokens);

        // Act
        final result = await authRepository.refreshEbayTokens(refreshToken);

        // Assert
        expect(result, expectedTokens);
        verify(mockApiService.post('/api/v1/ebay/oauth/refresh', data: {'refresh_token': refreshToken})).called(1);
      });
    });

    group('Token Management', () {
      test('should store tokens locally', () async {
        // Arrange
        const accessToken = 'test_access_token';
        const refreshToken = 'test_refresh_token';
        const expiresIn = 7200;

        when(mockSharedPreferences.setString(any, any)).thenAnswer((_) async => true);
        when(mockSharedPreferences.setInt(any, any)).thenAnswer((_) async => true);

        // Act
        await authRepository.storeTokens(accessToken, refreshToken, expiresIn);

        // Assert
        verify(mockSharedPreferences.setString('ebay_access_token', accessToken)).called(1);
        verify(mockSharedPreferences.setString('ebay_refresh_token', refreshToken)).called(1);
        verify(mockSharedPreferences.setInt('ebay_token_expires_at', any)).called(1);
      });

      test('should retrieve stored tokens', () async {
        // Arrange
        const accessToken = 'stored_access_token';
        const refreshToken = 'stored_refresh_token';
        final expiresAt = DateTime.now().add(const Duration(hours: 1)).millisecondsSinceEpoch;

        when(mockSharedPreferences.getString('ebay_access_token')).thenReturn(accessToken);
        when(mockSharedPreferences.getString('ebay_refresh_token')).thenReturn(refreshToken);
        when(mockSharedPreferences.getInt('ebay_token_expires_at')).thenReturn(expiresAt);

        // Act
        final result = await authRepository.getStoredTokens();

        // Assert
        expect(result!['access_token'], accessToken);
        expect(result['refresh_token'], refreshToken);
        expect(result['expires_at'], expiresAt);
      });

      test('should return null when no tokens are stored', () async {
        // Arrange
        when(mockSharedPreferences.getString(any)).thenReturn(null);
        when(mockSharedPreferences.getInt(any)).thenReturn(null);

        // Act
        final result = await authRepository.getStoredTokens();

        // Assert
        expect(result, isNull);
      });

      test('should clear stored tokens', () async {
        // Arrange
        when(mockSharedPreferences.remove(any)).thenAnswer((_) async => true);

        // Act
        await authRepository.clearTokens();

        // Assert
        verify(mockSharedPreferences.remove('ebay_access_token')).called(1);
        verify(mockSharedPreferences.remove('ebay_refresh_token')).called(1);
        verify(mockSharedPreferences.remove('ebay_token_expires_at')).called(1);
      });
    });

    group('Token Validation', () {
      test('should return true for valid tokens', () async {
        // Arrange
        const accessToken = 'valid_token';
        when(
          mockApiService.get('/api/v1/ebay/validate', headers: {'Authorization': 'Bearer $accessToken'}),
        ).thenAnswer((_) async => {'valid': true});

        // Act
        final result = await authRepository.validateToken(accessToken);

        // Assert
        expect(result, true);
      });

      test('should return false for invalid tokens', () async {
        // Arrange
        const accessToken = 'invalid_token';
        when(
          mockApiService.get('/api/v1/ebay/validate', headers: {'Authorization': 'Bearer $accessToken'}),
        ).thenThrow(const ServerException('Invalid token'));

        // Act
        final result = await authRepository.validateToken(accessToken);

        // Assert
        expect(result, false);
      });
    });

    group('Error Handling', () {
      test('should handle network errors gracefully', () async {
        // Arrange
        when(mockApiService.get('/api/v1/ebay/oauth/url')).thenThrow(NetworkException('No internet connection'));

        // Act & Assert
        expect(() => authRepository.getEbayOAuthUrl(), throwsA(isA<NetworkException>()));
      });

      test('should handle server errors gracefully', () async {
        // Arrange
        when(mockApiService.get('/api/v1/ebay/oauth/url')).thenThrow(ServerException('Internal server error'));

        // Act & Assert
        expect(() => authRepository.getEbayOAuthUrl(), throwsA(isA<ServerException>()));
      });
    });
  });
}
