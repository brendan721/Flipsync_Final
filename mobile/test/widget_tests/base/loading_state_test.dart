import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/core/design/flipsync_colors.dart';
import 'package:flipsync/core/design/flipsync_typography.dart';
import 'package:flipsync/core/widgets/loading_state.dart';

void main() {
  group('LoadingState Widget Tests', () {
    testWidgets('renders with default properties', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LoadingState(),
          ),
        ),
      );

      // Should show spinner by default
      expect(find.byType(CircularProgressIndicator), findsOneWidget);

      // Should not show message by default
      expect(find.byType(Text), findsNothing);
    });

    testWidgets('renders with custom message', (tester) async {
      const testMessage = 'Loading data...';
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LoadingState(message: testMessage),
          ),
        ),
      );

      expect(find.text(testMessage), findsOneWidget);

      final text = tester.widget<Text>(find.text(testMessage));
      expect(
        text.style?.color,
        equals(FlipSyncColors.textSecondary),
      );
      expect(
        text.style?.fontSize,
        equals(FlipSyncTypography.textTheme.bodyLarge?.fontSize),
      );
      expect(text.textAlign, equals(TextAlign.center));
    });

    testWidgets('can use custom loader', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LoadingState(
              customLoader: Icon(Icons.hourglass_empty),
              message: 'Test',
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.hourglass_empty), findsOneWidget);
      expect(find.text('Test'), findsOneWidget);
    });

    testWidgets('can show overlay', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LoadingState(
              showOverlay: true,
            ),
          ),
        ),
      );

      // Should have overlay container with correct background
      final containers = tester.widgetList<Container>(find.byType(Container));
      final overlayContainer = containers.firstWhere(
        (container) => container.color != null,
      );
      expect(overlayContainer.color, equals(Colors.black.withValues(alpha: 0.3)));
    });

    testWidgets('spinner has correct color', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LoadingState(),
          ),
        ),
      );

      final spinner = tester.widget<CircularProgressIndicator>(
        find.byType(CircularProgressIndicator),
      );

      expect(
        (spinner.valueColor as AlwaysStoppedAnimation<Color>).value,
        equals(FlipSyncColors.primary),
      );
    });

    testWidgets('maintains proper spacing', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LoadingState(
              message: 'Test',
            ),
          ),
        ),
      );

      // Verify spacing between spinner and message
      final sizedBoxes = tester.widgetList<SizedBox>(find.byType(SizedBox));
      final spacer = sizedBoxes.firstWhere(
        (box) => box.width == null && box.height != null,
      );
      expect(spacer.height, equals(24.0));
    });

    testWidgets('centers content properly', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: LoadingState(
              message: 'Test',
            ),
          ),
        ),
      );

      expect(find.byType(Center), findsOneWidget);

      final column = tester.widget<Column>(find.byType(Column));
      expect(column.mainAxisSize, equals(MainAxisSize.max));
    });
  });
}
