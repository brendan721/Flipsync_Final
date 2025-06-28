import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import '../lib/features/chat/models/chat_message.dart';

/// Demo widget to showcase Enhanced Unified Chat features
class EnhancedChatDemo extends StatelessWidget {
  const EnhancedChatDemo({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Enhanced Chat Demo',
      theme: ThemeData(primarySwatch: Colors.blue),
      home: const ChatDemoScreen(),
    );
  }
}

class ChatDemoScreen extends StatelessWidget {
  const ChatDemoScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Enhanced Unified Chat Demo'),
        backgroundColor: const Color(0xFF2563EB),
      ),
      body: Column(
        children: [
          // Demo Agent Indicators
          _buildAgentIndicatorDemo(),
          
          // Demo Quick Access Buttons
          _buildQuickAccessDemo(),
          
          // Demo Message Bubbles
          Expanded(child: _buildMessageDemo()),
        ],
      ),
    );
  }

  Widget _buildAgentIndicatorDemo() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Agent Indicators',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: [
              _buildDemoAgentIndicator('market'),
              _buildDemoAgentIndicator('content'),
              _buildDemoAgentIndicator('logistics'),
              _buildDemoAgentIndicator('executive'),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildDemoAgentIndicator(String agentType) {
    final config = _getAgentConfig(agentType);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: config['color'].withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: config['color'].withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            config['icon'],
            color: config['color'],
            size: 14,
          ),
          const SizedBox(width: 4),
          Text(
            config['name'],
            style: TextStyle(
              color: config['color'],
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuickAccessDemo() {
    return Container(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Quick Agent Access',
            style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                _buildDemoQuickAgentButton('market'),
                const SizedBox(width: 8),
                _buildDemoQuickAgentButton('content'),
                const SizedBox(width: 8),
                _buildDemoQuickAgentButton('logistics'),
                const SizedBox(width: 8),
                _buildDemoQuickAgentButton('executive'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDemoQuickAgentButton(String agentType) {
    final config = _getAgentConfig(agentType);
    final description = _getAgentDescription(agentType);
    
    return Container(
      width: 140,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: config['color'].withOpacity(0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: config['color'].withOpacity(0.3),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(
                config['emoji'],
                style: const TextStyle(fontSize: 16),
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  config['name'],
                  style: TextStyle(
                    color: config['color'],
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ),
          const SizedBox(height: 4),
          Text(
            description,
            style: TextStyle(
              color: config['color'].withOpacity(0.8),
              fontSize: 10,
              height: 1.2,
            ),
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
          ),
        ],
      ),
    );
  }

  Widget _buildMessageDemo() {
    final demoMessages = [
      ChatMessage.userText('Help me optimize my iPhone listing'),
      ChatMessage.agentText(
        'I\'ll connect you with our Market Agent for pricing analysis...',
        agentType: 'assistant',
      ),
      ChatMessage.agentText(
        'I\'ve analyzed your iPhone 13 listing. Your price (\$899) is 8% above market average. I recommend dropping to \$839 for 3x faster sales.',
        agentType: 'market',
      ),
      ChatMessage.userText('Can you also improve the description?'),
      ChatMessage.agentText(
        'I\'ll optimize your listing description with SEO keywords and mobile-friendly formatting for +15% engagement.',
        agentType: 'content',
      ),
    ];

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: demoMessages.length,
      itemBuilder: (context, index) {
        return _buildDemoMessageBubble(demoMessages[index]);
      },
    );
  }

  Widget _buildDemoMessageBubble(ChatMessage message) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Column(
        crossAxisAlignment: message.isUser ? CrossAxisAlignment.end : CrossAxisAlignment.start,
        children: [
          // Agent indicator for non-user messages
          if (!message.isUser && message.agentType != null)
            Padding(
              padding: const EdgeInsets.only(left: 48, bottom: 4),
              child: _buildDemoAgentIndicator(message.agentType!),
            ),
          
          Row(
            mainAxisAlignment: message.isUser ? MainAxisAlignment.end : MainAxisAlignment.start,
            children: [
              if (!message.isUser) ...[
                _buildDemoAgentAvatar(message.agentType),
                const SizedBox(width: 8),
              ],
              Flexible(
                child: Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: message.isUser ? const Color(0xFF2563EB) : Colors.white,
                    borderRadius: BorderRadius.circular(16),
                    boxShadow: [
                      BoxShadow(
                        color: Colors.black.withOpacity(0.05),
                        blurRadius: 5,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: Text(
                    message.content,
                    style: TextStyle(
                      color: message.isUser ? Colors.white : const Color(0xFF1F2937),
                      fontSize: 16,
                    ),
                  ),
                ),
              ),
              if (message.isUser) ...[
                const SizedBox(width: 8),
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: Colors.grey[300],
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Icon(
                    Icons.person,
                    color: Color(0xFF6B7280),
                    size: 16,
                  ),
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildDemoAgentAvatar(String? agentType) {
    final config = _getAgentConfig(agentType);
    return Container(
      padding: const EdgeInsets.all(8),
      decoration: BoxDecoration(
        color: config['color'],
        borderRadius: BorderRadius.circular(20),
      ),
      child: Icon(
        config['icon'],
        color: Colors.white,
        size: 16,
      ),
    );
  }

  Map<String, dynamic> _getAgentConfig(String? agentType) {
    switch (agentType?.toLowerCase()) {
      case 'market':
        return {
          'icon': Icons.store,
          'color': const Color(0xFF10B981),
          'name': 'Market Agent',
          'emoji': '🛒',
        };
      case 'content':
        return {
          'icon': Icons.edit,
          'color': const Color(0xFF3B82F6),
          'name': 'Content Agent',
          'emoji': '📝',
        };
      case 'logistics':
        return {
          'icon': Icons.local_shipping,
          'color': const Color(0xFFF59E0B),
          'name': 'Logistics Agent',
          'emoji': '🚚',
        };
      case 'executive':
        return {
          'icon': Icons.business,
          'color': const Color(0xFF8B5CF6),
          'name': 'Executive Agent',
          'emoji': '👔',
        };
      default:
        return {
          'icon': Icons.smart_toy,
          'color': const Color(0xFF2563EB),
          'name': 'FlipSync Assistant',
          'emoji': '🤖',
        };
    }
  }

  String _getAgentDescription(String agentType) {
    switch (agentType.toLowerCase()) {
      case 'market':
        return 'Pricing & Competition Analysis';
      case 'content':
        return 'SEO & Description Optimization';
      case 'logistics':
        return 'Shipping & Fulfillment';
      case 'executive':
        return 'Strategy & Coordination';
      default:
        return 'General AI Assistant';
    }
  }
}
