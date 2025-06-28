import 'package:flutter_test/flutter_test.dart';
import 'package:get_it/get_it.dart';
import 'package:flipsync/core/di/injection.dart' as di;
import 'package:flipsync/features/chat/presentation/bloc/chat_bloc.dart';
import 'package:flipsync/core/services/chat/chat_service.dart';
import 'package:flipsync/core/config/app_config.dart';
import 'package:flipsync/core/config/environment.dart' as env;

void main() {
  group('Dependency Injection Tests', () {
    setUp(() async {
      // Reset GetIt before each test
      GetIt.instance.reset();
    });

    test('should register ChatBloc successfully', () async {
      // Initialize AppConfig first
      AppConfig.initialize(
        environment: env.Environment.dev,
        apiBaseUrl: 'http://localhost:8001/api/v1',
        enableLogging: true,
      );

      // Configure dependencies
      await di.configureDependencies();

      // Check if ChatBloc is registered
      expect(GetIt.instance.isRegistered<ChatBloc>(), isTrue);

      // Try to get ChatBloc instance
      final chatBloc = GetIt.instance<ChatBloc>();
      expect(chatBloc, isNotNull);
      expect(chatBloc, isA<ChatBloc>());
    });

    test('should register ChatService successfully', () async {
      // Initialize AppConfig first
      AppConfig.initialize(
        environment: env.Environment.dev,
        apiBaseUrl: 'http://localhost:8001/api/v1',
        enableLogging: true,
      );

      // Configure dependencies
      await di.configureDependencies();

      // Check if ChatService is registered
      expect(GetIt.instance.isRegistered<ChatService>(), isTrue);

      // Try to get ChatService instance
      final chatService = GetIt.instance<ChatService>();
      expect(chatService, isNotNull);
      expect(chatService, isA<ChatService>());
    });

    test('should handle dependency chain correctly', () async {
      // Initialize AppConfig first
      AppConfig.initialize(
        environment: env.Environment.dev,
        apiBaseUrl: 'http://localhost:8001/api/v1',
        enableLogging: true,
      );

      // Configure dependencies
      await di.configureDependencies();

      // Check the entire dependency chain
      expect(GetIt.instance.isRegistered<ChatService>(), isTrue);
      expect(GetIt.instance.isRegistered<ChatBloc>(), isTrue);

      // Create ChatBloc and verify it has ChatService
      final chatBloc = GetIt.instance<ChatBloc>();
      expect(chatBloc, isNotNull);
    });
  });
}
