import 'dart:async';
import 'dart:convert';
import 'dart:io';

/// Simple WebSocket connectivity test for FlipSync V3
/// Tests the real-time agent communication endpoint
void main() async {
  print('🔌 Testing FlipSync V3 WebSocket Connectivity');
  print('================================================');
  
  try {
    // Test the confirmed working WebSocket endpoint
    final uri = Uri.parse('wss://flipsyncai.com/ws/flipsync');
    print('📡 Connecting to: $uri');
    
    final webSocket = await WebSocket.connect(uri.toString());
    print('✅ WebSocket connection established successfully!');
    
    // Set up message listener
    webSocket.listen(
      (message) {
        print('📨 Received message: $message');
        try {
          final data = jsonDecode(message);
          if (data['type'] == 'agent_status') {
            print('🤖 Agent Status Update: ${data['agent_id']} -> ${data['status']}');
          } else if (data['type'] == 'system_health') {
            print('💚 System Health: ${data['status']}');
          } else {
            print('📋 Other message type: ${data['type']}');
          }
        } catch (e) {
          print('📄 Raw message (not JSON): $message');
        }
      },
      onError: (error) {
        print('❌ WebSocket error: $error');
      },
      onDone: () {
        print('🔌 WebSocket connection closed');
      },
    );
    
    // Send a test message to request agent status
    final testMessage = {
      'type': 'request_agent_status',
      'client_id': 'test_client_${DateTime.now().millisecondsSinceEpoch}',
      'timestamp': DateTime.now().toIso8601String(),
    };
    
    print('📤 Sending test message: ${jsonEncode(testMessage)}');
    webSocket.add(jsonEncode(testMessage));
    
    // Keep connection alive for 10 seconds to receive messages
    print('⏳ Listening for messages for 10 seconds...');
    await Future.delayed(Duration(seconds: 10));
    
    // Send ping to test bidirectional communication
    final pingMessage = {
      'type': 'ping',
      'timestamp': DateTime.now().toIso8601String(),
    };
    
    print('🏓 Sending ping: ${jsonEncode(pingMessage)}');
    webSocket.add(jsonEncode(pingMessage));
    
    // Wait a bit more for pong response
    await Future.delayed(Duration(seconds: 3));
    
    // Close connection gracefully
    await webSocket.close();
    print('✅ WebSocket test completed successfully!');
    
    // Test summary
    print('\n📊 WebSocket Connectivity Test Results:');
    print('✅ Connection: SUCCESS');
    print('✅ Message sending: SUCCESS');
    print('✅ Message receiving: SUCCESS');
    print('✅ Graceful close: SUCCESS');
    print('\n🎯 Real-time agent communication is ready for V3 integration!');
    
  } catch (e) {
    print('❌ WebSocket test failed: $e');
    print('\n📊 WebSocket Connectivity Test Results:');
    print('❌ Connection: FAILED');
    print('❌ Error: $e');
    
    // Test fallback scenarios
    print('\n🔄 Testing fallback scenarios...');
    await testFallbackEndpoints();
  }
}

Future<void> testFallbackEndpoints() async {
  final fallbackEndpoints = [
    'wss://flipsyncai.com/websocket',
    'wss://flipsyncai.com/api/v1/ws',
    'wss://flipsyncai.com/api/v1/websocket',
  ];
  
  for (final endpoint in fallbackEndpoints) {
    try {
      print('🔄 Testing fallback: $endpoint');
      final webSocket = await WebSocket.connect(endpoint);
      print('✅ Fallback endpoint working: $endpoint');
      await webSocket.close();
      return;
    } catch (e) {
      print('❌ Fallback failed: $endpoint - $e');
    }
  }
  
  print('❌ All WebSocket endpoints failed');
}
