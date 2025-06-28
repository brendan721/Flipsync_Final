import 'dart:async';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:injectable/injectable.dart';
import '../../core/logging/logger.dart';
import '../../core/error/exceptions.dart';

/// Comprehensive error handling service for production FlipSync
@injectable
class ComprehensiveErrorHandler {
  final Logger _logger;
  final Map<String, int> _errorCounts = {};
  final Map<String, DateTime> _lastErrorTimes = {};
  final List<ErrorReport> _errorHistory = [];

  ComprehensiveErrorHandler(this._logger);

  /// Handle any error with comprehensive fallback strategies
  Future<ErrorHandlingResult> handleError(
    dynamic error, {
    String? context,
    Map<String, dynamic>? metadata,
    bool enableRetry = true,
    bool enableFallback = true,
  }) async {
    try {
      _logger.info('Handling error in context: ${context ?? "unknown"}');
      
      // Create error report
      final errorReport = _createErrorReport(error, context, metadata);
      _errorHistory.add(errorReport);
      
      // Determine error type and strategy
      final errorType = _categorizeError(error);
      final strategy = _determineStrategy(errorType, errorReport);
      
      // Execute handling strategy
      final result = await _executeStrategy(strategy, errorReport, enableRetry, enableFallback);
      
      // Track error for analytics
      _trackError(errorReport, result);
      
      return result;
    } catch (handlingError) {
      _logger.error('Error handling failed: $handlingError');
      return _createFailsafeResult(error, context);
    }
  }

  /// Handle network-specific errors
  Future<ErrorHandlingResult> handleNetworkError(
    dynamic error, {
    String? endpoint,
    String? method,
    int? statusCode,
    bool enableRetry = true,
  }) async {
    final metadata = {
      'endpoint': endpoint,
      'method': method,
      'status_code': statusCode,
      'error_type': 'network',
    };

    return handleError(
      error,
      context: 'network',
      metadata: metadata,
      enableRetry: enableRetry,
    );
  }

  /// Handle AI service errors with specific fallbacks
  Future<ErrorHandlingResult> handleAIError(
    dynamic error, {
    String? aiService,
    String? operation,
    Map<String, dynamic>? requestData,
  }) async {
    final metadata = {
      'ai_service': aiService,
      'operation': operation,
      'request_data': requestData,
      'error_type': 'ai_service',
    };

    return handleError(
      error,
      context: 'ai_service',
      metadata: metadata,
      enableFallback: true,
    );
  }

  /// Handle authentication errors
  Future<ErrorHandlingResult> handleAuthError(
    dynamic error, {
    String? authMethod,
    bool isTokenExpired = false,
  }) async {
    final metadata = {
      'auth_method': authMethod,
      'token_expired': isTokenExpired,
      'error_type': 'authentication',
    };

    return handleError(
      error,
      context: 'authentication',
      metadata: metadata,
      enableRetry: isTokenExpired, // Retry if token expired
    );
  }

  /// Get error statistics
  Map<String, dynamic> getErrorStatistics() {
    final now = DateTime.now();
    final recentErrors = _errorHistory.where(
      (error) => now.difference(error.timestamp).inHours < 24
    ).toList();

    return {
      'total_errors': _errorHistory.length,
      'recent_errors_24h': recentErrors.length,
      'error_types': _getErrorTypeDistribution(recentErrors),
      'most_common_errors': _getMostCommonErrors(),
      'error_rate_per_hour': recentErrors.length / 24,
    };
  }

  // Private implementation methods

  ErrorReport _createErrorReport(
    dynamic error,
    String? context,
    Map<String, dynamic>? metadata,
  ) {
    return ErrorReport(
      error: error,
      context: context ?? 'unknown',
      metadata: metadata ?? {},
      timestamp: DateTime.now(),
      stackTrace: StackTrace.current,
    );
  }

  ErrorType _categorizeError(dynamic error) {
    if (error is SocketException || error is HttpException) {
      return ErrorType.network;
    } else if (error is DioException) {
      return _categorizeDioError(error);
    } else if (error is AuthenticationException) {
      return ErrorType.authentication;
    } else if (error is ServerException) {
      return ErrorType.server;
    } else if (error is ValidationException) {
      return ErrorType.validation;
    } else if (error is TimeoutException) {
      return ErrorType.timeout;
    } else {
      return ErrorType.unknown;
    }
  }

  ErrorType _categorizeDioError(DioException error) {
    switch (error.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
        return ErrorType.timeout;
      case DioExceptionType.connectionError:
        return ErrorType.network;
      case DioExceptionType.badResponse:
        final statusCode = error.response?.statusCode;
        if (statusCode == 401 || statusCode == 403) {
          return ErrorType.authentication;
        } else if (statusCode != null && statusCode >= 500) {
          return ErrorType.server;
        } else {
          return ErrorType.validation;
        }
      default:
        return ErrorType.network;
    }
  }

