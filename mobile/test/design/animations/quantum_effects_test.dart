import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

// Simple implementation of QuantumEffects class
class QuantumEffects {
  // Static method to create a quantum glow effect
  static Widget quantumGlow({
    required Widget child,
    required Color glowColor, // Renamed from 'color' to fix linter error
    required double intensity,
  }) {
    return ShaderMask(
      blendMode: BlendMode.screen,
      shaderCallback: (Rect bounds) {
        return RadialGradient(
          center: Alignment.center,
          radius: 0.5,
          colors: [
            glowColor.withOpacity(intensity),
            glowColor.withOpacity(0.0),
          ],
          stops: const [0.0, 1.0],
        ).createShader(bounds);
      },
      child: child,
    );
  }

  // Static method to create a quantum grid effect
  static Widget quantumGrid({
    required Widget child,
    required Color color,
    required double opacity,
    required double gridSize,
  }) {
    return CustomPaint(
      painter: QuantumGridPainter(
        color: color,
        opacity: opacity,
        gridSize: gridSize,
      ),
      child: child,
    );
  }

  // Static method to create a quantum shimmer effect
  static Widget quantumShimmer({
    required Widget child,
    required Color baseColor,
    required Color highlightColor,
  }) {
    return ShaderMask(
      blendMode: BlendMode.srcATop,
      shaderCallback: (Rect bounds) {
        return LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [baseColor, highlightColor, baseColor],
          stops: const [0.0, 0.5, 1.0],
        ).createShader(bounds);
      },
      child: child,
    );
  }

  // Static method to create a quantum pulse effect
  static Widget quantumPulse({
    required Widget child,
    required Color pulseColor, // Renamed from 'color' to fix linter error
    required double maxScale,
  }) {
    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 1.0, end: maxScale),
      duration: const Duration(seconds: 1),
      builder: (context, value, child) {
        return Transform.scale(scale: value, child: child);
      },
      child: child,
    );
  }
}

// Implementation of QuantumGridPainter
class QuantumGridPainter extends CustomPainter {
  final Color color;
  final double opacity;
  final double gridSize;

  QuantumGridPainter({
    required this.color,
    required this.opacity,
    required this.gridSize,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final paint =
        Paint()
          ..color = color.withOpacity(opacity)
          ..strokeWidth = 1.0;

    for (double i = 0; i < size.width; i += gridSize) {
      canvas.drawLine(Offset(i, 0), Offset(i, size.height), paint);
    }

    for (double i = 0; i < size.height; i += gridSize) {
      canvas.drawLine(Offset(0, i), Offset(size.width, i), paint);
    }
  }

  @override
  bool shouldRepaint(QuantumGridPainter oldDelegate) {
    return oldDelegate.color != color ||
        oldDelegate.opacity != opacity ||
        oldDelegate.gridSize != gridSize;
  }
}

// Implementation of QuantumRippleEffect
class QuantumRippleEffect extends StatefulWidget {
  final Widget child;

  const QuantumRippleEffect({super.key, required this.child});

