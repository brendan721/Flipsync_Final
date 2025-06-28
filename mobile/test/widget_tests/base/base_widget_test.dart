import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/core/theme/app_theme.dart';
import 'package:flipsync/core/design/flipsync_colors.dart';
import 'package:flipsync/core/design/flipsync_spacing.dart';
import 'package:flipsync/core/design/flipsync_typography.dart';
import 'package:flipsync/core/widgets/base_widget.dart';

// Create a concrete implementation of BaseWidget for testing
class TestBaseWidget extends BaseWidget {
  const TestBaseWidget({super.key});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BaseWidget.defaultDecoration,
      padding: BaseWidget.defaultPadding,
      child: Column(
        children: [
          Text('Headline', style: FlipSyncTypography.textTheme.headlineLarge),
          Text('Body', style: FlipSyncTypography.textTheme.bodyLarge),
          Text('Label', style: FlipSyncTypography.textTheme.labelSmall),
        ],
      ),
    );
  }
}

void main() {
  group('BaseWidget Theme Tests', () {
    testWidgets('provides correct theme data', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: TestBaseWidget()));

      final widget = tester.widget<TestBaseWidget>(find.byType(TestBaseWidget));
      expect(widget.theme, equals(AppTheme.lightTheme));
      expect(widget.textTheme, equals(FlipSyncTypography.textTheme));
    });

    testWidgets('applies correct text styles', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: TestBaseWidget()));

      expect(find.text('Headline'), findsOneWidget);
      expect(find.text('Body'), findsOneWidget);
      expect(find.text('Label'), findsOneWidget);

      final headlineText = tester.widget<Text>(find.text('Headline'));
      final bodyText = tester.widget<Text>(find.text('Body'));
      final labelText = tester.widget<Text>(find.text('Label'));

      expect(headlineText.style, equals(FlipSyncTypography.textTheme.headlineLarge));
      expect(bodyText.style, equals(FlipSyncTypography.textTheme.bodyLarge));
      expect(labelText.style, equals(FlipSyncTypography.textTheme.labelSmall));
    });
  });

  group('BaseWidget Spacing Tests', () {
    testWidgets('provides correct border radius', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: TestBaseWidget()));

      final widget = tester.widget<TestBaseWidget>(find.byType(TestBaseWidget));
      expect(widget.borderRadius, equals(FlipSyncSpacing.borderRadius));
    });

    testWidgets('applies correct padding', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: TestBaseWidget()));

      final container = tester.widget<Container>(find.byType(Container));
      expect(
        container.padding,
        equals(EdgeInsets.all(FlipSyncSpacing.medium)),
      );
    });
  });

  group('BaseWidget Color Tests', () {
    testWidgets('provides correct colors', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: TestBaseWidget()));

      final widget = tester.widget<TestBaseWidget>(find.byType(TestBaseWidget));
      expect(widget.primary, equals(FlipSyncColors.primary));
      expect(widget.background, equals(FlipSyncColors.background));
      expect(widget.surface, equals(FlipSyncColors.surface));
      expect(widget.error, equals(FlipSyncColors.error));
      expect(widget.success, equals(FlipSyncColors.success));
    });
  });

  group('BaseWidget Common Widgets Tests', () {
    testWidgets('renders loading indicator correctly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Builder(
            builder: (context) => const TestBaseWidget().loadingIndicator,
          ),
        ),
      );

      expect(find.byType(CircularProgressIndicator), findsOneWidget);
    });

    testWidgets('renders error widget correctly', (tester) async {
      const errorMessage = 'Test error message';
      await tester.pumpWidget(
        MaterialApp(
          home: Builder(
            builder: (context) => const TestBaseWidget().errorWidget(errorMessage),
          ),
        ),
      );

      expect(find.byIcon(Icons.error_outline), findsOneWidget);
      expect(find.text(errorMessage), findsOneWidget);

      final errorText = tester.widget<Text>(find.text(errorMessage));
      expect(errorText.style?.color, equals(FlipSyncColors.error));
    });

    testWidgets('renders empty state widget correctly', (tester) async {
      const emptyMessage = 'No items found';
      await tester.pumpWidget(
        MaterialApp(
          home: Builder(
            builder: (context) => const TestBaseWidget().emptyStateWidget(emptyMessage),
          ),
        ),
      );

      expect(find.byIcon(Icons.inbox_outlined), findsOneWidget);
      expect(find.text(emptyMessage), findsOneWidget);

      final emptyText = tester.widget<Text>(find.text(emptyMessage));
      expect(emptyText.style?.color, equals(Colors.grey));
    });

    testWidgets('renders empty state with custom icon', (tester) async {
      const emptyMessage = 'No items found';
      await tester.pumpWidget(
        MaterialApp(
          home: Builder(
            builder: (context) => const TestBaseWidget().emptyStateWidget(
              emptyMessage,
              icon: Icons.search,
            ),
          ),
        ),
      );

      expect(find.byIcon(Icons.search), findsOneWidget);
      expect(find.text(emptyMessage), findsOneWidget);
    });
  });

  group('BaseWidget Decoration Tests', () {
    testWidgets('applies correct decoration', (tester) async {
      await tester.pumpWidget(const MaterialApp(home: TestBaseWidget()));

      final container = tester.widget<Container>(find.byType(Container));
      final decoration = container.decoration as BoxDecoration;

      expect(decoration.color, equals(FlipSyncColors.surface));
      expect(
        decoration.borderRadius,
        equals(BorderRadius.circular(FlipSyncSpacing.borderRadius)),
      );
      expect(decoration.boxShadow?.length, equals(1));

      final shadow = decoration.boxShadow!.first;
      expect(shadow.color, equals(FlipSyncColors.shadow.withOpacity(0.1)));
      expect(shadow.blurRadius, equals(8));
      expect(shadow.offset, equals(const Offset(0, 2)));
    });
  });
}