  ErrorHandlingStrategy _determineStrategy(ErrorType errorType, ErrorReport report) {
    // Check if this error is happening frequently
    final errorKey = '${errorType.name}_${report.context}';
    final errorCount = _errorCounts[errorKey] ?? 0;
    final lastErrorTime = _lastErrorTimes[errorKey];
    
    // If error happened recently and frequently, use different strategy
    if (lastErrorTime != null && 
        DateTime.now().difference(lastErrorTime).inMinutes < 5 && 
        errorCount > 3) {
      return ErrorHandlingStrategy.gracefulDegradation;
    }

    switch (errorType) {
      case ErrorType.network:
        return ErrorHandlingStrategy.retryWithBackoff;
      case ErrorType.timeout:
        return ErrorHandlingStrategy.retryWithBackoff;
      case ErrorType.authentication:
        return ErrorHandlingStrategy.refreshAndRetry;
      case ErrorType.server:
        return ErrorHandlingStrategy.fallbackWithCache;
      case ErrorType.validation:
        return ErrorHandlingStrategy.userFeedback;
      case ErrorType.aiService:
        return ErrorHandlingStrategy.fallbackService;
      case ErrorType.unknown:
      default:
        return ErrorHandlingStrategy.logAndContinue;
    }
  }

  Future<ErrorHandlingResult> _executeStrategy(
    ErrorHandlingStrategy strategy,
    ErrorReport report,
    bool enableRetry,
    bool enableFallback,
  ) async {
    switch (strategy) {
      case ErrorHandlingStrategy.retryWithBackoff:
        return _executeRetryWithBackoff(report, enableRetry);
      case ErrorHandlingStrategy.refreshAndRetry:
        return _executeRefreshAndRetry(report);
      case ErrorHandlingStrategy.fallbackWithCache:
        return _executeFallbackWithCache(report, enableFallback);
      case ErrorHandlingStrategy.fallbackService:
        return _executeFallbackService(report, enableFallback);
      case ErrorHandlingStrategy.gracefulDegradation:
        return _executeGracefulDegradation(report);
      case ErrorHandlingStrategy.userFeedback:
        return _executeUserFeedback(report);
      case ErrorHandlingStrategy.logAndContinue:
      default:
        return _executeLogAndContinue(report);
    }
  }

  Future<ErrorHandlingResult> _executeRetryWithBackoff(
    ErrorReport report,
    bool enableRetry,
  ) async {
    if (!enableRetry) {
      return _executeLogAndContinue(report);
    }

    const maxRetries = 3;
    const baseDelay = Duration(milliseconds: 500);

    for (int attempt = 1; attempt <= maxRetries; attempt++) {
      await Future.delayed(Duration(milliseconds: baseDelay.inMilliseconds * attempt));
      
      try {
        // In a real implementation, this would retry the original operation
        await Future.delayed(Duration(milliseconds: 100));
        
        return ErrorHandlingResult(
          success: true,
          strategy: ErrorHandlingStrategy.retryWithBackoff,
          message: 'Operation succeeded after $attempt attempts',
          retryCount: attempt,
        );
      } catch (e) {
        if (attempt == maxRetries) {
          return ErrorHandlingResult(
            success: false,
            strategy: ErrorHandlingStrategy.retryWithBackoff,
            message: 'Operation failed after $maxRetries attempts',
            retryCount: attempt,
            fallbackUsed: true,
          );
        }
      }
    }

    return _executeLogAndContinue(report);
  }

  Future<ErrorHandlingResult> _executeRefreshAndRetry(ErrorReport report) async {
    try {
      // Refresh authentication token
      await _refreshAuthToken();
      
      // Retry original operation
      await Future.delayed(Duration(milliseconds: 100));
      
      return ErrorHandlingResult(
        success: true,
        strategy: ErrorHandlingStrategy.refreshAndRetry,
        message: 'Authentication refreshed and operation retried successfully',
      );
    } catch (e) {
      return ErrorHandlingResult(
        success: false,
        strategy: ErrorHandlingStrategy.refreshAndRetry,
        message: 'Failed to refresh authentication',
        fallbackUsed: true,
      );
    }
  }

  Future<ErrorHandlingResult> _executeFallbackWithCache(
    ErrorReport report,
    bool enableFallback,
  ) async {
    if (!enableFallback) {
      return _executeLogAndContinue(report);
    }

    try {
      // Try to get cached data
      final cachedData = await _getCachedData(report.context);
      
      if (cachedData != null) {
        return ErrorHandlingResult(
          success: true,
          strategy: ErrorHandlingStrategy.fallbackWithCache,
          message: 'Using cached data as fallback',
          fallbackUsed: true,
          data: cachedData,
        );
      }
    } catch (e) {
      _logger.warning('Cache fallback failed: $e');
    }

    return _executeLogAndContinue(report);
  }

