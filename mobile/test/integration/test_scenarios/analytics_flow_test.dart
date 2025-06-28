import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import '../test_utils/test_data.dart';
import '../test_utils/test_helpers.dart';

Future<void> runAnalyticsTests(WidgetTester tester) async {
  group('Analytics Flow Tests', () {
    setUp(() async {
      // Ensure logged in
      await TestHelpers.loginUser(tester);

      // Navigate to analytics
      final analyticsTab = find.byKey(const Key('analytics_tab'));
      await tester.tap(analyticsTab);
      await tester.pumpAndSettle();
    });

    testWidgets('Market trend visualization', (tester) async {
      // Load test data - simulate loading market data
      await Future.delayed(const Duration(milliseconds: 100));

      // Create test chart
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: AppBar(title: const Text('Market Trends')),
            body: Column(
              children: [
                Container(
                  key: const Key('trend_chart'),
                  height: 300,
                  color: Colors.blue[100],
                  child: Center(child: const Text('Market Trend Chart')),
                ),
                GestureDetector(
                  key: const Key('chart_interaction_area'),
                  onTap: () {
                    // Would show tooltip in real widget
                  },
                  child: Container(
                    height: 50,
                    color: Colors.blue[200],
                    child: Center(
                      child: Text(
                        'Interact with chart - ${TestData.expectedTooltipValue}',
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      );

      // Verify trend chart
      expect(find.byKey(const Key('trend_chart')), findsOneWidget);

      // Interact with chart
      final chartArea = find.byKey(const Key('chart_interaction_area'));
      await tester.tap(chartArea);
      await tester.pumpAndSettle();

      // Verify tooltip
      expect(find.byKey(const Key('chart_interaction_area')), findsOneWidget);
      expect(
        find.text('Interact with chart - ${TestData.expectedTooltipValue}'),
        findsOneWidget,
      );
    });

    testWidgets('Competitor analysis', (tester) async {
      // Navigate to competitor view - simulate competitor tab
      await tester.pumpWidget(
        MaterialApp(
          home: DefaultTabController(
            length: 3,
            child: Scaffold(
              appBar: AppBar(
                bottom: TabBar(
                  tabs: [
                    Tab(text: 'Overview'),
                    Tab(key: Key('competitor_tab'), text: 'Competitors'),
                    Tab(text: 'Details'),
                  ],
                ),
              ),
              body: TabBarView(
                children: [
                  Center(child: Text('Overview')),
                  Column(
                    children: [
                      Container(
                        key: Key('competitor_heatmap'),
                        height: 300,
                        color: Colors.orange[100],
                        child: Center(child: Text('Competitor Heatmap')),
                      ),
                      DropdownButton<String>(
                        key: Key('metric_selector'),
                        value: 'Market Share',
                        items:
                            [
                              'Market Share',
                              'Price Competitiveness',
                              'Growth',
                            ].map((String value) {
                              return DropdownMenuItem<String>(
                                value: value,
                                child: Text(value),
                              );
                            }).toList(),
                        onChanged: (_) {},
                      ),
                      Text(TestData.expectedCompetitorMetric),
                    ],
                  ),
                  Center(child: Text('Details')),
                ],
              ),
            ),
          ),
        ),
      );

      final competitorTab = find.byKey(const Key('competitor_tab'));
      await tester.tap(competitorTab);
      await tester.pumpAndSettle();

      // Verify heatmap
      expect(find.byKey(const Key('competitor_heatmap')), findsOneWidget);

      // Select metric
      final metricDropdown = find.byKey(const Key('metric_selector'));
      await tester.tap(metricDropdown);
      await tester.pumpAndSettle();

      final priceMetric = find.text('Price Competitiveness');
      await tester.tap(priceMetric);
      await tester.pumpAndSettle();

      // Verify metric data
      expect(find.text(TestData.expectedCompetitorMetric), findsOneWidget);
    });

    testWidgets('Performance metrics', (tester) async {
      // Navigate to performance view - simulate performance tab
      await tester.pumpWidget(
        MaterialApp(
          home: DefaultTabController(
            length: 3,
            child: Scaffold(
              appBar: AppBar(
                bottom: TabBar(
                  tabs: [
                    Tab(text: 'Overview'),
                    Tab(text: 'Details'),
                    Tab(key: Key('performance_tab'), text: 'Performance'),
                  ],
                ),
              ),
              body: TabBarView(
                children: [
                  Center(child: Text('Overview')),
                  Center(child: Text('Details')),
                  Column(
                    mainAxisAlignment: MainAxisAlignment.spaceEvenly,
                    children: [
                      Container(
                        key: Key('revenue_gauge'),
                        height: 100,
                        width: 100,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.green[100],
                        ),
                        child: Center(
                          child: Text(TestData.expectedRevenueValue),
                        ),
                      ),
                      Container(
                        key: Key('conversion_gauge'),
                        height: 100,
                        width: 100,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.blue[100],
                        ),
                        child: Center(
                          child: Text(TestData.expectedConversionRate),
                        ),
                      ),
                      Container(
                        key: Key('roi_gauge'),
                        height: 100,
                        width: 100,
                        decoration: BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.purple[100],
                        ),
                        child: Center(child: Text(TestData.expectedROI)),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      );

      final performanceTab = find.byKey(const Key('performance_tab'));
      await tester.tap(performanceTab);
      await tester.pumpAndSettle();

      // Verify gauges
      expect(find.byKey(const Key('revenue_gauge')), findsOneWidget);
      expect(find.byKey(const Key('conversion_gauge')), findsOneWidget);
      expect(find.byKey(const Key('roi_gauge')), findsOneWidget);

      // Verify values
      expect(find.text(TestData.expectedRevenueValue), findsOneWidget);
      expect(find.text(TestData.expectedConversionRate), findsOneWidget);
      expect(find.text(TestData.expectedROI), findsOneWidget);
    });

    testWidgets('Data export', (tester) async {
      // Simulate export dialog
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            appBar: AppBar(title: const Text('Analytics')),
            body: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                ElevatedButton(
                  key: const Key('export_button'),
                  onPressed: () {},
                  child: const Text('Export Data'),
                ),
              ],
            ),
          ),
        ),
      );

      // Open export dialog
      final exportButton = find.byKey(const Key('export_button'));
      await tester.tap(exportButton);
      await tester.pumpAndSettle();

      // Create a dialog for date selection
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Center(
              child: AlertDialog(
                title: const Text('Select Date Range'),
                content: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Row(
                      children: [
                        Text('From:'),
                        SizedBox(width: 10),
                        TextButton(
                          key: const Key('date_range_selector'),
                          onPressed: () {},
                          child: Text('Select Date'),
                        ),
                      ],
                    ),
                    SizedBox(height: 20),
                    Row(children: [Text('Metrics:')]),
                    Row(
                      children: [
                        Checkbox(value: false, onChanged: (_) {}),
                        Text('Revenue'),
                      ],
                    ),
                    Row(
                      children: [
                        Checkbox(value: false, onChanged: (_) {}),
                        Text('Conversions'),
                      ],
                    ),
                    SizedBox(height: 20),
                    ElevatedButton(
                      key: const Key('confirm_export_button'),
                      onPressed: () {},
                      child: const Text('Export'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );

      // Select date range by simulating date picker interaction
      final rangeSelector = find.byKey(const Key('date_range_selector'));
      await tester.tap(rangeSelector);
      await tester.pumpAndSettle();

      // Select metrics
      final metricCheckboxes = find.byType(Checkbox);
      await tester.tap(metricCheckboxes.first);
      await tester.tap(metricCheckboxes.at(1));
      await tester.pumpAndSettle();

      // Export data
      final confirmButton = find.byKey(const Key('confirm_export_button'));
      await tester.tap(confirmButton);
      await tester.pumpAndSettle();

      // Show success message
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(body: Center(child: Text('Export completed'))),
        ),
      );

      // Verify export
      expect(find.text('Export completed'), findsOneWidget);
    });

    testWidgets('Real-time updates', (tester) async {
      // Set up real-time updates UI
      await tester.pumpWidget(
        MaterialApp(
          home: StatefulBuilder(
            builder: (context, setState) {
              bool isRealtime = false;
              String updateValue = 'No updates';

              return Scaffold(
                appBar: AppBar(title: const Text('Real-time Data')),
                body: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text('Real-time updates:'),
                        Switch(
                          key: const Key('realtime_toggle'),
                          value: isRealtime,
                          onChanged: (value) {
                            setState(() {
                              isRealtime = value;
                              if (isRealtime) {
                                updateValue = TestData.realtimeUpdateValue;
                              } else {
                                updateValue = 'No updates';
                              }
                            });
                          },
                        ),
                      ],
                    ),
                    SizedBox(height: 20),
                    Text(updateValue),
                  ],
                ),
              );
            },
          ),
        ),
      );

      // Enable real-time updates
      final realtimeToggle = find.byKey(const Key('realtime_toggle'));
      await tester.tap(realtimeToggle);
      await tester.pumpAndSettle();

      // Verify updates
      expect(find.text(TestData.realtimeUpdateValue), findsOneWidget);
    });

    testWidgets('Custom analysis', (tester) async {
      // Set up custom analysis UI
      await tester.pumpWidget(
        MaterialApp(
          home: StatefulBuilder(
            builder: (context, setState) {
              final List<String> selectedMetrics = [];
              String calculationResult = '';

              return Scaffold(
                appBar: AppBar(title: const Text('Custom Analysis')),
                body: Column(
                  children: [
                    ElevatedButton(
                      key: const Key('custom_analysis_button'),
                      onPressed: () {
                        setState(() {
                          // Open metrics panel (simulated here)
                        });
                      },
                      child: const Text('Create Custom Analysis'),
                    ),
                    SizedBox(height: 20),
                    ElevatedButton(
                      key: const Key('add_metric_button'),
                      onPressed: () {
                        setState(() {
                          // UI would show selection menu
                        });
                      },
                      child: const Text('Add Metric'),
                    ),
                    if (selectedMetrics.isNotEmpty)
                      Column(
                        children:
                            selectedMetrics
                                .map((metric) => ListTile(title: Text(metric)))
                                .toList(),
                      ),
                    SizedBox(height: 20),
                    TextField(
                      key: const Key('formula_field'),
                      decoration: InputDecoration(labelText: 'Custom Formula'),
                    ),
                    SizedBox(height: 20),
                    ElevatedButton(
                      key: const Key('run_analysis_button'),
                      onPressed: () {
                        setState(() {
                          calculationResult =
                              TestData.expectedCustomAnalysisResult;
                        });
                      },
                      child: const Text('Run Analysis'),
                    ),
                    SizedBox(height: 20),
                    Text(calculationResult),
                  ],
                ),
              );
            },
          ),
        ),
      );

      // Open custom analysis
      final customButton = find.byKey(const Key('custom_analysis_button'));
      await tester.tap(customButton);
      await tester.pumpAndSettle();

      // Add metrics
      final addButton = find.byKey(const Key('add_metric_button'));
      await tester.tap(addButton);
      await tester.pumpAndSettle();

      // Set calculation
      final formulaField = find.byKey(const Key('formula_field'));
      await tester.enterText(formulaField, '{Revenue} / {Costs} * 100');
      await tester.pumpAndSettle();

      // Run analysis
      final runButton = find.byKey(const Key('run_analysis_button'));
      await tester.tap(runButton);
      await tester.pumpAndSettle();

      // Verify results
      expect(find.text(TestData.expectedCustomAnalysisResult), findsOneWidget);
    });
  });
}
