import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/features/communication/presentation/screens/conversation_screen.dart';
import 'package:flipsync/features/communication/models/conversation_models.dart';

/// End-to-End Integration Tests for FlipSync Communication System
/// Tests the complete conversation flow for both buyer and agent communication
void main() {
  group('Communication Integration Tests', () {
    late Conversation buyerConversation;
    late Conversation agentConversation;

    setUp(() {
      buyerConversation = Conversation(
        id: 'conv_buyer_test',
        title: 'iPhone 13 Pro Max Inquiry',
        type: ConversationType.buyerCommunication,
        participants: [
          ConversationParticipant(
            id: 'user_001',
            name: 'You',
            type: ConversationParticipantType.human,
          ),
          ConversationParticipant(
            id: 'buyer_test',
            name: 'test_buyer',
            type: ConversationParticipantType.buyer,
          ),
        ],
        createdAt: DateTime.now().subtract(Duration(hours: 1)),
        updatedAt: DateTime.now(),
      );

      agentConversation = Conversation(
        id: 'conv_agent_test',
        title: 'Market Agent Collaboration',
        type: ConversationType.agentCollaboration,
        participants: [
          ConversationParticipant(
            id: 'user_001',
            name: 'You',
            type: ConversationParticipantType.human,
          ),
          ConversationParticipant(
            id: 'market_agent',
            name: 'Market',
            type: ConversationParticipantType.marketAgent,
          ),
        ],
        createdAt: DateTime.now().subtract(Duration(hours: 2)),
        updatedAt: DateTime.now(),
      );
    });

    testWidgets('should display buyer conversation screen correctly', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: ConversationScreen(conversation: buyerConversation),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Buyer conversation elements
      expect(find.text('test_buyer'), findsOneWidget);
      expect(find.text('Buyer Communication'), findsOneWidget);
      expect(find.byIcon(Icons.person), findsAtLeastNWidgets(1));
      expect(find.text('Reply to buyer...'), findsOneWidget);
      expect(find.byIcon(Icons.auto_awesome), findsOneWidget); // Suggestions button
    });

    testWidgets('should display agent conversation screen correctly', (WidgetTester tester) async {
      // Arrange & Act
      await tester.pumpWidget(
        MaterialApp(
          home: ConversationScreen(conversation: agentConversation),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Agent conversation elements
      expect(find.text('Market Agent'), findsOneWidget);
      expect(find.text('Agent Collaboration'), findsOneWidget);
      expect(find.byIcon(Icons.psychology), findsAtLeastNWidgets(1));
      expect(find.text('Collaborate with your agent...'), findsOneWidget);
      expect(find.byIcon(Icons.insights), findsOneWidget); // Insights button
    });

    testWidgets('should send message in buyer conversation', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: ConversationScreen(conversation: buyerConversation),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Type and send message
      await tester.enterText(find.byType(TextField), 'Test message to buyer');
      await tester.tap(find.byIcon(Icons.send));
      await tester.pumpAndSettle();

      // Assert - Message should be sent (input cleared)
      expect(find.text('Test message to buyer'), findsNothing); // Input cleared
    });

    testWidgets('should send message in agent conversation', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: ConversationScreen(conversation: agentConversation),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Type and send message
      await tester.enterText(find.byType(TextField), 'Test collaboration message');
      await tester.tap(find.byIcon(Icons.send));
      await tester.pumpAndSettle();

      // Assert - Message should be sent (input cleared)
      expect(find.text('Test collaboration message'), findsNothing); // Input cleared
    });

    testWidgets('should toggle suggested responses in buyer conversation', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: ConversationScreen(conversation: buyerConversation),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Toggle suggestions
      await tester.tap(find.byIcon(Icons.auto_awesome));
      await tester.pumpAndSettle();

      // Assert - Suggestions should be visible
      expect(find.text('Suggested Responses'), findsOneWidget);

      // Act - Toggle again to hide
      await tester.tap(find.byIcon(Icons.auto_awesome));
      await tester.pumpAndSettle();

      // Assert - Suggestions should be hidden
      expect(find.text('Suggested Responses'), findsNothing);
    });

    testWidgets('should display agent collaboration tools', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: ConversationScreen(conversation: agentConversation),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Agent collaboration tools should be visible
      expect(find.text('Collaborating with Market Agent'), findsOneWidget);
      expect(find.text('Active'), findsOneWidget); // Agent status
      
      // Should have quick action buttons
      expect(find.text('Price Analysis'), findsOneWidget);
      expect(find.text('Competitor Check'), findsOneWidget);
    });

    testWidgets('should handle quick action in agent conversation', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: ConversationScreen(conversation: agentConversation),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Tap a quick action
      await tester.tap(find.text('Price Analysis'));
      await tester.pumpAndSettle();

      // Assert - Should populate message input
      final textField = tester.widget<TextField>(find.byType(TextField));
      expect(textField.controller?.text, contains('price'));
    });

    testWidgets('should handle message submission via Enter key', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: ConversationScreen(conversation: buyerConversation),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Type message and press Enter
      await tester.enterText(find.byType(TextField), 'Test Enter key submission');
      await tester.testTextInput.receiveAction(TextInputAction.done);
      await tester.pumpAndSettle();

      // Assert - Message should be sent
      expect(find.text('Test Enter key submission'), findsNothing); // Input cleared
    });

    testWidgets('should display conversation history', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: ConversationScreen(conversation: buyerConversation),
        ),
      );
      await tester.pumpAndSettle();

      // Assert - Should display message list (even if empty initially)
      expect(find.byType(ListView), findsOneWidget);
    });

    testWidgets('should handle back navigation', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: ConversationScreen(conversation: buyerConversation),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Tap back button
      await tester.tap(find.byIcon(Icons.arrow_back));
      await tester.pumpAndSettle();

      // Assert - Should navigate back (in real app, would go to dashboard)
      // In test, just verify the tap was handled
      expect(find.byType(ConversationScreen), findsNothing);
    });

    testWidgets('should handle empty message submission', (WidgetTester tester) async {
      // Arrange
      await tester.pumpWidget(
        MaterialApp(
          home: ConversationScreen(conversation: buyerConversation),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Try to send empty message
      await tester.tap(find.byIcon(Icons.send));
      await tester.pumpAndSettle();

      // Assert - Should not crash or show error
      expect(find.byType(ConversationScreen), findsOneWidget);
    });
  });

  group('Communication Error Handling', () {
    testWidgets('should handle message sending errors gracefully', (WidgetTester tester) async {
      // Arrange
      final conversation = Conversation(
        id: 'conv_error_test',
        title: 'Error Test Conversation',
        type: ConversationType.buyerCommunication,
        participants: [
          ConversationParticipant(
            id: 'user_001',
            name: 'You',
            type: ConversationParticipantType.human,
          ),
          ConversationParticipant(
            id: 'buyer_error',
            name: 'error_buyer',
            type: ConversationParticipantType.buyer,
          ),
        ],
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      await tester.pumpWidget(
        MaterialApp(
          home: ConversationScreen(conversation: conversation),
        ),
      );
      await tester.pumpAndSettle();

      // Act - Try to send message (might fail in mock service)
      await tester.enterText(find.byType(TextField), 'Test error handling');
      await tester.tap(find.byIcon(Icons.send));
      await tester.pumpAndSettle();

      // Assert - Should handle error gracefully
      expect(find.byType(ConversationScreen), findsOneWidget);
    });

    testWidgets('should handle loading states', (WidgetTester tester) async {
      // Arrange
      final conversation = Conversation(
        id: 'conv_loading_test',
        title: 'Loading Test Conversation',
        type: ConversationType.agentCollaboration,
        participants: [
          ConversationParticipant(
            id: 'user_001',
            name: 'You',
            type: ConversationParticipantType.human,
          ),
          ConversationParticipant(
            id: 'agent_loading',
            name: 'Loading Agent',
            type: ConversationParticipantType.marketAgent,
          ),
        ],
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      // Act
      await tester.pumpWidget(
        MaterialApp(
          home: ConversationScreen(conversation: conversation),
        ),
      );

      // Assert - Should show loading initially, then content
      await tester.pumpAndSettle();
      expect(find.byType(ConversationScreen), findsOneWidget);
    });
  });

  group('Communication Performance', () {
    testWidgets('should render conversation screen within performance limits', (WidgetTester tester) async {
      // Arrange
      final stopwatch = Stopwatch()..start();
      final conversation = Conversation(
        id: 'conv_perf_test',
        title: 'Performance Test Conversation',
        type: ConversationType.buyerCommunication,
        participants: [
          ConversationParticipant(
            id: 'user_001',
            name: 'You',
            type: ConversationParticipantType.human,
          ),
          ConversationParticipant(
            id: 'buyer_perf',
            name: 'perf_buyer',
            type: ConversationParticipantType.buyer,
          ),
        ],
        createdAt: DateTime.now(),
        updatedAt: DateTime.now(),
      );

      // Act
      await tester.pumpWidget(
        MaterialApp(
          home: ConversationScreen(conversation: conversation),
        ),
      );
      await tester.pumpAndSettle();

      stopwatch.stop();

      // Assert - Should render within reasonable time
      expect(stopwatch.elapsedMilliseconds, lessThan(3000));
      expect(find.byType(ConversationScreen), findsOneWidget);
    });
  });
}
