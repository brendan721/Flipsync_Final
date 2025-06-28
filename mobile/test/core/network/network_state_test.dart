import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/core/network/network_state.dart';

void main() {
  late NetworkState networkState;

  setUp(() {
    networkState = NetworkState();
  });

  tearDown(() {
    networkState.dispose();
  });

  group('NetworkState', () {
    test('initial state is online with no errors', () {
      expect(networkState.isOnline, isTrue);
      expect(networkState.error, isNull);
      expect(networkState.isLoading, isFalse);
    });

    test('setOnline updates state correctly', () {
      var notified = false;
      networkState.addListener(() => notified = true);

      networkState.setOffline();
      networkState.setError(NetworkError('Test error'));

      expect(notified, isTrue);
      notified = false;

      networkState.setOnline();

      expect(networkState.isOnline, isTrue);
      expect(networkState.error, isNull);
      expect(notified, isTrue);
    });

    test('setOffline updates state correctly', () {
      var notified = false;
      networkState.addListener(() => notified = true);

      networkState.setOffline();

      expect(networkState.isOnline, isFalse);
      expect(notified, isTrue);
    });

    test('setError updates error state correctly', () {
      var notified = false;
      networkState.addListener(() => notified = true);

      final timeoutError = NetworkError('Connection timeout');
      networkState.setError(timeoutError);

      expect(networkState.error, equals(timeoutError));
      expect(notified, isTrue);
    });

    test('clearError removes error state', () {
      var notified = false;
      networkState.addListener(() => notified = true);

      networkState.setError(NetworkError('Test error'));
      notified = false;

      networkState.clearError();

      expect(networkState.error, isNull);
      expect(notified, isTrue);
    });

    test('setLoading updates loading state correctly', () {
      var notified = false;
      networkState.addListener(() => notified = true);

      expect(networkState.isLoading, isFalse);

      networkState.setLoading(true);
      expect(networkState.isLoading, isTrue);
      expect(notified, isTrue);

      notified = false;
      networkState.setLoading(false);
      expect(networkState.isLoading, isFalse);
      expect(notified, isTrue);
    });

    test('multiple state changes notify listeners correctly', () {
      var notificationCount = 0;
      networkState.addListener(() => notificationCount++);

      networkState.setOffline();
      networkState.setError(NetworkError('Test error'));
      networkState.setLoading(true);
      networkState.setOnline();
      networkState.clearError();
      networkState.setLoading(false);

      expect(notificationCount, equals(6));
    });

    test('NetworkError toString returns message', () {
      final error = NetworkError('Test error message');
      expect(error.toString(), equals('Test error message'));
    });

    test('NetworkError with stack trace stores information correctly', () {
      final stackTrace = StackTrace.current;
      final error = NetworkError(
        'Test error',
        error: Exception('Original error'),
        stackTrace: stackTrace,
      );

      expect(error.message, equals('Test error'));
      expect(error.error, isA<Exception>());
      expect(error.stackTrace, equals(stackTrace));
    });
  });

  group('Network Error Handling', () {
    test('handles connection timeout errors', () {
      final timeoutError = NetworkError('Connection timeout');
      networkState.setError(timeoutError);
      networkState.setOffline();

      expect(networkState.error?.message, equals('Connection timeout'));
      expect(networkState.isOnline, isFalse);
    });

    test('handles server errors', () {
      final serverError = NetworkError('Internal server error');
      networkState.setError(serverError);

      expect(networkState.error?.message, equals('Internal server error'));
      expect(networkState.isOnline,
          isTrue); // Server errors don't affect online status
    });

    test('handles authentication errors', () {
      final authError = NetworkError('Authentication failed');
      networkState.setError(authError);

      expect(networkState.error?.message, equals('Authentication failed'));
      expect(networkState.isOnline, isTrue);
    });

    test('handles connection errors', () {
      final connectionError = NetworkError('No internet connection');
      networkState.setError(connectionError);

      expect(networkState.error?.message, equals('No internet connection'));
      expect(networkState.isOnline, isFalse);
    });

    test('error state is preserved until cleared', () {
      final error = NetworkError('Test error');
      networkState.setError(error);

      expect(networkState.error, isNotNull);
      networkState.setLoading(true);
      expect(networkState.error,
          isNotNull); // Error persists through loading state
      networkState.setLoading(false);
      expect(networkState.error, isNotNull);

      networkState.clearError();
      expect(networkState.error, isNull);
    });

    test('multiple errors are handled sequentially', () {
      final error1 = NetworkError('First error');
      final error2 = NetworkError('Second error');

      networkState.setError(error1);
      expect(networkState.error?.message, equals('First error'));

      networkState.setError(error2);
      expect(networkState.error?.message, equals('Second error'));
    });
  });
}