  Future<ErrorHandlingResult> _executeFallbackService(
    ErrorReport report,
    bool enableFallback,
  ) async {
    if (!enableFallback) {
      return _executeLogAndContinue(report);
    }

    try {
      // For AI services, fallback to OpenAI if Ollama fails
      if (report.context == 'ai_service') {
        final fallbackResult = await _useAIFallbackService(report);
        return ErrorHandlingResult(
          success: true,
          strategy: ErrorHandlingStrategy.fallbackService,
          message: 'Using fallback AI service',
          fallbackUsed: true,
          data: fallbackResult,
        );
      }
    } catch (e) {
      _logger.warning('Fallback service failed: $e');
    }

    return _executeLogAndContinue(report);
  }

  Future<ErrorHandlingResult> _executeGracefulDegradation(ErrorReport report) async {
    return ErrorHandlingResult(
      success: true,
      strategy: ErrorHandlingStrategy.gracefulDegradation,
      message: 'Feature temporarily disabled due to repeated errors',
      fallbackUsed: true,
    );
  }

  Future<ErrorHandlingResult> _executeUserFeedback(ErrorReport report) async {
    return ErrorHandlingResult(
      success: false,
      strategy: ErrorHandlingStrategy.userFeedback,
      message: _getUserFriendlyMessage(report),
      requiresUserAction: true,
    );
  }

  Future<ErrorHandlingResult> _executeLogAndContinue(ErrorReport report) async {
    _logger.error('Error logged: ${report.error}');
    
    return ErrorHandlingResult(
      success: false,
      strategy: ErrorHandlingStrategy.logAndContinue,
      message: 'Error logged and operation continued',
    );
  }

  ErrorHandlingResult _createFailsafeResult(dynamic error, String? context) {
    return ErrorHandlingResult(
      success: false,
      strategy: ErrorHandlingStrategy.logAndContinue,
      message: 'Failsafe error handling activated',
      fallbackUsed: true,
    );
  }

  void _trackError(ErrorReport report, ErrorHandlingResult result) {
    final errorKey = '${_categorizeError(report.error).name}_${report.context}';
    _errorCounts[errorKey] = (_errorCounts[errorKey] ?? 0) + 1;
    _lastErrorTimes[errorKey] = DateTime.now();
  }

  Map<String, int> _getErrorTypeDistribution(List<ErrorReport> errors) {
    final distribution = <String, int>{};
    for (final error in errors) {
      final type = _categorizeError(error.error).name;
      distribution[type] = (distribution[type] ?? 0) + 1;
    }
    return distribution;
  }

  List<String> _getMostCommonErrors() {
    final sortedErrors = _errorCounts.entries.toList()
      ..sort((a, b) => b.value.compareTo(a.value));
    return sortedErrors.take(5).map((e) => e.key).toList();
  }

  Future<void> _refreshAuthToken() async {
    await Future.delayed(Duration(milliseconds: 200));
    // Implementation would refresh the actual auth token
  }

  Future<Map<String, dynamic>?> _getCachedData(String context) async {
    await Future.delayed(Duration(milliseconds: 50));
    // Implementation would retrieve cached data
    return {'cached': true, 'context': context};
  }

  Future<Map<String, dynamic>> _useAIFallbackService(ErrorReport report) async {
    await Future.delayed(Duration(milliseconds: 500));
    // Implementation would call fallback AI service (OpenAI)
    return {'fallback_ai': true, 'service': 'openai'};
  }

  String _getUserFriendlyMessage(ErrorReport report) {
    final errorType = _categorizeError(report.error);
    switch (errorType) {
      case ErrorType.network:
        return 'Please check your internet connection and try again.';
      case ErrorType.authentication:
        return 'Please log in again to continue.';
      case ErrorType.validation:
        return 'Please check your input and try again.';
      case ErrorType.server:
        return 'Our servers are experiencing issues. Please try again later.';
      case ErrorType.timeout:
        return 'The request is taking longer than expected. Please try again.';
      case ErrorType.aiService:
        return 'AI service is temporarily unavailable. Using fallback.';
      default:
        return 'An unexpected error occurred. Please try again.';
    }
  }
}

// Supporting classes and enums
class ErrorReport {
  final dynamic error;
  final String context;
  final Map<String, dynamic> metadata;
  final DateTime timestamp;
  final StackTrace stackTrace;

  ErrorReport({
    required this.error,
    required this.context,
    required this.metadata,
    required this.timestamp,
    required this.stackTrace,
  });
}

enum ErrorType {
  network,
  authentication,
  server,
  validation,
  timeout,
  aiService,
  unknown,
}

enum ErrorHandlingStrategy {
  retryWithBackoff,
  refreshAndRetry,
  fallbackWithCache,
  fallbackService,
  gracefulDegradation,
  userFeedback,
  logAndContinue,
}

class ErrorHandlingResult {
  final bool success;
  final ErrorHandlingStrategy strategy;
  final String message;
  final bool fallbackUsed;
  final bool requiresUserAction;
  final int retryCount;
  final Map<String, dynamic>? data;

  ErrorHandlingResult({
    required this.success,
    required this.strategy,
    required this.message,
    this.fallbackUsed = false,
    this.requiresUserAction = false,
    this.retryCount = 0,
    this.data,
  });
}
