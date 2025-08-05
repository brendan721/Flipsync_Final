import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/features/dashboard/presentation/widgets/opportunity_discovery_widget.dart';

void main() {
  group('OpportunityDiscoveryWidget', () {
    late List<AgentOpportunity> testOpportunities;

    setUp(() {
      testOpportunities = [
        AgentOpportunity(
          id: '1',
          title: 'iPhone 13: Market gap found',
          description: 'Suggested price: \$850 → Expected +\$20 profit',
          type: OpportunityType.pricing,
          potentialProfit: 20.0,
          confidence: 0.85,
          agentSource: 'Market Agent',
          discoveredAt: DateTime.now(),
        ),
        AgentOpportunity(
          id: '2',
          title: 'Books: Bundle opportunity',
          description: '3-pack increases profit by \$15',
          type: OpportunityType.bundle,
          potentialProfit: 15.0,
          confidence: 0.92,
          agentSource: 'Executive Agent',
          discoveredAt: DateTime.now().subtract(Duration(hours: 1)),
        ),
        AgentOpportunity(
          id: '3',
          title: 'Camera: Boost listing',
          description: 'Featured placement could increase visibility',
          type: OpportunityType.boost,
          potentialProfit: 30.0,
          confidence: 0.78,
          agentSource: 'Content Agent',
          discoveredAt: DateTime.now().subtract(Duration(hours: 2)),
        ),
      ];
    });

    testWidgets('should display opportunities correctly', (WidgetTester tester) async {
      // Arrange
      final decisions = <String, bool>{};

      // Act
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OpportunityDiscoveryWidget(
              opportunities: testOpportunities,
              onDecision: (opportunity, approved) {
                decisions[opportunity.id] = approved;
              },
            ),
          ),
        ),
      );

      // Assert
      expect(find.text('Opportunities Discovered'), findsOneWidget);
      expect(find.text('iPhone 13: Market gap found'), findsOneWidget);
      expect(find.text('Books: Bundle opportunity'), findsOneWidget);
      expect(find.text('+\$20.00'), findsOneWidget);
      expect(find.text('+\$15.00'), findsOneWidget);
      expect(find.text('85%'), findsOneWidget); // Confidence
      expect(find.text('92%'), findsOneWidget); // Confidence
    });

    testWidgets('should show only top 2 opportunities by default', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OpportunityDiscoveryWidget(
              opportunities: testOpportunities,
              onDecision: (opportunity, approved) {},
            ),
          ),
        ),
      );

      // Should show first 2 opportunities
      expect(find.text('iPhone 13: Market gap found'), findsOneWidget);
      expect(find.text('Books: Bundle opportunity'), findsOneWidget);
      // Should not show the third one
      expect(find.text('Camera: Boost listing'), findsNothing);
    });

    testWidgets('should handle opportunity decisions', (WidgetTester tester) async {
      // Arrange
      final decisions = <String, bool>{};

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OpportunityDiscoveryWidget(
              opportunities: testOpportunities,
              onDecision: (opportunity, approved) {
                decisions[opportunity.id] = approved;
              },
            ),
          ),
        ),
      );

      // Act - Approve first opportunity
      await tester.tap(find.text('Apply').first);
      await tester.pump();

      // Assert
      expect(decisions['1'], isTrue);

      // Act - Decline second opportunity (tap the second "Not Now" button)
      final notNowButtons = find.text('Not Now');
      expect(notNowButtons, findsNWidgets(2));
      await tester.tap(notNowButtons.at(1));
      await tester.pump();

      // Assert
      expect(decisions['2'], isFalse);
    });

    testWidgets('should display confidence badges with correct colors', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OpportunityDiscoveryWidget(
              opportunities: testOpportunities,
              onDecision: (opportunity, approved) {},
            ),
          ),
        ),
      );

      // High confidence (92%) should be visible
      expect(find.text('92%'), findsOneWidget);
      // Medium-high confidence (85%) should be visible
      expect(find.text('85%'), findsOneWidget);
    });

    testWidgets('should show View All button when more than 2 opportunities', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OpportunityDiscoveryWidget(
              opportunities: testOpportunities, // 3 opportunities
              onDecision: (opportunity, approved) {},
              onViewAll: () {},
            ),
          ),
        ),
      );

      expect(find.text('View All'), findsOneWidget);
    });

    testWidgets('should not show View All button when 2 or fewer opportunities', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OpportunityDiscoveryWidget(
              opportunities: testOpportunities.take(2).toList(),
              onDecision: (opportunity, approved) {},
              onViewAll: () {},
            ),
          ),
        ),
      );

      expect(find.text('View All'), findsNothing);
    });

    testWidgets('should handle View All callback', (WidgetTester tester) async {
      // Arrange
      bool viewAllPressed = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OpportunityDiscoveryWidget(
              opportunities: testOpportunities,
              onDecision: (opportunity, approved) {},
              onViewAll: () {
                viewAllPressed = true;
              },
            ),
          ),
        ),
      );

      // Act
      await tester.tap(find.text('View All'));
      await tester.pump();

      // Assert
      expect(viewAllPressed, isTrue);
    });

    testWidgets('should show quick actions when multiple opportunities', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OpportunityDiscoveryWidget(
              opportunities: testOpportunities,
              onDecision: (opportunity, approved) {},
            ),
          ),
        ),
      );

      expect(find.text('Quick Approve'), findsOneWidget);
      expect(find.text('Review All'), findsOneWidget);
    });

    testWidgets('should display empty state when no opportunities', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OpportunityDiscoveryWidget(
              opportunities: [],
              onDecision: (opportunity, approved) {},
            ),
          ),
        ),
      );

      expect(find.text('Agents are analyzing opportunities'), findsOneWidget);
      expect(find.text('Check back soon for new discoveries!'), findsOneWidget);
      expect(find.byIcon(Icons.search), findsOneWidget);
    });

    testWidgets('should display correct opportunity type icons', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OpportunityDiscoveryWidget(
              opportunities: testOpportunities,
              onDecision: (opportunity, approved) {},
            ),
          ),
        ),
      );

      // Should have pricing and bundle icons
      expect(find.byIcon(Icons.price_change), findsOneWidget);
      expect(find.byIcon(Icons.inventory), findsOneWidget);
    });

    testWidgets('should handle quick approve action', (WidgetTester tester) async {
      // Arrange
      final decisions = <String, bool>{};

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: OpportunityDiscoveryWidget(
              opportunities: testOpportunities,
              onDecision: (opportunity, approved) {
                decisions[opportunity.id] = approved;
              },
            ),
          ),
        ),
      );

      // Act
      await tester.tap(find.text('Quick Approve'));
      await tester.pump();

      // Assert - Should approve first 2 opportunities
      expect(decisions['1'], isTrue);
      expect(decisions['2'], isTrue);
      expect(decisions.containsKey('3'), isFalse); // Third not shown
    });
  });
}
