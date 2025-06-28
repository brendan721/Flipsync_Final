import 'dart:convert';
import 'package:dio/dio.dart';
import 'package:injectable/injectable.dart';
import '../../core/network/api_client.dart';
import '../../core/error/exceptions.dart';
import '../../models/ai/performance_prediction.dart';

/// Service for AI-powered listing performance prediction (AI Feature 5)
@injectable
class AIPerformancePredictionService {
  final ApiClient _apiClient;

  AIPerformancePredictionService(this._apiClient);

  /// Predict listing performance and success probability
  Future<PerformancePrediction> predictListingPerformance({
    required Map<String, dynamic> productData,
    required Map<String, dynamic> listingData,
    String marketplace = 'ebay',
    Map<String, dynamic>? historicalContext,
  }) async {
    try {
      final response = await _apiClient.post(
        '/ai/predict-performance',
        data: {
          'product_data': productData,
          'listing_data': listingData,
          'marketplace': marketplace,
          'historical_context': historicalContext,
        },
      );

      if (response.statusCode == 200) {
        final data = response.data;
        if (data['success'] == true) {
          return PerformancePrediction.fromJson(data['prediction']);
        } else {
          throw ServerException('Performance prediction failed: ${data['message']}');
        }
      } else {
        throw ServerException('Failed to predict performance: ${response.statusCode}');
      }
    } on DioException catch (e) {
      if (e.response?.statusCode == 401) {
        throw AuthenticationException('Authentication required for performance prediction');
      } else if (e.response?.statusCode == 429) {
        throw RateLimitException('Too many prediction requests. Please try again later.');
      } else {
        throw ServerException('Network error during performance prediction: ${e.message}');
      }
    } catch (e) {
      throw ServerException('Unexpected error during performance prediction: $e');
    }
  }

  /// Get performance prediction for multiple listings (batch processing)
  Future<List<PerformancePrediction>> predictBatchPerformance({
    required List<Map<String, dynamic>> listings,
    String marketplace = 'ebay',
  }) async {
    try {
      final List<PerformancePrediction> predictions = [];
      
      // Process in batches of 5 to avoid overwhelming the API
      for (int i = 0; i < listings.length; i += 5) {
        final batch = listings.skip(i).take(5).toList();
        final batchPredictions = await Future.wait(
          batch.map((listing) => predictListingPerformance(
            productData: listing['product_data'] ?? {},
            listingData: listing['listing_data'] ?? {},
            marketplace: marketplace,
          )),
        );
        predictions.addAll(batchPredictions);
      }
      
      return predictions;
    } catch (e) {
      throw ServerException('Batch performance prediction failed: $e');
    }
  }

  /// Get performance insights for existing listings
  Future<Map<String, dynamic>> getPerformanceInsights({
    required String listingId,
    int daysPeriod = 30,
  }) async {
    try {
      final response = await _apiClient.get(
        '/analytics/performance-insights/$listingId',
        queryParameters: {
          'days_period': daysPeriod,
        },
      );

      if (response.statusCode == 200) {
        return response.data;
      } else {
        throw ServerException('Failed to get performance insights: ${response.statusCode}');
      }
    } on DioException catch (e) {
      throw ServerException('Network error getting performance insights: ${e.message}');
    }
  }

  /// Compare listing performance against market averages
  Future<Map<String, dynamic>> compareMarketPerformance({
    required Map<String, dynamic> listingData,
    required String category,
    String marketplace = 'ebay',
  }) async {
    try {
      final response = await _apiClient.post(
        '/ai/market-comparison',
        data: {
          'listing_data': listingData,
          'category': category,
          'marketplace': marketplace,
        },
      );

      if (response.statusCode == 200) {
        return response.data;
      } else {
        throw ServerException('Failed to compare market performance: ${response.statusCode}');
      }
    } on DioException catch (e) {
      throw ServerException('Network error during market comparison: ${e.message}');
    }
  }

  /// Get performance optimization recommendations
  Future<List<String>> getOptimizationRecommendations({
    required Map<String, dynamic> listingData,
    required PerformancePrediction currentPrediction,
  }) async {
    try {
      final response = await _apiClient.post(
        '/ai/optimization-recommendations',
        data: {
          'listing_data': listingData,
          'current_prediction': currentPrediction.toJson(),
        },
      );

      if (response.statusCode == 200) {
        final data = response.data;
        return List<String>.from(data['recommendations'] ?? []);
      } else {
        throw ServerException('Failed to get optimization recommendations: ${response.statusCode}');
      }
    } on DioException catch (e) {
      throw ServerException('Network error getting recommendations: ${e.message}');
    }
  }

  /// Validate prediction accuracy (for learning and improvement)
  Future<void> validatePredictionAccuracy({
    required String predictionId,
    required Map<String, dynamic> actualResults,
  }) async {
    try {
      await _apiClient.post(
        '/ai/validate-prediction',
        data: {
          'prediction_id': predictionId,
          'actual_results': actualResults,
        },
      );
    } on DioException catch (e) {
      // Non-critical operation, log but don't throw
      print('Warning: Failed to validate prediction accuracy: ${e.message}');
    }
  }
}
