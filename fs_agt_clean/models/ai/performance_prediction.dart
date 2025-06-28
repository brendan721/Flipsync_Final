import 'package:json_annotation/json_annotation.dart';

part 'performance_prediction.g.dart';

/// Performance prediction result from AI Feature 5
@JsonSerializable()
class PerformancePrediction {
  @JsonKey(name: 'sale_time_prediction_days')
  final int saleTimePredictionDays;
  
  @JsonKey(name: 'success_probability')
  final double successProbability;
  
  @JsonKey(name: 'performance_score')
  final double performanceScore;
  
  @JsonKey(name: 'performance_category')
  final String performanceCategory;
  
  final String confidence;
  
  @JsonKey(name: 'optimization_recommendations')
  final List<String> optimizationRecommendations;
  
  @JsonKey(name: 'factors_analysis')
  final Map<String, dynamic> factorsAnalysis;
  
  @JsonKey(name: 'market_comparison')
  final Map<String, dynamic> marketComparison;
  
  @JsonKey(name: 'predicted_at')
  final String predictedAt;

  const PerformancePrediction({
    required this.saleTimePredictionDays,
    required this.successProbability,
    required this.performanceScore,
    required this.performanceCategory,
    required this.confidence,
    required this.optimizationRecommendations,
    required this.factorsAnalysis,
    required this.marketComparison,
    required this.predictedAt,
  });

  factory PerformancePrediction.fromJson(Map<String, dynamic> json) =>
      _$PerformancePredictionFromJson(json);

  Map<String, dynamic> toJson() => _$PerformancePredictionToJson(this);

  /// Get performance category as enum
  PerformanceCategory get categoryEnum {
    switch (performanceCategory.toLowerCase()) {
      case 'excellent':
        return PerformanceCategory.excellent;
      case 'good':
        return PerformanceCategory.good;
      case 'average':
        return PerformanceCategory.average;
      case 'poor':
        return PerformanceCategory.poor;
      default:
        return PerformanceCategory.average;
    }
  }

  /// Get confidence level as enum
  ConfidenceLevel get confidenceEnum {
    switch (confidence.toLowerCase()) {
      case 'high':
        return ConfidenceLevel.high;
      case 'medium':
        return ConfidenceLevel.medium;
      case 'low':
        return ConfidenceLevel.low;
      default:
        return ConfidenceLevel.medium;
    }
  }

  /// Get competitive position from market comparison
  String get competitivePosition {
    return marketComparison['competitive_position'] ?? 'average';
  }

  /// Get market demand factor
  double get marketDemand {
    return (marketComparison['market_demand'] ?? 1.0).toDouble();
  }

  /// Get category performance score
  double get categoryPerformance {
    return (marketComparison['category_performance'] ?? 0.5).toDouble();
  }

  /// Get overall quality score from factors analysis
  double get overallQualityScore {
    final qualityFactors = factorsAnalysis['quality_factors'] as Map<String, dynamic>?;
    return (qualityFactors?['overall_quality_score'] ?? 0.5).toDouble();
  }

  /// Check if prediction indicates good performance
  bool get isGoodPerformance {
    return performanceScore >= 0.7 && successProbability >= 0.6;
  }

  /// Get formatted sale time prediction
  String get formattedSaleTime {
    if (saleTimePredictionDays <= 7) {
      return '$saleTimePredictionDays days';
    } else if (saleTimePredictionDays <= 30) {
      final weeks = (saleTimePredictionDays / 7).round();
      return '$weeks week${weeks > 1 ? 's' : ''}';
    } else {
      final months = (saleTimePredictionDays / 30).round();
      return '$months month${months > 1 ? 's' : ''}';
    }
  }

  /// Get success probability as percentage
  String get successProbabilityPercentage {
    return '${(successProbability * 100).round()}%';
  }

  /// Get performance score as percentage
  String get performanceScorePercentage {
    return '${(performanceScore * 100).round()}%';
  }
}

/// Performance category enumeration
enum PerformanceCategory {
  excellent,
  good,
  average,
  poor,
}

/// Confidence level enumeration
enum ConfidenceLevel {
  high,
  medium,
  low,
}

/// Extension methods for performance category
extension PerformanceCategoryExtension on PerformanceCategory {
  String get displayName {
    switch (this) {
      case PerformanceCategory.excellent:
        return 'Excellent';
      case PerformanceCategory.good:
        return 'Good';
      case PerformanceCategory.average:
        return 'Average';
      case PerformanceCategory.poor:
        return 'Poor';
    }
  }

  String get description {
    switch (this) {
      case PerformanceCategory.excellent:
        return 'Outstanding performance expected';
      case PerformanceCategory.good:
        return 'Good performance likely';
      case PerformanceCategory.average:
        return 'Average performance expected';
      case PerformanceCategory.poor:
        return 'Below average performance likely';
    }
  }
}

/// Extension methods for confidence level
extension ConfidenceLevelExtension on ConfidenceLevel {
  String get displayName {
    switch (this) {
      case ConfidenceLevel.high:
        return 'High Confidence';
      case ConfidenceLevel.medium:
        return 'Medium Confidence';
      case ConfidenceLevel.low:
        return 'Low Confidence';
    }
  }

  double get scoreThreshold {
    switch (this) {
      case ConfidenceLevel.high:
        return 0.8;
      case ConfidenceLevel.medium:
        return 0.6;
      case ConfidenceLevel.low:
        return 0.4;
    }
  }
}
