import 'package:json_annotation/json_annotation.dart';

part 'conversational_optimization.g.dart';

/// Conversational optimization result from AI Feature 6
@JsonSerializable()
class ConversationalOptimizationResult {
  @JsonKey(name: 'original_request')
  final String originalRequest;
  
  @JsonKey(name: 'optimized_listing')
  final Map<String, dynamic> optimizedListing;
  
  @JsonKey(name: 'changes_made')
  final List<OptimizationChange> changesMade;
  
  final String explanation;
  final double confidence;
  
  @JsonKey(name: 'additional_suggestions')
  final List<String> additionalSuggestions;
  
  @JsonKey(name: 'processed_at')
  final String processedAt;

  const ConversationalOptimizationResult({
    required this.originalRequest,
    required this.optimizedListing,
    required this.changesMade,
    required this.explanation,
    required this.confidence,
    required this.additionalSuggestions,
    required this.processedAt,
  });

  factory ConversationalOptimizationResult.fromJson(Map<String, dynamic> json) =>
      _$ConversationalOptimizationResultFromJson(json);

  Map<String, dynamic> toJson() => _$ConversationalOptimizationResultToJson(this);

  /// Check if optimization was successful
  bool get isSuccessful => confidence >= 0.7 && changesMade.isNotEmpty;

  /// Get confidence as percentage
  String get confidencePercentage => '${(confidence * 100).round()}%';

  /// Get summary of changes
  String get changesSummary {
    if (changesMade.isEmpty) return 'No changes made';
    
    final fields = changesMade.map((c) => c.field).toSet();
    return 'Updated ${fields.join(', ')}';
  }

  /// Check if specific field was changed
  bool hasFieldChanged(String field) {
    return changesMade.any((change) => change.field == field);
  }

  /// Get change for specific field
  OptimizationChange? getChangeForField(String field) {
    try {
      return changesMade.firstWhere((change) => change.field == field);
    } catch (e) {
      return null;
    }
  }
}

/// Individual optimization change
@JsonSerializable()
class OptimizationChange {
  final String field;
  
  @JsonKey(name: 'old_value')
  final dynamic oldValue;
  
  @JsonKey(name: 'new_value')
  final dynamic newValue;
  
  final String reason;

  const OptimizationChange({
    required this.field,
    required this.oldValue,
    required this.newValue,
    required this.reason,
  });

  factory OptimizationChange.fromJson(Map<String, dynamic> json) =>
      _$OptimizationChangeFromJson(json);

  Map<String, dynamic> toJson() => _$OptimizationChangeToJson(this);

  /// Get field display name
  String get fieldDisplayName {
    switch (field.toLowerCase()) {
      case 'title':
        return 'Title';
      case 'description':
        return 'Description';
      case 'price':
        return 'Price';
      case 'keywords':
        return 'Keywords';
      case 'category':
        return 'Category';
      case 'images':
        return 'Images';
      default:
        return field.replaceAll('_', ' ').split(' ').map((word) => 
          word.isNotEmpty ? word[0].toUpperCase() + word.substring(1) : word
        ).join(' ');
    }
  }

  /// Get change type
  ChangeType get changeType {
    if (oldValue == null || oldValue.toString().isEmpty) {
      return ChangeType.added;
    } else if (newValue == null || newValue.toString().isEmpty) {
      return ChangeType.removed;
    } else {
      return ChangeType.modified;
    }
  }

  /// Get formatted change description
  String get changeDescription {
    switch (changeType) {
      case ChangeType.added:
        return 'Added $fieldDisplayName';
      case ChangeType.removed:
        return 'Removed $fieldDisplayName';
      case ChangeType.modified:
        return 'Updated $fieldDisplayName';
    }
  }
}

/// Conversation message for chat history
@JsonSerializable()
class ConversationMessage {
  final String role; // 'user' or 'assistant'
  final String content;
  final DateTime timestamp;

  const ConversationMessage({
    required this.role,
    required this.content,
    required this.timestamp,
  });

  factory ConversationMessage.fromJson(Map<String, dynamic> json) =>
      _$ConversationMessageFromJson(json);

  Map<String, dynamic> toJson() => _$ConversationMessageToJson(this);

  /// Check if message is from user
  bool get isFromUser => role == 'user';

  /// Check if message is from assistant
  bool get isFromAssistant => role == 'assistant';

  /// Get formatted timestamp
  String get formattedTime {
    final now = DateTime.now();
    final difference = now.difference(timestamp);
    
    if (difference.inMinutes < 1) {
      return 'Just now';
    } else if (difference.inHours < 1) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inDays < 1) {
      return '${difference.inHours}h ago';
    } else {
      return '${difference.inDays}d ago';
    }
  }
}

/// Optimization focus areas
enum OptimizationFocus {
  general,
  seo,
  pricing,
  content,
  images,
  category,
}

/// Change types
enum ChangeType {
  added,
  removed,
  modified,
}

/// Extension methods for optimization focus
extension OptimizationFocusExtension on OptimizationFocus {
  String get displayName {
    switch (this) {
      case OptimizationFocus.general:
        return 'General';
      case OptimizationFocus.seo:
        return 'SEO';
      case OptimizationFocus.pricing:
        return 'Pricing';
      case OptimizationFocus.content:
        return 'Content';
      case OptimizationFocus.images:
        return 'Images';
      case OptimizationFocus.category:
        return 'Category';
    }
  }

  String get description {
    switch (this) {
      case OptimizationFocus.general:
        return 'Overall listing improvement';
      case OptimizationFocus.seo:
        return 'Search engine optimization';
      case OptimizationFocus.pricing:
        return 'Pricing strategy optimization';
      case OptimizationFocus.content:
        return 'Content quality enhancement';
      case OptimizationFocus.images:
        return 'Image optimization';
      case OptimizationFocus.category:
        return 'Category optimization';
    }
  }
}

/// Quick optimization commands
class QuickOptimizationCommands {
  static const String improveTitle = 'improve_title';
  static const String enhanceDescription = 'enhance_description';
  static const String optimizeKeywords = 'optimize_keywords';
  static const String adjustPricing = 'adjust_pricing';
  static const String improveCategory = 'improve_category';
  static const String addFeatures = 'add_features';

  static const List<String> allCommands = [
    improveTitle,
    enhanceDescription,
    optimizeKeywords,
    adjustPricing,
    improveCategory,
    addFeatures,
  ];

  static String getDisplayName(String command) {
    switch (command) {
      case improveTitle:
        return 'Improve Title';
      case enhanceDescription:
        return 'Enhance Description';
      case optimizeKeywords:
        return 'Optimize Keywords';
      case adjustPricing:
        return 'Adjust Pricing';
      case improveCategory:
        return 'Improve Category';
      case addFeatures:
        return 'Add Features';
      default:
        return command.replaceAll('_', ' ').split(' ').map((word) => 
          word.isNotEmpty ? word[0].toUpperCase() + word.substring(1) : word
        ).join(' ');
    }
  }

  static String getDescription(String command) {
    switch (command) {
      case improveTitle:
        return 'Make the title more engaging and SEO-friendly';
      case enhanceDescription:
        return 'Improve product description with more details';
      case optimizeKeywords:
        return 'Add relevant keywords for better visibility';
      case adjustPricing:
        return 'Suggest competitive pricing strategy';
      case improveCategory:
        return 'Optimize category selection';
      case addFeatures:
        return 'Highlight key product features';
      default:
        return 'Optimize listing';
    }
  }
}
