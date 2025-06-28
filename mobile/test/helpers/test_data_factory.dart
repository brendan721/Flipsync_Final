// Test data factory functions - no mocks, just test data creation
import 'package:flipsync/core/models/user.dart';
import 'package:flipsync/core/models/agent_type.dart';
import 'package:flipsync/features/agent_monitoring/models/agent_status.dart';
import 'package:flipsync/features/chat/models/chat_message.dart';

/// Create test user for testing
User createTestUser({
  String userId = 'test-user-id',
  String email = 'test@example.com',
  String displayName = 'Test User',
}) {
  return User(
    userId: userId,
    email: email,
    displayName: displayName,
    createdAt: DateTime.now(),
    lastUpdated: DateTime.now(),
    lastSynced: DateTime.now(),
  );
}

/// Create test agent status for testing
AgentStatus createTestAgentStatus({
  AgentType agentType = AgentType.market,
  bool isActive = true,
  String uptime = '2h 15m',
  int tasksCompleted = 5,
  String lastAction = 'Test action',
  int efficiency = 95,
}) {
  return AgentStatus(
    agentType: agentType,
    isActive: isActive,
    uptime: uptime,
    tasksCompleted: tasksCompleted,
    lastAction: lastAction,
    efficiency: efficiency,
  );
}

/// Create test chat message for testing
ChatMessage createTestChatMessage({
  String content = 'Test message',
  MessageSender sender = MessageSender.user,
  MessageType type = MessageType.text,
  DateTime? timestamp,
}) {
  return ChatMessage(
    content: content,
    sender: sender,
    type: type,
    timestamp: timestamp ?? DateTime.now(),
    id: 'test-message-id',
  );
}
