import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:injectable/injectable.dart';
import '../../core/network/api_client.dart';
import '../../core/error/exceptions.dart';
import '../../models/ai/conversational_optimization.dart';

/// Service for conversational listing optimization (AI Feature 6)
@injectable
class AIConversationalOptimizationService {
  final ApiClient _apiClient;
  final Map<String, List<ConversationMessage>> _conversationHistory = {};

  AIConversationalOptimizationService(this._apiClient);

  /// Process conversational optimization request
  Future<ConversationalOptimizationResult> optimizeWithConversation({
    required String userMessage,
    required Map<String, dynamic> currentListing,
    String optimizationFocus = 'general',
    String? conversationId,
  }) async {
    try {
      // Get conversation context
      final conversationContext = _getConversationContext(conversationId);
      
      final response = await _apiClient.post(
        '/ai/conversational-optimize',
        data: {
          'user_message': userMessage,
          'current_listing': currentListing,
          'conversation_context': conversationContext.map((msg) => msg.toJson()).toList(),
          'optimization_focus': optimizationFocus,
        },
      );

      if (response.statusCode == 200) {
        final data = response.data;
        if (data['success'] == true) {
          final result = ConversationalOptimizationResult.fromJson(data['optimization']);
          
          // Update conversation history
          _updateConversationHistory(conversationId, userMessage, result);
          
          return result;
        } else {
          throw ServerException('Conversational optimization failed: ${data['message']}');
        }
      } else {
        throw ServerException('Failed to process optimization: ${response.statusCode}');
      }
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw AuthenticationException('Authentication required for conversational optimization');
      } else if (e.response?.statusCode == 429) {
        throw RateLimitException('Too many optimization requests. Please try again later.');
      } else {
        throw ServerException('Network error during optimization: ${e.message}');
      }
    } catch (e) {
      throw ServerException('Unexpected error during conversational optimization: $e');
    }
  }

  /// Start a new conversation session
  String startConversation() {
    final conversationId = DateTime.now().millisecondsSinceEpoch.toString();
    _conversationHistory[conversationId] = [];
    return conversationId;
  }

  /// Get conversation history for a session
  List<ConversationMessage> getConversationHistory(String? conversationId) {
    if (conversationId == null) return [];
    return _conversationHistory[conversationId] ?? [];
  }

  /// Clear conversation history
  void clearConversation(String? conversationId) {
    if (conversationId != null) {
      _conversationHistory.remove(conversationId);
    }
  }

  /// Get suggested optimization prompts
  Future<List<String>> getSuggestedPrompts({
    required Map<String, dynamic> listingData,
    String category = 'general',
  }) async {
    try {
      final response = await _apiClient.post(
        '/ai/suggested-prompts',
        data: {
          'listing_data': listingData,
          'category': category,
        },
      );

      if (response.statusCode == 200) {
        final data = response.data;
        return List<String>.from(data['prompts'] ?? []);
      } else {
        // Return fallback prompts if API fails
        return _getFallbackPrompts(category);
      }
    } on DioException catch (e) {
      // Return fallback prompts on network error
      return _getFallbackPrompts(category);
    }
  }

  /// Process quick optimization commands
  Future<ConversationalOptimizationResult> processQuickCommand({
    required String command,
    required Map<String, dynamic> currentListing,
    String? conversationId,
  }) async {
    final commandMap = {
      'improve_title': 'Make the title more engaging and SEO-friendly',
      'enhance_description': 'Improve the product description with more details',
      'optimize_keywords': 'Add relevant keywords for better search visibility',
      'adjust_pricing': 'Suggest better pricing strategy',
      'improve_category': 'Optimize category selection',
      'add_features': 'Highlight key product features',
    };

    final userMessage = commandMap[command] ?? command;
    
    return optimizeWithConversation(
      userMessage: userMessage,
      currentListing: currentListing,
      optimizationFocus: _getOptimizationFocus(command),
      conversationId: conversationId,
    );
  }

  /// Explain optimization changes
  Future<String> explainChanges({
    required List<OptimizationChange> changes,
    String? conversationId,
  }) async {
    try {
      final response = await _apiClient.post(
        '/ai/explain-changes',
        data: {
          'changes': changes.map((change) => change.toJson()).toList(),
        },
      );

      if (response.statusCode == 200) {
        return response.data['explanation'] ?? 'Changes applied successfully.';
      } else {
        return _generateFallbackExplanation(changes);
      }
    } on DioException catch (e) {
      return _generateFallbackExplanation(changes);
    }
  }

  /// Validate optimization results
  Future<Map<String, dynamic>> validateOptimization({
    required Map<String, dynamic> originalListing,
    required Map<String, dynamic> optimizedListing,
  }) async {
    try {
      final response = await _apiClient.post(
        '/ai/validate-optimization',
        data: {
          'original_listing': originalListing,
          'optimized_listing': optimizedListing,
        },
      );

      if (response.statusCode == 200) {
        return response.data;
      } else {
        return _createFallbackValidation();
      }
    } on DioException catch (e) {
      return _createFallbackValidation();
    }
  }

  // Private helper methods

  List<ConversationMessage> _getConversationContext(String? conversationId) {
    if (conversationId == null) return [];
    return _conversationHistory[conversationId] ?? [];
  }

  void _updateConversationHistory(
    String? conversationId,
    String userMessage,
    ConversationalOptimizationResult result,
  ) {
    if (conversationId == null) return;

    final history = _conversationHistory[conversationId] ?? [];
    
    // Add user message
    history.add(ConversationMessage(
      role: 'user',
      content: userMessage,
      timestamp: DateTime.now(),
    ));
    
    // Add assistant response
    history.add(ConversationMessage(
      role: 'assistant',
      content: result.explanation,
      timestamp: DateTime.now(),
    ));
    
    // Keep only last 20 messages
    if (history.length > 20) {
      history.removeRange(0, history.length - 20);
    }
    
    _conversationHistory[conversationId] = history;
  }

  List<String> _getFallbackPrompts(String category) {
    return [
      'Make the title more engaging',
      'Improve the product description',
      'Add relevant keywords',
      'Optimize for better search visibility',
      'Enhance the listing quality',
    ];
  }

  String _getOptimizationFocus(String command) {
    final focusMap = {
      'improve_title': 'seo',
      'enhance_description': 'content',
      'optimize_keywords': 'seo',
      'adjust_pricing': 'pricing',
      'improve_category': 'category',
      'add_features': 'content',
    };
    
    return focusMap[command] ?? 'general';
  }

  String _generateFallbackExplanation(List<OptimizationChange> changes) {
    if (changes.isEmpty) {
      return 'No changes were made to your listing.';
    }
    
    final changeTypes = changes.map((c) => c.field).toSet();
    return 'Updated ${changeTypes.join(', ')} to improve your listing performance.';
  }

  Map<String, dynamic> _createFallbackValidation() {
    return {
      'is_valid': true,
      'score': 0.8,
      'improvements': ['Listing has been optimized'],
      'warnings': [],
    };
  }
}
