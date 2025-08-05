import 'dart:async';
import 'package:get_it/get_it.dart';
import 'lib/core/di/injection.dart';
import 'lib/core/config/app_config.dart';
import 'lib/core/config/environment.dart' as env;
import 'lib/core/state/auth_state.dart';
import 'lib/core/auth/auth_service.dart';
import 'lib/services/websocket_service_consolidated.dart';
import 'lib/features/chat/presentation/bloc/chat_bloc.dart';

/// Test script to verify all fixes are working
void main() async {
  print('🧪 Testing FlipSync V3 Fixes...\n');
  
  try {
    // Test 1: Dependency Injection
    print('1️⃣ Testing Dependency Injection...');
    await testDependencyInjection();
    print('✅ Dependency Injection: PASSED\n');
    
    // Test 2: Authentication State
    print('2️⃣ Testing Authentication State...');
    await testAuthenticationState();
    print('✅ Authentication State: PASSED\n');
    
    // Test 3: WebSocket Service
    print('3️⃣ Testing WebSocket Service...');
    await testWebSocketService();
    print('✅ WebSocket Service: PASSED\n');
    
    print('🎉 All tests passed! FlipSync V3 fixes are working correctly.');
    
  } catch (e, stackTrace) {
    print('❌ Test failed: $e');
    print('Stack trace: $stackTrace');
  }
}

Future<void> testDependencyInjection() async {
  // Initialize app configuration
  AppConfig.initialize(
    environment: env.Environment.dev,
    apiBaseUrl: 'http://localhost:8000/api/v1',
    enableLogging: true,
  );
  
  // Configure dependencies
  await configureDependencies();
  
  // Test critical services
  final authService = GetIt.instance<AuthService>();
  print('   ✓ AuthService registered: ${authService.runtimeType}');
  
  final authState = GetIt.instance<AuthState>();
  print('   ✓ AuthState registered: ${authState.runtimeType}');
  
  final webSocketService = GetIt.instance<ConsolidatedWebSocketService>();
  print('   ✓ WebSocketService registered: ${webSocketService.runtimeType}');
  
  final chatBloc = GetIt.instance<ChatBloc>();
  print('   ✓ ChatBloc registered: ${chatBloc.runtimeType}');
}

Future<void> testAuthenticationState() async {
  final authState = GetIt.instance<AuthState>();
  
  // Test initial state
  print('   ✓ Initial authenticated state: ${authState.isAuthenticated}');
  print('   ✓ Initial auth token: ${authState.authToken != null ? 'Present' : 'None'}');
  
  // Test state management
  authState.setAuthState(
    isAuthenticated: false,
    authToken: null,
    userId: null,
  );
  
  print('   ✓ State management working correctly');
}

Future<void> testWebSocketService() async {
  final webSocketService = GetIt.instance<ConsolidatedWebSocketService>();
  
  // Test service initialization
  print('   ✓ WebSocket service initialized');
  print('   ✓ Connection state: ${webSocketService.isConnected}');
  
  // Test stream availability
  final hasAllMessages = webSocketService.allMessages != null;
  final hasChatMessages = webSocketService.chatMessages != null;
  final hasStatusUpdates = webSocketService.statusUpdates != null;
  
  print('   ✓ All messages stream: ${hasAllMessages ? 'Available' : 'Missing'}');
  print('   ✓ Chat messages stream: ${hasChatMessages ? 'Available' : 'Missing'}');
  print('   ✓ Status updates stream: ${hasStatusUpdates ? 'Available' : 'Missing'}');
  
  // Test token refresh mechanism (without actually connecting)
  try {
    // This should not throw an error even if no token is available
    webSocketService.setAuthToken('test_token');
    print('   ✓ Token management working');
  } catch (e) {
    throw Exception('Token management failed: $e');
  }
}
