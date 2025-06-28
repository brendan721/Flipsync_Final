/// Test script for Phase 2C Enhanced Workflow Progress Visualization
/// This script demonstrates the enhanced workflow progress features

import 'dart:convert';
import 'package:flutter/material.dart';
import 'lib/core/models/workflow_models.dart';
import 'lib/features/chat/widgets/workflow_progress_widget.dart';

void main() {
  runApp(const WorkflowProgressTestApp());
}

class WorkflowProgressTestApp extends StatelessWidget {
  const WorkflowProgressTestApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Phase 2C: Workflow Progress Test',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        useMaterial3: true,
      ),
      home: const WorkflowProgressTestScreen(),
    );
  }
}

class WorkflowProgressTestScreen extends StatefulWidget {
  const WorkflowProgressTestScreen({Key? key}) : super(key: key);

  @override
  State<WorkflowProgressTestScreen> createState() => _WorkflowProgressTestScreenState();
}

class _WorkflowProgressTestScreenState extends State<WorkflowProgressTestScreen> {
  List<WorkflowStatus> testWorkflows = [];
  Map<String, bool> expandedWorkflows = {};

  @override
  void initState() {
    super.initState();
    _generateTestWorkflows();
  }

  void _generateTestWorkflows() {
    // Create test workflow data based on real API response
    final testData = [
      {
        'workflow_id': 'fd007be9-fa72-4b3f-8028-bb5d2e0687cf',
        'workflow_type': 'pricing_strategy',
        'participating_agents': ['market', 'content', 'executive'],
        'status': 'failed',
        'context': {
          'user_message': 'I need help with pricing strategy for my electronics products',
          'conversation_id': '570790c5-ea66-4d32-bc4f-75eeaa73148b',
          'trigger_phrases': ['pricing strategy', 'pricing strategy'],
          'confidence': 0.4,
          'triggered_via': 'rest_api',
        },
        'results': {},
        'start_time': '2025-06-16T23:18:32.878538+00:00',
        'end_time': '2025-06-16T23:18:32.879916+00:00',
        'error_message': 'Unknown workflow type: pricing_strategy',
      },
      {
        'workflow_id': 'test-workflow-in-progress',
        'workflow_type': 'product_analysis',
        'participating_agents': ['market', 'content', 'executive', 'logistics'],
        'status': 'inProgress',
        'context': {
          'user_message': 'Can you analyze this MacBook Pro M3 for selling potential?',
          'confidence': 0.8,
          'triggered_via': 'rest_api',
        },
        'results': {},
        'start_time': DateTime.now().subtract(const Duration(minutes: 2)).toIso8601String(),
        'progress': 0.6,
        'current_phase': 'Market Analysis',
      },
      {
        'workflow_id': 'test-workflow-completed',
        'workflow_type': 'listing_optimization',
        'participating_agents': ['content', 'market'],
        'status': 'completed',
        'context': {
          'user_message': 'Help me optimize my iPhone listing',
          'confidence': 0.9,
          'triggered_via': 'websocket',
        },
        'results': {
          'optimized_title': 'iPhone 15 Pro Max 256GB - Unlocked, Excellent Condition',
          'suggested_price': 899.99,
          'improvements': ['Better keywords', 'Enhanced description', 'Competitive pricing'],
        },
        'start_time': DateTime.now().subtract(const Duration(hours: 1)).toIso8601String(),
        'end_time': DateTime.now().subtract(const Duration(minutes: 45)).toIso8601String(),
        'progress': 1.0,
      },
    ];

    setState(() {
      testWorkflows = testData.map((data) => WorkflowStatus.fromJson(data)).toList();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Phase 2C: Enhanced Workflow Progress'),
        backgroundColor: const Color(0xFF2563EB),
        foregroundColor: Colors.white,
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _generateTestWorkflows,
            tooltip: 'Refresh Test Data',
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    const Color(0xFF2563EB).withOpacity(0.1),
                    const Color(0xFF3B82F6).withOpacity(0.1),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: const Color(0xFF2563EB).withOpacity(0.3),
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(
                        Icons.hub,
                        color: Color(0xFF2563EB),
                        size: 24,
                      ),
                      SizedBox(width: 12),
                      Text(
                        'Phase 2C: Enhanced Progress Visualization',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                          color: Color(0xFF1F2937),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Real-time multi-agent workflow coordination with detailed progress tracking',
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[600],
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      _buildStatCard('Active Workflows', testWorkflows.length.toString(), Icons.sync),
                      const SizedBox(width: 16),
                      _buildStatCard('Agents Coordinated', '12', Icons.smart_toy),
                      const SizedBox(width: 16),
                      _buildStatCard('Success Rate', '85%', Icons.check_circle),
                    ],
                  ),
                ],
              ),
            ),
            
            const SizedBox(height: 24),
            
            // Workflow Progress Widgets
            if (testWorkflows.isNotEmpty) ...[
              const Text(
                'Active Workflows',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: Color(0xFF1F2937),
                ),
              ),
              const SizedBox(height: 16),
              ...testWorkflows.map((workflow) {
                final isExpanded = expandedWorkflows[workflow.workflowId] ?? false;
                return WorkflowProgressWidget(
                  workflow: workflow,
                  isExpanded: isExpanded,
                  onToggleExpanded: () {
                    setState(() {
                      expandedWorkflows[workflow.workflowId] = !isExpanded;
                    });
                  },
                );
              }).toList(),
            ] else ...[
              const Center(
                child: Column(
                  children: [
                    Icon(
                      Icons.hourglass_empty,
                      size: 64,
                      color: Colors.grey,
                    ),
                    SizedBox(height: 16),
                    Text(
                      'No active workflows',
                      style: TextStyle(
                        fontSize: 16,
                        color: Colors.grey,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // Simulate triggering a new workflow
          _simulateNewWorkflow();
        },
        backgroundColor: const Color(0xFF2563EB),
        child: const Icon(Icons.add, color: Colors.white),
      ),
    );
  }

  Widget _buildStatCard(String title, String value, IconData icon) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: Colors.grey[300]!),
        ),
        child: Column(
          children: [
            Icon(icon, color: const Color(0xFF2563EB), size: 20),
            const SizedBox(height: 4),
            Text(
              value,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: Color(0xFF1F2937),
              ),
            ),
            Text(
              title,
              style: TextStyle(
                fontSize: 10,
                color: Colors.grey[600],
              ),
              textAlign: TextAlign.center,
            ),
          ],
        ),
      ),
    );
  }

  void _simulateNewWorkflow() {
    final newWorkflow = WorkflowStatus(
      workflowId: 'test-${DateTime.now().millisecondsSinceEpoch}',
      workflowType: 'market_research',
      participatingAgents: ['market', 'trend_detector', 'competitor_analyzer'],
      status: WorkflowStatusType.inProgress,
      context: {
        'user_message': 'Research the gaming laptop market',
        'confidence': 0.7,
        'triggered_via': 'test_simulation',
      },
      results: {},
      startTime: DateTime.now(),
      progress: 0.2,
      currentPhase: 'Data Collection',
    );

    setState(() {
      testWorkflows.add(newWorkflow);
    });

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('🚀 New workflow triggered: Market Research'),
        backgroundColor: Color(0xFF2563EB),
      ),
    );
  }
}
