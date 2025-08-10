import 'package:flutter_test/flutter_test.dart';
import 'package:bloc_test/bloc_test.dart';
import 'package:mockito/mockito.dart';
import 'package:mockito/annotations.dart';
import 'package:flipsync_mobile/presentation/blocs/auth/auth_bloc.dart';
import 'package:flipsync_mobile/presentation/blocs/auth/auth_event.dart';
import 'package:flipsync_mobile/presentation/blocs/auth/auth_state.dart';
import 'package:flipsync_mobile/data/repositories/auth_repository.dart';
import 'package:flipsync_mobile/core/network/websocket_service.dart';
import 'package:flipsync_mobile/core/errors/exceptions.dart';

import 'auth_bloc_test.mocks.dart';

@GenerateMocks([AuthRepository, WebSocketService])
void main() {
  group('AuthBloc Tests', () {
    late AuthBloc authBloc;
    late MockAuthRepository mockAuthRepository;

    setUp(() {
      mockAuthRepository = MockAuthRepository();
      final mockWebSocketService = MockWebSocketService();
      authBloc = AuthBloc(mockAuthRepository, mockWebSocketService);
    });

    tearDown(() {
      authBloc.close();
    });

    test('initial state is AuthInitial', () {
      expect(authBloc.state, const AuthInitial());
    });

    group('AuthEbayLoginRequested', () {
      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthOAuthInProgress] when OAuth URL is fetched successfully',
        build: () {
          when(mockAuthRepository.startEbayOAuth('test_user')).thenAnswer(
            (_) async => {'oauth_url': 'https://auth.ebay.com/oauth2/authorize?client_id=test', 'state': 'test_state'},
          );
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthEbayLoginRequested('test_user')),
        expect: () => [
          const AuthLoading(),
          const AuthOAuthInProgress(
            oauthUrl: 'https://auth.ebay.com/oauth2/authorize?client_id=test',
            state: 'test_state',
          ),
        ],
        verify: (_) {
          verify(mockAuthRepository.startEbayOAuth('test_user')).called(1);
        },
      );

      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthError] when OAuth URL fetch fails',
        build: () {
          when(
            mockAuthRepository.startEbayOAuth('test_user'),
          ).thenThrow(const ServerException('Failed to get OAuth URL'));
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthEbayLoginRequested('test_user')),
        expect: () => [const AuthLoading(), const AuthError(message: 'Failed to get OAuth URL')],
        verify: (_) {
          verify(mockAuthRepository.startEbayOAuth('test_user')).called(1);
        },
      );
    });

    group('AuthOAuthCallbackReceived', () {
      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthAuthenticated] when OAuth callback is processed successfully',
        build: () {
          final tokens = {
            'access_token': 'test_access_token',
            'refresh_token': 'test_refresh_token',
            'expires_in': 7200,
          };
          when(mockAuthRepository.exchangeCodeForTokens('test_code', 'test_state')).thenAnswer((_) async => tokens);
          when(
            mockAuthRepository.storeTokens('test_access_token', 'test_refresh_token', 7200),
          ).thenAnswer((_) async {});
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthOAuthCallbackReceived(code: 'test_code', state: 'test_state')),
        expect: () => [
          const AuthLoading(),
          AuthAuthenticated(
            userId: 'test_user',
            environment: 'sandbox',
            tokenType: 'Bearer',
            expiresAt: DateTime.now().add(const Duration(hours: 2)),
            scopes: const ['https://api.ebay.com/oauth/api_scope'],
          ),
        ],
        verify: (_) {
          verify(mockAuthRepository.exchangeCodeForTokens('test_code', 'test_state')).called(1);
          verify(mockAuthRepository.storeTokens('test_access_token', 'test_refresh_token', 7200)).called(1);
        },
      );

      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthError] when OAuth callback processing fails',
        build: () {
          when(
            mockAuthRepository.exchangeCodeForTokens('invalid_code', 'invalid_state'),
          ).thenThrow(const ServerException('Invalid authorization code'));
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthOAuthCallbackReceived(code: 'invalid_code', state: 'invalid_state')),
        expect: () => [const AuthLoading(), const AuthError(message: 'Invalid authorization code')],
        verify: (_) {
          verify(mockAuthRepository.exchangeCodeForTokens('invalid_code', 'invalid_state')).called(1);
        },
      );
    });

    group('AuthTokenRefreshRequested', () {
      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthAuthenticated] when token refresh is successful',
        build: () {
          final newTokens = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_in': 7200,
          };
          when(mockAuthRepository.refreshEbayTokens('old_refresh_token')).thenAnswer((_) async => newTokens);
          when(mockAuthRepository.storeTokens('new_access_token', 'new_refresh_token', 7200)).thenAnswer((_) async {});
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthTokenRefreshRequested('test_user')),
        expect: () => [
          const AuthLoading(),
          AuthAuthenticated(
            userId: 'test_user',
            environment: 'sandbox',
            tokenType: 'Bearer',
            expiresAt: DateTime.now().add(const Duration(hours: 2)),
            scopes: const ['https://api.ebay.com/oauth/api_scope'],
          ),
        ],
        verify: (_) {
          verify(mockAuthRepository.refreshEbayTokens('old_refresh_token')).called(1);
          verify(mockAuthRepository.storeTokens('new_access_token', 'new_refresh_token', 7200)).called(1);
        },
      );

      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthError] when token refresh fails',
        build: () {
          when(
            mockAuthRepository.refreshEbayTokens('expired_refresh_token'),
          ).thenThrow(const ServerException('Refresh token expired'));
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthTokenRefreshRequested('test_user')),
        expect: () => [const AuthLoading(), const AuthError(message: 'Refresh token expired')],
        verify: (_) {
          verify(mockAuthRepository.refreshEbayTokens('expired_refresh_token')).called(1);
        },
      );
    });

    group('AuthStatusRequested', () {
      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthAuthenticated] when stored tokens are valid',
        build: () {
          final storedTokens = {
            'access_token': 'stored_access_token',
            'refresh_token': 'stored_refresh_token',
            'expires_at': DateTime.now().add(const Duration(hours: 1)).millisecondsSinceEpoch,
          };
          when(mockAuthRepository.getStoredTokens()).thenAnswer((_) async => storedTokens);
          when(mockAuthRepository.validateToken('stored_access_token')).thenAnswer((_) async => true);
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthStatusRequested()),
        expect: () => [
          const AuthLoading(),
          AuthAuthenticated(
            userId: 'test_user',
            environment: 'sandbox',
            tokenType: 'Bearer',
            expiresAt: DateTime.now().add(const Duration(hours: 1)),
            scopes: const ['https://api.ebay.com/oauth/api_scope'],
          ),
        ],
        verify: (_) {
          verify(mockAuthRepository.getStoredTokens()).called(1);
          verify(mockAuthRepository.validateToken('stored_access_token')).called(1);
        },
      );

      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthInitial] when no tokens are stored',
        build: () {
          when(mockAuthRepository.getStoredTokens()).thenAnswer((_) async => null);
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthStatusRequested()),
        expect: () => [const AuthLoading(), const AuthInitial()],
        verify: (_) {
          verify(mockAuthRepository.getStoredTokens()).called(1);
        },
      );

      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthInitial] when stored tokens are invalid',
        build: () {
          final storedTokens = {
            'access_token': 'invalid_access_token',
            'refresh_token': 'invalid_refresh_token',
            'expires_at': DateTime.now().add(const Duration(hours: 1)).millisecondsSinceEpoch,
          };
          when(mockAuthRepository.getStoredTokens()).thenAnswer((_) async => storedTokens);
          when(mockAuthRepository.validateToken('invalid_access_token')).thenAnswer((_) async => false);
          when(mockAuthRepository.clearTokens()).thenAnswer((_) async {});
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthStatusRequested()),
        expect: () => [const AuthLoading(), const AuthInitial()],
        verify: (_) {
          verify(mockAuthRepository.getStoredTokens()).called(1);
          verify(mockAuthRepository.validateToken('invalid_access_token')).called(1);
          verify(mockAuthRepository.clearTokens()).called(1);
        },
      );
    });

    group('AuthLogoutRequested', () {
      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthInitial] when logout is successful',
        build: () {
          when(mockAuthRepository.clearTokens()).thenAnswer((_) async {});
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthLogoutRequested()),
        expect: () => [const AuthLoading(), const AuthInitial()],
        verify: (_) {
          verify(mockAuthRepository.clearTokens()).called(1);
        },
      );

      blocTest<AuthBloc, AuthState>(
        'emits [AuthLoading, AuthError] when logout fails',
        build: () {
          when(mockAuthRepository.clearTokens()).thenThrow(Exception('Failed to clear tokens'));
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthLogoutRequested()),
        expect: () => [const AuthLoading(), const AuthError(message: 'Failed to clear tokens')],
        verify: (_) {
          verify(mockAuthRepository.clearTokens()).called(1);
        },
      );
    });

    group('Error Handling', () {
      blocTest<AuthBloc, AuthState>(
        'handles network errors gracefully',
        build: () {
          when(mockAuthRepository.getEbayOAuthUrl()).thenThrow(NetworkException('No internet connection'));
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthEbayLoginRequested('test_user')),
        expect: () => [const AuthLoading(), const AuthError(message: 'No internet connection')],
      );

      blocTest<AuthBloc, AuthState>(
        'handles server errors gracefully',
        build: () {
          when(mockAuthRepository.getEbayOAuthUrl()).thenThrow(ServerException('Server temporarily unavailable'));
          return authBloc;
        },
        act: (bloc) => bloc.add(const AuthEbayLoginRequested('test_user')),
        expect: () => [const AuthLoading(), const AuthError(message: 'Server temporarily unavailable')],
      );
    });
  });
}
