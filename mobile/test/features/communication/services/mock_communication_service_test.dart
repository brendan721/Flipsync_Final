import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/features/communication/services/mock_communication_service.dart';
import 'package:flipsync/features/communication/models/conversation_models.dart';

void main() {
  group('MockCommunicationService', () {
    late MockCommunicationService service;

    setUp(() {
      service = MockCommunicationService();
    });

    tearDown(() {
      service.dispose();
    });

    group('getConversations', () {
      test('should return list of conversations', () async {
        final conversations = await service.getConversations();
        
        expect(conversations, isA<List<Conversation>>());
        expect(conversations.isNotEmpty, true);
      });

      test('should include both buyer and agent conversations', () async {
        final conversations = await service.getConversations();
        
        final buyerConversations = conversations
            .where((c) => c.type == ConversationType.buyerCommunication)
            .toList();
        final agentConversations = conversations
            .where((c) => c.type == ConversationType.agentCollaboration)
            .toList();
        
        expect(buyerConversations.isNotEmpty, true);
        expect(agentConversations.isNotEmpty, true);
      });

      test('should have realistic conversation data', () async {
        final conversations = await service.getConversations();
        final firstConversation = conversations.first;
        
        expect(firstConversation.id.isNotEmpty, true);
        expect(firstConversation.title.isNotEmpty, true);
        expect(firstConversation.participants.isNotEmpty, true);
        expect(firstConversation.createdAt.isBefore(DateTime.now()), true);
      });
    });

    group('getMessages', () {
      test('should return empty list for non-existent conversation', () async {
        final messages = await service.getMessages('non_existent_id');
        
        expect(messages, isEmpty);
      });

      test('should return messages sorted by timestamp', () async {
        // First get a conversation ID
        final conversations = await service.getConversations();
        final conversationId = conversations.first.id;
        
        final messages = await service.getMessages(conversationId);
        
        // Check if messages are sorted by timestamp
        for (int i = 1; i < messages.length; i++) {
          expect(
            messages[i].timestamp.isAfter(messages[i - 1].timestamp) ||
            messages[i].timestamp.isAtSameMomentAs(messages[i - 1].timestamp),
            true,
          );
        }
      });
    });

    group('sendMessage', () {
      test('should create and return new message', () async {
        final conversations = await service.getConversations();
        final conversationId = conversations.first.id;
        const messageContent = 'Test message';
        
        final message = await service.sendMessage(
          conversationId: conversationId,
          content: messageContent,
        );
        
        expect(message.conversationId, conversationId);
        expect(message.content, messageContent);
        expect(message.senderId, 'user_001');
        expect(message.type, MessageType.text);
        expect(message.status, MessageStatus.sent);
      });

      test('should update conversation last message', () async {
        final conversations = await service.getConversations();
        final conversationId = conversations.first.id;
        const messageContent = 'Test message for last message update';
        
        await service.sendMessage(
          conversationId: conversationId,
          content: messageContent,
        );
        
        final updatedConversations = await service.getConversations();
        final updatedConversation = updatedConversations
            .firstWhere((c) => c.id == conversationId);
        
        expect(updatedConversation.lastMessage?.content, messageContent);
      });

      test('should handle empty message content', () async {
        final conversations = await service.getConversations();
        final conversationId = conversations.first.id;
        
        final message = await service.sendMessage(
          conversationId: conversationId,
          content: '',
        );
        
        expect(message.content, '');
      });
    });

    group('getSuggestedResponses', () {
      test('should return list of suggested responses', () async {
        final conversations = await service.getConversations();
        final conversationId = conversations.first.id;
        
        final suggestions = await service.getSuggestedResponses(conversationId);
        
        expect(suggestions, isA<List<SuggestedResponse>>());
        expect(suggestions.isNotEmpty, true);
      });

      test('should have realistic suggestion data', () async {
        final conversations = await service.getConversations();
        final conversationId = conversations.first.id;
        
        final suggestions = await service.getSuggestedResponses(conversationId);
        final firstSuggestion = suggestions.first;
        
        expect(firstSuggestion.id.isNotEmpty, true);
        expect(firstSuggestion.content.isNotEmpty, true);
        expect(firstSuggestion.confidence, greaterThan(0.0));
        expect(firstSuggestion.confidence, lessThanOrEqualTo(1.0));
        expect(firstSuggestion.reasoning.isNotEmpty, true);
      });

      test('should have high confidence suggestions', () async {
        final conversations = await service.getConversations();
        final conversationId = conversations.first.id;
        
        final suggestions = await service.getSuggestedResponses(conversationId);
        
        // At least one suggestion should have high confidence
        final hasHighConfidence = suggestions
            .any((s) => s.confidence >= 0.8);
        
        expect(hasHighConfidence, true);
      });
    });

    group('getAgentInsights', () {
      test('should return list of agent insights', () async {
        final insights = await service.getAgentInsights();
        
        expect(insights, isA<List<AgentInsight>>());
        expect(insights.isNotEmpty, true);
      });

      test('should have realistic insight data', () async {
        final insights = await service.getAgentInsights();
        final firstInsight = insights.first;
        
        expect(firstInsight.id.isNotEmpty, true);
        expect(firstInsight.agentId.isNotEmpty, true);
        expect(firstInsight.agentType.isNotEmpty, true);
        expect(firstInsight.title.isNotEmpty, true);
        expect(firstInsight.description.isNotEmpty, true);
        expect(firstInsight.createdAt.isBefore(DateTime.now()), true);
      });

      test('should include insights with different priorities', () async {
        final insights = await service.getAgentInsights();
        
        final priorities = insights.map((i) => i.priority).toSet();
        
        // Should have multiple priority levels
        expect(priorities.length, greaterThan(1));
      });

      test('should include insights from different agent types', () async {
        final insights = await service.getAgentInsights();
        
        final agentTypes = insights.map((i) => i.agentType).toSet();
        
        // Should have insights from different agents
        expect(agentTypes.length, greaterThan(1));
      });
    });

    group('streams', () {
      test('should emit initial conversations on stream', () async {
        final stream = service.conversationsStream;
        
        final conversations = await stream.first;
        
        expect(conversations, isA<List<Conversation>>());
        expect(conversations.isNotEmpty, true);
      });

      test('should emit updated conversations after sending message', () async {
        final stream = service.conversationsStream;
        final conversations = await service.getConversations();
        final conversationId = conversations.first.id;
        
        // Skip initial emission
        await stream.first;
        
        // Send message and wait for stream update
        await service.sendMessage(
          conversationId: conversationId,
          content: 'Stream test message',
        );
        
        final updatedConversations = await stream.first;
        final updatedConversation = updatedConversations
            .firstWhere((c) => c.id == conversationId);
        
        expect(updatedConversation.lastMessage?.content, 'Stream test message');
      });

      test('should emit messages on messages stream', () async {
        final stream = service.messagesStream;
        
        final messages = await stream.first;
        
        expect(messages, isA<List<ConversationMessage>>());
      });
    });

    group('error handling', () {
      test('should handle network delays gracefully', () async {
        final stopwatch = Stopwatch()..start();
        
        await service.getConversations();
        
        stopwatch.stop();
        
        // Should simulate network delay (at least 100ms)
        expect(stopwatch.elapsedMilliseconds, greaterThanOrEqualTo(100));
      });

      test('should handle concurrent requests', () async {
        final futures = List.generate(5, (_) => service.getConversations());
        
        final results = await Future.wait(futures);
        
        // All requests should succeed
        expect(results.length, 5);
        for (final result in results) {
          expect(result, isA<List<Conversation>>());
        }
      });
    });
  });
}
