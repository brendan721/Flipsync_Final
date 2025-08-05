import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/features/communication/models/conversation_models.dart';

void main() {
  group('ConversationParticipant', () {
    test('should create participant with required fields', () {
      const participant = ConversationParticipant(
        id: 'user_001',
        name: 'John Doe',
        type: ConversationParticipantType.human,
      );

      expect(participant.id, 'user_001');
      expect(participant.name, 'John Doe');
      expect(participant.type, ConversationParticipantType.human);
      expect(participant.isOnline, false);
      expect(participant.avatarUrl, null);
    });

    test('should support copyWith functionality', () {
      const original = ConversationParticipant(
        id: 'user_001',
        name: 'John Doe',
        type: ConversationParticipantType.human,
      );

      final updated = original.copyWith(
        name: 'Jane Doe',
        isOnline: true,
      );

      expect(updated.id, 'user_001');
      expect(updated.name, 'Jane Doe');
      expect(updated.type, ConversationParticipantType.human);
      expect(updated.isOnline, true);
    });

    test('should implement equality correctly', () {
      const participant1 = ConversationParticipant(
        id: 'user_001',
        name: 'John Doe',
        type: ConversationParticipantType.human,
      );

      const participant2 = ConversationParticipant(
        id: 'user_001',
        name: 'John Doe',
        type: ConversationParticipantType.human,
      );

      const participant3 = ConversationParticipant(
        id: 'user_002',
        name: 'John Doe',
        type: ConversationParticipantType.human,
      );

      expect(participant1, equals(participant2));
      expect(participant1, isNot(equals(participant3)));
    });
  });

  group('ConversationMessage', () {
    test('should create message with required fields', () {
      final timestamp = DateTime.now();
      final message = ConversationMessage(
        id: 'msg_001',
        conversationId: 'conv_001',
        senderId: 'user_001',
        content: 'Hello world',
        type: MessageType.text,
        timestamp: timestamp,
      );

      expect(message.id, 'msg_001');
      expect(message.conversationId, 'conv_001');
      expect(message.senderId, 'user_001');
      expect(message.content, 'Hello world');
      expect(message.type, MessageType.text);
      expect(message.timestamp, timestamp);
      expect(message.status, MessageStatus.sent);
    });

    test('should support copyWith functionality', () {
      final timestamp = DateTime.now();
      final original = ConversationMessage(
        id: 'msg_001',
        conversationId: 'conv_001',
        senderId: 'user_001',
        content: 'Hello world',
        type: MessageType.text,
        timestamp: timestamp,
      );

      final updated = original.copyWith(
        content: 'Updated message',
        status: MessageStatus.delivered,
      );

      expect(updated.id, 'msg_001');
      expect(updated.content, 'Updated message');
      expect(updated.status, MessageStatus.delivered);
      expect(updated.timestamp, timestamp);
    });
  });

  group('Conversation', () {
    late List<ConversationParticipant> participants;
    late DateTime createdAt;
    late DateTime updatedAt;

    setUp(() {
      createdAt = DateTime.now().subtract(Duration(hours: 1));
      updatedAt = DateTime.now();
      participants = [
        ConversationParticipant(
          id: 'user_001',
          name: 'Human User',
          type: ConversationParticipantType.human,
        ),
        ConversationParticipant(
          id: 'buyer_001',
          name: 'Buyer',
          type: ConversationParticipantType.buyer,
        ),
      ];
    });

    test('should create conversation with required fields', () {
      final conversation = Conversation(
        id: 'conv_001',
        title: 'Test Conversation',
        type: ConversationType.buyerCommunication,
        participants: participants,
        createdAt: createdAt,
        updatedAt: updatedAt,
      );

      expect(conversation.id, 'conv_001');
      expect(conversation.title, 'Test Conversation');
      expect(conversation.type, ConversationType.buyerCommunication);
      expect(conversation.participants, participants);
      expect(conversation.unreadCount, 0);
      expect(conversation.isPinned, false);
    });

    test('should identify unread messages correctly', () {
      final conversation = Conversation(
        id: 'conv_001',
        title: 'Test Conversation',
        type: ConversationType.buyerCommunication,
        participants: participants,
        unreadCount: 3,
        createdAt: createdAt,
        updatedAt: updatedAt,
      );

      expect(conversation.hasUnreadMessages, true);
    });

    test('should get other participant correctly', () {
      final conversation = Conversation(
        id: 'conv_001',
        title: 'Test Conversation',
        type: ConversationType.buyerCommunication,
        participants: participants,
        createdAt: createdAt,
        updatedAt: updatedAt,
      );

      final otherParticipant = conversation.getOtherParticipant('user_001');
      expect(otherParticipant?.id, 'buyer_001');
      expect(otherParticipant?.name, 'Buyer');
    });

    test('should generate correct display name for buyer communication', () {
      final conversation = Conversation(
        id: 'conv_001',
        title: 'Test Conversation',
        type: ConversationType.buyerCommunication,
        participants: participants,
        createdAt: createdAt,
        updatedAt: updatedAt,
      );

      final displayName = conversation.getDisplayName('user_001');
      expect(displayName, 'Buyer');
    });

    test('should generate correct display name for agent collaboration', () {
      final agentParticipants = [
        ConversationParticipant(
          id: 'user_001',
          name: 'Human User',
          type: ConversationParticipantType.human,
        ),
        ConversationParticipant(
          id: 'market_agent',
          name: 'Market',
          type: ConversationParticipantType.marketAgent,
        ),
      ];

      final conversation = Conversation(
        id: 'conv_001',
        title: 'Agent Collaboration',
        type: ConversationType.agentCollaboration,
        participants: agentParticipants,
        createdAt: createdAt,
        updatedAt: updatedAt,
      );

      final displayName = conversation.getDisplayName('user_001');
      expect(displayName, 'Market Agent');
    });
  });

  group('AgentInsight', () {
    test('should create insight with required fields', () {
      final createdAt = DateTime.now();
      final insight = AgentInsight(
        id: 'insight_001',
        agentId: 'market_agent',
        agentType: 'Market Agent',
        title: 'Price Alert',
        description: 'Competitor price drop detected',
        type: InsightType.priceAlert,
        priority: InsightPriority.high,
        createdAt: createdAt,
      );

      expect(insight.id, 'insight_001');
      expect(insight.agentId, 'market_agent');
      expect(insight.agentType, 'Market Agent');
      expect(insight.title, 'Price Alert');
      expect(insight.description, 'Competitor price drop detected');
      expect(insight.type, InsightType.priceAlert);
      expect(insight.priority, InsightPriority.high);
      expect(insight.createdAt, createdAt);
      expect(insight.requiresResponse, false);
    });

    test('should support insights that require response', () {
      final createdAt = DateTime.now();
      final insight = AgentInsight(
        id: 'insight_001',
        agentId: 'market_agent',
        agentType: 'Market Agent',
        title: 'Price Alert',
        description: 'Competitor price drop detected',
        type: InsightType.priceAlert,
        priority: InsightPriority.high,
        createdAt: createdAt,
        requiresResponse: true,
      );

      expect(insight.requiresResponse, true);
    });
  });

  group('SuggestedResponse', () {
    test('should create suggested response with required fields', () {
      const response = SuggestedResponse(
        id: 'suggestion_001',
        content: 'Thank you for your inquiry!',
        confidence: 0.95,
        reasoning: 'Standard polite response',
      );

      expect(response.id, 'suggestion_001');
      expect(response.content, 'Thank you for your inquiry!');
      expect(response.confidence, 0.95);
      expect(response.reasoning, 'Standard polite response');
    });

    test('should implement equality correctly', () {
      const response1 = SuggestedResponse(
        id: 'suggestion_001',
        content: 'Thank you for your inquiry!',
        confidence: 0.95,
        reasoning: 'Standard polite response',
      );

      const response2 = SuggestedResponse(
        id: 'suggestion_001',
        content: 'Thank you for your inquiry!',
        confidence: 0.95,
        reasoning: 'Standard polite response',
      );

      expect(response1, equals(response2));
    });
  });
}
