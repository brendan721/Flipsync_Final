import 'package:flipsync_mobile/data/models/decision_model.dart';
import 'package:flipsync_mobile/presentation/blocs/decisions/decisions_state.dart';

/// Test data factory for creating proper test instances
class TestDataFactory {
  /// Create a sample DecisionModel for testing
  static DecisionModel createSampleDecision({
    String? id,
    String? agentId,
    String? decisionType,
    double? confidence,
    String? timestamp,
    String? status,
  }) {
    return DecisionModel(
      id: id ?? 'test_decision_1',
      decisionId: id ?? 'test_decision_1',
      agentId: agentId ?? 'test_agent',
      decisionType: decisionType ?? 'optimization',
      status: status ?? 'completed',
      executionTimeMs: 150.0,
      confidence: confidence ?? 0.95,
      context: const {'test': true},
      result: const DecisionResult(
        action: 'optimize_pricing',
        alternatives: [],
        reasoning: 'Test reasoning',
        batteryEfficient: true,
        networkEfficient: true,
      ),
      compliance: const ComplianceInfo(
        usedLlm: false,
        usedStandardPipeline: true,
        algorithmUsed: 'test_algorithm',
        llmFreeCompliant: true,
        pipelineCompliant: true,
      ),
      performance: const PerformanceInfo(meets1000msTarget: true, confidenceLevel: 'high'),
      timestamps: TimestampInfo(
        startedAt: timestamp ?? '2024-01-01T00:00:00Z',
        completedAt: timestamp ?? '2024-01-01T00:00:01Z',
        createdAt: timestamp ?? '2024-01-01T00:00:00Z',
      ),
    );
  }

  /// Create sample PaginationInfo for testing
  static PaginationInfo createSamplePagination({int? totalCount, int? limit, int? offset, bool? hasMore}) {
    return PaginationInfo(
      totalCount: totalCount ?? 100,
      limit: limit ?? 50,
      offset: offset ?? 0,
      hasMore: hasMore ?? false,
    );
  }

  /// Create sample ComplianceMetrics for testing
  static ComplianceMetrics createSampleComplianceMetrics({
    int? totalDecisions,
    double? llmFreeRate,
    double? standardPipelineRate,
    double? performanceTargetRate,
    double? fullyCompliantRate,
  }) {
    return ComplianceMetrics(
      totalDecisions: totalDecisions ?? 100,
      llmFreeRate: llmFreeRate ?? 1.0,
      standardPipelineRate: standardPipelineRate ?? 1.0,
      performanceTargetRate: performanceTargetRate ?? 1.0,
      fullyCompliantRate: fullyCompliantRate ?? 1.0,
    );
  }

  /// Create sample DatabaseInfo for testing
  static DatabaseInfo createSampleDatabaseInfo({String? source, bool? legacyFree, String? architecture}) {
    return DatabaseInfo(
      source: source ?? 'flipsync_agentic_test',
      legacyFree: legacyFree ?? true,
      architecture: architecture ?? '4+1',
    );
  }

  /// Create a complete DecisionsLoaded state for testing
  static DecisionsLoaded createSampleDecisionsLoaded({
    List<DecisionModel>? decisions,
    PaginationInfo? pagination,
    Map<String, dynamic>? filtersApplied,
    ComplianceMetrics? complianceMetrics,
    DatabaseInfo? databaseInfo,
    DateTime? lastUpdated,
    bool? hasMore,
  }) {
    return DecisionsLoaded(
      decisions: decisions ?? [createSampleDecision()],
      pagination: pagination ?? createSamplePagination(),
      filtersApplied: filtersApplied ?? const {},
      complianceMetrics: complianceMetrics ?? createSampleComplianceMetrics(),
      databaseInfo: databaseInfo ?? createSampleDatabaseInfo(),
      lastUpdated: lastUpdated ?? DateTime.parse('2024-01-01T00:00:00Z'),
      hasMore: hasMore ?? false,
    );
  }

  /// Create sample decisions list for testing
  static List<DecisionModel> createSampleDecisionsList({int count = 2, String? agentId}) {
    return List.generate(
      count,
      (index) => createSampleDecision(
        id: 'test_decision_${index + 1}',
        agentId: agentId ?? 'test_agent',
        decisionType: index == 0 ? 'content_optimization' : 'pricing_adjustment',
        confidence: index == 0 ? 0.95 : 0.87,
        timestamp: index == 0 ? '2024-01-01T00:00:00Z' : '2024-01-01T01:00:00Z',
      ),
    );
  }
}
