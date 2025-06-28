import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/core/design/tokens/colors.dart';
import 'package:flipsync/core/design/tokens/typography.dart';
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

      // Should have background by default
      final container = tester.widget<Container>(find.byType(Container));
      expect(container.decoration, isNotNull);

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
        equals(FlipSyncTypography.bodyLarge.fontSize),
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

      expect(find.byType(Container), findsOneWidget);
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
      expect(
        find.byType(SizedBox),
        findsOneWidget,
      );

      final spacer = tester.widget<SizedBox>(find.byType(SizedBox));
      expect(spacer.height, equals(16));
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
      expect(column.mainAxisSize, equals(MainAxisSize.min));
    });
  });
}
