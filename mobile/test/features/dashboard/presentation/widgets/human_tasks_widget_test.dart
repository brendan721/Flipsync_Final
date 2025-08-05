import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/features/dashboard/presentation/widgets/human_tasks_widget.dart';

void main() {
  group('HumanTasksWidget', () {
    late List<HumanTask> testTasks;

    setUp(() {
      testTasks = [
        HumanTask(
          id: '1',
          title: 'MacBook Air M2',
          description: 'Condition assessment needed',
          type: HumanTaskType.conditionAssessment,
          priority: HumanTaskPriority.high,
          productId: 'macbook-001',
          createdAt: DateTime.now(),
        ),
        HumanTask(
          id: '2',
          title: 'Vintage Camera',
          description: 'Completeness check required',
          type: HumanTaskType.completenessCheck,
          priority: HumanTaskPriority.medium,
          productId: 'camera-001',
          createdAt: DateTime.now().subtract(Duration(hours: 2)),
        ),
        HumanTask(
          id: '3',
          title: 'iPhone 13 Pro Max',
          description: 'Photos needed for listing',
          type: HumanTaskType.photoCapture,
          priority: HumanTaskPriority.medium,
          productId: 'iphone-001',
          createdAt: DateTime.now().subtract(Duration(hours: 3)),
        ),
        HumanTask(
          id: '4',
          title: 'Designer Watch',
          description: 'Authenticity verification needed',
          type: HumanTaskType.authenticity,
          priority: HumanTaskPriority.urgent,
          productId: 'watch-001',
          createdAt: DateTime.now().subtract(Duration(hours: 4)),
        ),
      ];
    });

    testWidgets('should display human tasks correctly', (WidgetTester tester) async {
      // Arrange
      final tappedTasks = <String>[];

      // Act
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HumanTasksWidget(
              tasks: testTasks,
              onTaskTap: (task) {
                tappedTasks.add(task.id);
              },
            ),
          ),
        ),
      );

      // Assert
      expect(find.text('Items Needing Your Attention'), findsOneWidget);
      expect(find.text('MacBook Air M2'), findsOneWidget);
      expect(find.text('Vintage Camera'), findsOneWidget);
      expect(find.text('iPhone 13 Pro Max'), findsOneWidget);
      expect(find.text('Condition assessment needed'), findsOneWidget);
      expect(find.text('Completeness check required'), findsOneWidget);
      expect(find.text('Photos needed for listing'), findsOneWidget);
    });

    testWidgets('should show only top 3 tasks by default', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HumanTasksWidget(
              tasks: testTasks,
              onTaskTap: (task) {},
            ),
          ),
        ),
      );

      // Should show first 3 tasks
      expect(find.text('MacBook Air M2'), findsOneWidget);
      expect(find.text('Vintage Camera'), findsOneWidget);
      expect(find.text('iPhone 13 Pro Max'), findsOneWidget);
      // Should not show the fourth one
      expect(find.text('Designer Watch'), findsNothing);
    });

    testWidgets('should handle task tap', (WidgetTester tester) async {
      // Arrange
      final tappedTasks = <String>[];

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HumanTasksWidget(
              tasks: testTasks,
              onTaskTap: (task) {
                tappedTasks.add(task.id);
              },
            ),
          ),
        ),
      );

      // Act
      await tester.tap(find.text('MacBook Air M2'));
      await tester.pump();

      // Assert
      expect(tappedTasks, contains('1'));
    });

    testWidgets('should display priority badges correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HumanTasksWidget(
              tasks: testTasks,
              onTaskTap: (task) {},
            ),
          ),
        ),
      );

      expect(find.text('High'), findsOneWidget);
      expect(find.text('Medium'), findsNWidgets(2));
    });

    testWidgets('should display correct task type icons', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HumanTasksWidget(
              tasks: testTasks,
              onTaskTap: (task) {},
            ),
          ),
        ),
      );

      // Should have different task type icons
      expect(find.byIcon(Icons.search), findsOneWidget); // condition assessment
      expect(find.byIcon(Icons.checklist), findsOneWidget); // completeness check
      expect(find.byIcon(Icons.camera_alt), findsOneWidget); // photo capture
    });

    testWidgets('should show View All button when more than 3 tasks', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HumanTasksWidget(
              tasks: testTasks, // 4 tasks
              onTaskTap: (task) {},
              onViewAll: () {},
            ),
          ),
        ),
      );

      expect(find.text('View All'), findsOneWidget);
    });

    testWidgets('should not show View All button when 3 or fewer tasks', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HumanTasksWidget(
              tasks: testTasks.take(3).toList(),
              onTaskTap: (task) {},
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
            body: HumanTasksWidget(
              tasks: testTasks,
              onTaskTap: (task) {},
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

    testWidgets('should show action buttons when tasks exist', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HumanTasksWidget(
              tasks: testTasks,
              onTaskTap: (task) {},
            ),
          ),
        ),
      );

      expect(find.text('Assess Items'), findsOneWidget);
    });

    testWidgets('should show Schedule Later button when callback provided', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HumanTasksWidget(
              tasks: testTasks,
              onTaskTap: (task) {},
              onScheduleLater: () {},
            ),
          ),
        ),
      );

      expect(find.text('Schedule Later'), findsOneWidget);
    });

    testWidgets('should handle Schedule Later callback', (WidgetTester tester) async {
      // Arrange
      bool scheduleLaterPressed = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HumanTasksWidget(
              tasks: testTasks,
              onTaskTap: (task) {},
              onScheduleLater: () {
                scheduleLaterPressed = true;
              },
            ),
          ),
        ),
      );

      // Act
      await tester.tap(find.text('Schedule Later'));
      await tester.pump();

      // Assert
      expect(scheduleLaterPressed, isTrue);
    });

    testWidgets('should display empty state when no tasks', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HumanTasksWidget(
              tasks: [],
              onTaskTap: (task) {},
            ),
          ),
        ),
      );

      expect(find.text('All caught up!'), findsOneWidget);
      expect(find.text('No items need your attention right now'), findsOneWidget);
      expect(find.byIcon(Icons.check_circle), findsOneWidget);
    });

    testWidgets('should handle Assess Items button tap', (WidgetTester tester) async {
      // Arrange
      final tappedTasks = <String>[];

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: HumanTasksWidget(
              tasks: testTasks,
              onTaskTap: (task) {
                tappedTasks.add(task.id);
              },
            ),
          ),
        ),
      );

      // Act
      await tester.tap(find.text('Assess Items'));
      await tester.pump();

      // Assert - Should tap the first task
      expect(tappedTasks, contains('1'));
    });
  });
}
