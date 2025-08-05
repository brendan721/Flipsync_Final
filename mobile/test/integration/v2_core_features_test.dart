import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/features/agent_insights/models/agent_insight_models.dart';
import 'package:flipsync/features/agent_insights/services/agent_insights_service.dart';
import 'package:flipsync/features/partnership_settings/models/partnership_settings_models.dart';
import 'package:flipsync/features/partnership_settings/services/partnership_settings_service.dart';
import 'package:dio/dio.dart';

/// V2 Core Features Test - Unit tests for V2 partnership features
/// Tests the core V2 implementation without full app integration
void main() {
  group('V2 Core Features Tests', () {
    late Dio mockDio;
    late AgentInsightsService agentInsightsService;
    late PartnershipSettingsService partnershipSettingsService;

    setUp(() {
      mockDio = Dio();
      agentInsightsService = AgentInsightsService(mockDio);
      partnershipSettingsService = PartnershipSettingsService(mockDio);
    });

    group('Agent Insights Models', () {
      test('should create ProactiveRecommendation from JSON', () {
        final json = {
          'id': 'rec_001',
          'agent_id': 'market_agent',
          'agent_type': 'market',
          'title': 'Test Recommendation',
          'description': 'Test Description',
          'type': 'opportunity',
          'confidence': 0.85,
          'potential_impact': 150.0,
          'data': {'test': 'data'},
          'created_at': '2024-01-01T00:00:00Z',
          'priority': 'high',
          'available_actions': ['view', 'accept'],
        };

        final recommendation = ProactiveRecommendation.fromJson(json);

        expect(recommendation.id, equals('rec_001'));
        expect(recommendation.agentId, equals('market_agent'));
        expect(recommendation.title, equals('Test Recommendation'));
        expect(recommendation.confidence, equals(0.85));
        expect(recommendation.type, equals(RecommendationType.opportunity));
        expect(recommendation.priority, equals(RecommendationPriority.high));
      });

      test('should create AgentDiscovery from JSON', () {
        final json = {
          'id': 'disc_001',
          'agent_id': 'market_agent',
          'agent_type': 'market',
          'title': 'Test Discovery',
          'description': 'Test Description',
          'type': 'marketTrend',
          'discovery_data': {'trend': 'upward'},
          'confidence': 0.92,
          'potential_value': 500.0,
          'discovered_at': '2024-01-01T00:00:00Z',
          'available_actions': ['investigate'],
          'status': 'newDiscovery',
        };

        final discovery = AgentDiscovery.fromJson(json);

        expect(discovery.id, equals('disc_001'));
        expect(discovery.agentId, equals('market_agent'));
        expect(discovery.title, equals('Test Discovery'));
        expect(discovery.confidence, equals(0.92));
        expect(discovery.type, equals(DiscoveryType.marketTrend));
        expect(discovery.status, equals(DiscoveryStatus.newDiscovery));
      });

      test('should create MarketInsight from JSON', () {
        final json = {
          'id': 'insight_001',
          'category': 'pricing',
          'title': 'Test Insight',
          'description': 'Test Description',
          'data': {'price_change': 0.05},
          'impact': 0.75,
          'timestamp': '2024-01-01T00:00:00Z',
          'source': 'market_agent',
        };

        final insight = MarketInsight.fromJson(json);

        expect(insight.id, equals('insight_001'));
        expect(insight.category, equals('pricing'));
        expect(insight.title, equals('Test Insight'));
        expect(insight.impact, equals(0.75));
        expect(insight.source, equals('market_agent'));
      });

      test('should create PerformanceAlert from JSON', () {
        final json = {
          'id': 'alert_001',
          'agent_id': 'logistics_agent',
          'title': 'Test Alert',
          'message': 'Test Message',
          'severity': 'warning',
          'type': 'performance',
          'alert_data': {'metric': 'shipping_cost'},
          'created_at': '2024-01-01T00:00:00Z',
          'is_read': false,
          'available_actions': ['investigate'],
        };

        final alert = PerformanceAlert.fromJson(json);

        expect(alert.id, equals('alert_001'));
        expect(alert.agentId, equals('logistics_agent'));
        expect(alert.title, equals('Test Alert'));
        expect(alert.severity, equals(AlertSeverity.warning));
        expect(alert.type, equals(AlertType.performance));
        expect(alert.isRead, equals(false));
      });
    });

    group('Partnership Settings Models', () {
      test('should create DecisionAuthority with default values', () {
        final authority = DecisionAuthority(
          mode: DecisionMode.collaborative,
          agentAuthorities: {
            'market_agent': AgentAuthorityLevel.suggest,
            'content_agent': AgentAuthorityLevel.implement,
          },
          autoApprovalThreshold: 0.8,
          requireConfirmationForHighValue: true,
          highValueThreshold: 100.0,
        );

        expect(authority.mode, equals(DecisionMode.collaborative));
        expect(authority.agentAuthorities['market_agent'], equals(AgentAuthorityLevel.suggest));
        expect(authority.autoApprovalThreshold, equals(0.8));
        expect(authority.requireConfirmationForHighValue, equals(true));
      });

      test('should create PricingBoundaries with category limits', () {
        final boundaries = PricingBoundaries(
          maxPriceDropPercentage: 0.15,
          minProfitMargin: 25.0,
          repricingFrequency: RepricingFrequency.daily,
          enableAutomaticRepricing: true,
          categoryLimits: {
            'electronics': CategoryPricingLimits(
              maxDropPercentage: 0.10,
              minMargin: 30.0,
              enableRepricing: true,
            ),
          },
        );

        expect(boundaries.maxPriceDropPercentage, equals(0.15));
        expect(boundaries.minProfitMargin, equals(25.0));
        expect(boundaries.repricingFrequency, equals(RepricingFrequency.daily));
        expect(boundaries.categoryLimits['electronics']?.maxDropPercentage, equals(0.10));
      });

      test('should create NotificationPreferences with all options', () {
        final preferences = NotificationPreferences(
          highValueOpportunities: true,
          urgentBuyerMessages: true,
          dailyPerformanceSummaries: false,
          priceAdjustmentAlerts: true,
          agentRecommendations: true,
          systemAlerts: true,
          preferredMethod: NotificationMethod.push,
          agentSpecificNotifications: {
            'market_agent': true,
            'content_agent': false,
          },
        );

        expect(preferences.highValueOpportunities, equals(true));
        expect(preferences.preferredMethod, equals(NotificationMethod.push));
        expect(preferences.agentSpecificNotifications['market_agent'], equals(true));
      });

      test('should create AgentBehaviorSettings with aggressiveness levels', () {
        final behavior = AgentBehaviorSettings(
          aggressivenessLevel: 0.6,
          enableProactiveRecommendations: true,
          enableAutomaticOptimization: true,
          riskTolerance: 0.5,
          agentSpecificSettings: {
            'market_agent': AgentSpecificBehavior(
              enabled: true,
              aggressivenessOverride: 0.7,
              allowedActions: ['analyze_market'],
              restrictedActions: ['auto_purchase'],
            ),
          },
        );

        expect(behavior.aggressivenessLevel, equals(0.6));
        expect(behavior.enableProactiveRecommendations, equals(true));
        expect(behavior.agentSpecificSettings['market_agent']?.enabled, equals(true));
      });

      test('should create complete PartnershipSettings', () {
        final settings = PartnershipSettings(
          id: 'settings_001',
          userId: 'user_001',
          decisionAuthority: DecisionAuthority(
            mode: DecisionMode.collaborative,
            agentAuthorities: {'market_agent': AgentAuthorityLevel.suggest},
            autoApprovalThreshold: 0.8,
            requireConfirmationForHighValue: true,
            highValueThreshold: 100.0,
          ),
          pricingBoundaries: PricingBoundaries(
            maxPriceDropPercentage: 0.15,
            minProfitMargin: 25.0,
            repricingFrequency: RepricingFrequency.daily,
            enableAutomaticRepricing: true,
            categoryLimits: {},
          ),
          notificationPreferences: NotificationPreferences(
            highValueOpportunities: true,
            urgentBuyerMessages: true,
            dailyPerformanceSummaries: false,
            priceAdjustmentAlerts: true,
            agentRecommendations: true,
            systemAlerts: true,
            preferredMethod: NotificationMethod.push,
            agentSpecificNotifications: {},
          ),
          agentBehavior: AgentBehaviorSettings(
            aggressivenessLevel: 0.6,
            enableProactiveRecommendations: true,
            enableAutomaticOptimization: true,
            riskTolerance: 0.5,
            agentSpecificSettings: {},
          ),
          lastUpdated: DateTime.now(),
        );

        expect(settings.id, equals('settings_001'));
        expect(settings.userId, equals('user_001'));
        expect(settings.decisionAuthority.mode, equals(DecisionMode.collaborative));
        expect(settings.pricingBoundaries.maxPriceDropPercentage, equals(0.15));
        expect(settings.notificationPreferences.highValueOpportunities, equals(true));
        expect(settings.agentBehavior.aggressivenessLevel, equals(0.6));
      });
    });

    group('Service Mock Data', () {
      test('AgentInsightsService should return mock recommendations', () async {
        final recommendations = await agentInsightsService.getProactiveRecommendations();
        
        expect(recommendations, isNotEmpty);
        expect(recommendations.first.agentType, equals('market'));
        expect(recommendations.first.confidence, greaterThan(0.0));
        expect(recommendations.first.potentialImpact, greaterThan(0.0));
      });

      test('AgentInsightsService should return mock discoveries', () async {
        final discoveries = await agentInsightsService.getAgentDiscoveries();
        
        expect(discoveries, isNotEmpty);
        expect(discoveries.first.agentType, equals('market'));
        expect(discoveries.first.confidence, greaterThan(0.0));
        expect(discoveries.first.potentialValue, greaterThan(0.0));
      });

      test('PartnershipSettingsService should return default settings', () async {
        final settings = await partnershipSettingsService.getPartnershipSettings();
        
        expect(settings.id, equals('default_settings'));
        expect(settings.decisionAuthority.mode, equals(DecisionMode.collaborative));
        expect(settings.pricingBoundaries.enableAutomaticRepricing, equals(true));
        expect(settings.notificationPreferences.highValueOpportunities, equals(true));
        expect(settings.agentBehavior.enableProactiveRecommendations, equals(true));
      });
    });

    group('V2 Partnership Philosophy Validation', () {
      test('should validate human-agent collaboration principles', () {
        // Test that V2 models support partnership approach
        final recommendation = ProactiveRecommendation(
          id: 'test',
          agentId: 'market_agent',
          agentType: 'market',
          title: 'Partnership Test',
          description: 'Agent-initiated recommendation',
          type: RecommendationType.opportunity,
          confidence: 0.9,
          potentialImpact: 200.0,
          data: {},
          createdAt: DateTime.now(),
          priority: RecommendationPriority.high,
          availableActions: [RecommendationAction.accept, RecommendationAction.dismiss],
        );

        // Verify agent can initiate recommendations (V2 principle)
        expect(recommendation.availableActions, contains(RecommendationAction.accept));
        expect(recommendation.confidence, greaterThan(0.8)); // High confidence for partnership
        
        // Test decision authority supports collaboration
        final authority = DecisionAuthority(
          mode: DecisionMode.collaborative,
          agentAuthorities: {'market_agent': AgentAuthorityLevel.suggest},
          autoApprovalThreshold: 0.8,
          requireConfirmationForHighValue: true,
          highValueThreshold: 100.0,
        );

        expect(authority.mode, equals(DecisionMode.collaborative));
        expect(authority.requireConfirmationForHighValue, equals(true));
      });

      test('should validate shared responsibility model', () {
        final behavior = AgentBehaviorSettings(
          aggressivenessLevel: 0.6, // Balanced partnership
          enableProactiveRecommendations: true, // Agent initiative
          enableAutomaticOptimization: true, // Agent autonomy within bounds
          riskTolerance: 0.5, // Moderate risk for partnership
          agentSpecificSettings: {
            'market_agent': AgentSpecificBehavior(
              enabled: true,
              aggressivenessOverride: 0.7,
              allowedActions: ['analyze_market', 'suggest_pricing'],
              restrictedActions: ['auto_purchase'], // Human retains control
            ),
          },
        );

        expect(behavior.enableProactiveRecommendations, equals(true));
        expect(behavior.agentSpecificSettings['market_agent']?.restrictedActions, 
               contains('auto_purchase')); // Human keeps final purchase decisions
      });
    });
  });
}