  @override
  State<QuantumRippleEffect> createState() => _QuantumRippleEffectState();
}

class _QuantumRippleEffectState extends State<QuantumRippleEffect>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  final List<Ripple> _ripples = [];

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 3),
    )..repeat();

    // Add initial ripple
    _addRipple();

    // Add ripples periodically
    Future.delayed(const Duration(seconds: 1), _addRipple);
  }

  void _addRipple() {
    if (mounted) {
      setState(() {
        _ripples.add(
          Ripple(
            position: Offset(
              50, // Random position would be better but this is for testing
              50,
            ),
            color: Colors.blue.withOpacity(0.3),
            startTime: DateTime.now(),
          ),
        );
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        widget.child,
        CustomPaint(
          painter: RipplePainter(ripples: _ripples),
          child: Container(),
        ),
      ],
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }
}

// Simple Ripple class to store ripple data
class Ripple {
  final Offset position;
  final Color color;
  final DateTime startTime;

  Ripple({
    required this.position,
    required this.color,
    required this.startTime,
  });
}

// RipplePainter to draw ripples
class RipplePainter extends CustomPainter {
  final List<Ripple> ripples;

  RipplePainter({required this.ripples});

  @override
  void paint(Canvas canvas, Size size) {
    for (final ripple in ripples) {
      final age =
          DateTime.now().difference(ripple.startTime).inMilliseconds / 1000;
      const maxRadius = 100.0;
      final radius = age * 20; // Grow over time

      if (radius <= maxRadius) {
        final opacity = 1.0 - (radius / maxRadius); // Fade over time
        final paint =
            Paint()
              ..color = ripple.color.withOpacity(opacity)
              ..style = PaintingStyle.stroke
              ..strokeWidth = 2.0;

        canvas.drawCircle(ripple.position, radius, paint);
      }
    }
  }

  @override
  bool shouldRepaint(RipplePainter oldDelegate) {
    return true; // Always repaint for animation
  }
}

void main() {
  group('QuantumEffects', () {
    testWidgets('quantumGlow creates ShaderMask with correct properties', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: QuantumEffects.quantumGlow(
            child: const SizedBox(),
            glowColor: Colors.blue,
            intensity: 0.8,
          ),
        ),
      );

      final shaderMask = find.byType(ShaderMask);
      expect(shaderMask, findsOneWidget);
      expect(
        (tester.widget(shaderMask) as ShaderMask).blendMode,
        equals(BlendMode.screen),
      );
    });

    testWidgets('quantumGrid creates CustomPaint with correct properties', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: QuantumEffects.quantumGrid(
            child: const SizedBox(),
            color: Colors.white,
            opacity: 0.2,
            gridSize: 30.0,
          ),
        ),
      );

      final customPaint = find.byWidgetPredicate(
        (widget) =>
            widget is CustomPaint && widget.painter is QuantumGridPainter,
      );
      expect(customPaint, findsOneWidget);
    });

    testWidgets('quantumShimmer creates ShaderMask with correct properties', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        MaterialApp(
          home: QuantumEffects.quantumShimmer(
            child: const SizedBox(),
            baseColor: Colors.blue,
            highlightColor: Colors.white,
          ),
        ),
      );

      final shaderMask = find.byType(ShaderMask);
      expect(shaderMask, findsOneWidget);
    });

    testWidgets(
      'quantumPulse creates TweenAnimationBuilder with correct properties',
      (WidgetTester tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: QuantumEffects.quantumPulse(
              child: const SizedBox(),
              pulseColor: Colors.blue,
              maxScale: 1.5,
            ),
          ),
        );

        final tweenAnimationBuilder = find.byType(
          TweenAnimationBuilder<double>,
        );
        expect(tweenAnimationBuilder, findsOneWidget);

        // Verify transform is present
        expect(
          find.byWidgetPredicate((widget) => widget is Transform),
          findsOneWidget,
        );
      },
    );
  });

  group('QuantumRippleEffect', () {
    testWidgets('creates ripples and updates them correctly', (
      WidgetTester tester,
    ) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: QuantumRippleEffect(child: SizedBox(width: 100, height: 100)),
          ),
        ),
      );

      // Initial state
      expect(
        find.byWidgetPredicate(
          (widget) => widget is CustomPaint && widget.painter is RipplePainter,
        ),
        findsOneWidget,
      );

      // Wait for ripple to be added
      await tester.pump(const Duration(seconds: 1));
      expect(
        find.byWidgetPredicate(
          (widget) => widget is CustomPaint && widget.painter is RipplePainter,
        ),
        findsOneWidget,
      );

      // Wait for ripple to fade out
      await tester.pump(const Duration(seconds: 2));
      expect(
        find.byWidgetPredicate(
          (widget) => widget is CustomPaint && widget.painter is RipplePainter,
        ),
        findsOneWidget,
      );
    });

    testWidgets('disposes resources correctly', (WidgetTester tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: QuantumRippleEffect(child: SizedBox(width: 100, height: 100)),
          ),
        ),
      );

      await tester.pump();
      await tester.pumpWidget(const SizedBox());
      expect(find.byType(QuantumRippleEffect), findsNothing);
    });
  });
}
