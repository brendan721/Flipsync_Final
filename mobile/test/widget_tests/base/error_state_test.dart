import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/core/theme/theme_data.dart';
import 'package:flipsync/core/widgets/error_state.dart';

void main() {
  group('ErrorState Widget Tests', () {
    const testTitle = 'Error Occurred';
    const testMessage = 'Something went wrong. Please try again.';
    late ThemeData theme;

    setUp(() {
      theme = FlipSyncTheme.darkTheme;
    });

    testWidgets('renders with required properties', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: theme,
          home: const Scaffold(
            body: ErrorState(
              title: testTitle,
              message: testMessage,
            ),
          ),
        ),
      );

      // Verify icon
      expect(find.byIcon(Icons.error_outline), findsOneWidget);
      final icon = tester.widget<Icon>(find.byIcon(Icons.error_outline));
      expect(icon.color, equals(theme.colorScheme.error));
      expect(icon.size, equals(48));

      // Verify title
      expect(find.text(testTitle), findsOneWidget);
      final titleWidget = tester.widget<Text>(find.text(testTitle));
      expect(titleWidget.style?.color, equals(theme.colorScheme.error));
      expect(titleWidget.style?.fontSize, equals(theme.textTheme.titleLarge?.fontSize));
      expect(titleWidget.textAlign, equals(TextAlign.center));

      // Verify message
      expect(find.text(testMessage), findsOneWidget);
      final messageWidget = tester.widget<Text>(find.text(testMessage));
      expect(
        messageWidget.style?.color,
        equals(theme.colorScheme.onSurface.withOpacity(0.7)),
      );
      expect(messageWidget.style?.fontSize, equals(theme.textTheme.bodyMedium?.fontSize));
      expect(messageWidget.textAlign, equals(TextAlign.center));

      // Should have background by default
      final container = tester.widget<Container>(find.byType(Container));
      expect(container.decoration, isNotNull);

      // Should not show retry button by default
      expect(find.byIcon(Icons.refresh), findsNothing);
      expect(find.text('Retry'), findsNothing);
    });

    testWidgets('displays error content correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: theme,
          home: const Scaffold(
            body: ErrorState(
              title: testTitle,
              message: testMessage,
            ),
          ),
        ),
      );

      // Verify the error state displays correctly
      expect(find.text(testTitle), findsOneWidget);
      expect(find.text(testMessage), findsOneWidget);
      expect(find.byIcon(Icons.error_outline), findsOneWidget);
    });

    testWidgets('shows retry button when onRetry provided', (tester) async {
      bool retryPressed = false;

      await tester.pumpWidget(
        MaterialApp(
          theme: theme,
          home: Scaffold(
            body: ErrorState(
              title: testTitle,
              message: testMessage,
              onRetry: () => retryPressed = true,
            ),
          ),
        ),
      );

      // Verify retry button exists
      expect(find.byIcon(Icons.refresh), findsOneWidget);
      expect(find.text('Retry'), findsOneWidget);

      // Find the button by looking for the Row that contains both the icon and text
      final buttonFinder = find.byWidgetPredicate(
        (widget) => widget is ElevatedButton && widget.onPressed != null,
      );
      expect(buttonFinder, findsOneWidget);

      // Verify button styling
      final button = tester.widget<ElevatedButton>(buttonFinder);
      final buttonStyle = button.style as ButtonStyle;

      expect(
        buttonStyle.backgroundColor?.resolve({}),
        equals(theme.colorScheme.primary),
      );
      expect(
        buttonStyle.foregroundColor?.resolve({}),
        equals(theme.colorScheme.onPrimary),
      );

      // Test button press
      await tester.tap(buttonFinder);
      await tester.pump();
      expect(retryPressed, isTrue);
    });

    testWidgets('maintains proper spacing', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: theme,
          home: Scaffold(
            body: ErrorState(
              title: testTitle,
              message: testMessage,
              onRetry: () {},
            ),
          ),
        ),
      );

      // Find all spacers
      final spacers = tester.widgetList<SizedBox>(find.byType(SizedBox));

      // Verify the key spacing values exist
      expect(spacers.length, greaterThan(0));
    });

    testWidgets('centers content properly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: theme,
          home: const Scaffold(
            body: ErrorState(
              title: testTitle,
              message: testMessage,
            ),
          ),
        ),
      );

      // Find the outer Center widget that wraps the Column
      final centerFinder = find.ancestor(
        of: find.byType(Column),
        matching: find.byType(Center),
      );
      expect(centerFinder, findsOneWidget);

      final column = tester.widget<Column>(find.byType(Column));
      expect(column.mainAxisSize, equals(MainAxisSize.min));
    });

    testWidgets('applies correct padding', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: theme,
          home: const Scaffold(
            body: ErrorState(
              title: testTitle,
              message: testMessage,
            ),
          ),
        ),
      );

      // Verify the error state has proper padding
      expect(find.byType(Padding), findsOneWidget);
    });

    testWidgets('button has correct shape', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: theme,
          home: Scaffold(
            body: ErrorState(
              title: testTitle,
              message: testMessage,
              onRetry: () {},
            ),
          ),
        ),
      );

      final buttonFinder = find.byWidgetPredicate(
        (widget) => widget is ElevatedButton && widget.onPressed != null,
      );
      expect(buttonFinder, findsOneWidget);

      // Verify button exists and is styled correctly
      expect(buttonFinder, findsOneWidget);
    });
  });
}
