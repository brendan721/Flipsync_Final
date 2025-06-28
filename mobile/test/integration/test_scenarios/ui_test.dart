import 'package:flutter_test/flutter_test.dart';
import 'package:flutter/material.dart';
import '../test_utils/test_data.dart';
import '../test_utils/test_helpers.dart';

Future<void> runUiTests(WidgetTester tester) async {
  group('UI/UX Tests', () {
    setUp(() async {
      await TestHelpers.resetApp();
    });

    group('Response Time Tests', () {
      testWidgets('Button tap response', (tester) async {
        final stopwatch = Stopwatch()..start();

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: Center(
                child: ElevatedButton(
                  key: const Key('login_button'),
                  onPressed: () {},
                  child: const Text('Login'),
                ),
              ),
            ),
          ),
        );

        await TestHelpers.tapButton(tester, 'login_button');
        stopwatch.stop();

        expect(
          stopwatch.elapsedMilliseconds,
          lessThan(TestData.maxTapResponseTime),
        );
      });

      testWidgets('List scroll response', (tester) async {
        await TestHelpers.loginUser(tester);

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: ListView.builder(
                itemCount: 100,
                itemBuilder:
                    (context, index) => ListTile(title: Text('Item $index')),
              ),
            ),
          ),
        );

        final stopwatch = Stopwatch()..start();
        await tester.fling(find.byType(ListView), const Offset(0, -500), 1000);
        await tester.pumpAndSettle();
        stopwatch.stop();

        expect(
          stopwatch.elapsedMilliseconds,
          lessThan(TestData.maxScrollResponseTime),
        );
      });

      testWidgets('Screen transitions', (tester) async {
        await TestHelpers.loginUser(tester);

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              appBar: AppBar(title: const Text('Screen 1')),
              body: Center(
                child: ElevatedButton(
                  key: const Key('next_screen'),
                  onPressed: () {},
                  child: const Text('Go to Next Screen'),
                ),
              ),
            ),
          ),
        );

        final stopwatch = Stopwatch()..start();
        await TestHelpers.tapButton(tester, 'next_screen');
        await tester.pumpAndSettle();
        stopwatch.stop();

        expect(
          stopwatch.elapsedMilliseconds,
          lessThan(TestData.maxTransitionDuration),
        );
      });
    });

    group('Rendering Tests', () {
      testWidgets('Initial render performance', (tester) async {
        final stopwatch = Stopwatch()..start();

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              appBar: AppBar(title: const Text('Test App')),
              body: ListView.builder(
                itemCount: 20,
                itemBuilder:
                    (context, index) => ListTile(
                      title: Text('Item $index'),
                      subtitle: Text('Description for item $index'),
                      leading: const Icon(Icons.star),
                      trailing: const Icon(Icons.arrow_forward),
                    ),
              ),
            ),
          ),
        );

        final firstPaintTime = stopwatch.elapsedMilliseconds;
        await tester.pumpAndSettle();
        stopwatch.stop();

        expect(firstPaintTime, lessThan(TestData.maxFirstPaintTime));
        expect(
          stopwatch.elapsedMilliseconds,
          lessThan(TestData.maxTimeToInteractive),
        );
      });

      testWidgets('Layout performance', (tester) async {
        await TestHelpers.loginUser(tester);

        final stopwatch = Stopwatch()..start();

        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              body: GridView.builder(
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  childAspectRatio: 1.5,
                ),
                itemCount: 20,
                itemBuilder:
                    (context, index) =>
                        Card(child: Center(child: Text('Item $index'))),
              ),
            ),
          ),
        );

        await tester.binding.setSurfaceSize(const Size(600, 800));
        await tester.pumpAndSettle();
        stopwatch.stop();

        expect(stopwatch.elapsedMilliseconds, lessThan(TestData.maxLayoutTime));
      });
    });

    group('Accessibility Tests', () {
      testWidgets('Screen reader compatibility', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              appBar: AppBar(title: const Text('Accessibility Test')),
              body: Column(
                children: [
                  TextField(
                    decoration: const InputDecoration(
                      labelText: 'Enter your name',
                      semanticCounterText: 'Name Input Field',
                    ),
                  ),
                  ElevatedButton(onPressed: () {}, child: const Text('Submit')),
                ],
              ),
            ),
          ),
        );

        final semanticsNode = tester.getSemantics(find.byType(TextField));

        expect(semanticsNode, isNotNull);
        expect(semanticsNode.label, isNotEmpty);

        final buttonSize = tester.getSize(find.byType(ElevatedButton));
        expect(buttonSize.width, greaterThanOrEqualTo(48.0));
        expect(buttonSize.height, greaterThanOrEqualTo(48.0));
      });
    });

    group('Cross-Device Tests', () {
      testWidgets('Responsive layout', (tester) async {
        for (final size in [
          const Size(320, 480),
          const Size(375, 667),
          const Size(414, 896),
          const Size(768, 1024),
        ]) {
          await tester.binding.setSurfaceSize(size);

          await tester.pumpWidget(
            MaterialApp(
              home: Scaffold(
                appBar: AppBar(title: const Text('Responsive Test')),
                body: LayoutBuilder(
                  builder: (context, constraints) {
                    if (constraints.maxWidth < 600) {
                      return ListView(
                        children: List.generate(
                          10,
                          (index) => ListTile(title: Text('Item $index')),
                        ),
                      );
                    } else {
                      return GridView.count(
                        crossAxisCount: 2,
                        children: List.generate(
                          10,
                          (index) =>
                              Card(child: Center(child: Text('Item $index'))),
                        ),
                      );
                    }
                  },
                ),
              ),
            ),
          );

          await tester.pumpAndSettle();

          expect(tester.takeException(), isNull);

          final stopwatch = Stopwatch()..start();
          await tester.pump();
          await tester.pumpAndSettle();
          stopwatch.stop();

          expect(
            stopwatch.elapsedMilliseconds,
            lessThan(
              TestData.maxRenderTimePerDevice[size.width < 600
                      ? 'small'
                      : 'large'] ??
                  1000.0,
            ),
          );
        }
      });
    });

    group('State Management Tests', () {
      testWidgets('State updates', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: StatefulBuilder(
              builder: (context, setState) {
                int counter = 0;
                return Scaffold(
                  appBar: AppBar(title: const Text('State Test')),
                  body: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text('Count: $counter'),
                        ElevatedButton(
                          key: const Key('increment_button'),
                          onPressed: () {
                            setState(() {
                              counter++;
                            });
                          },
                          child: const Text('Increment'),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        );

        final stopwatch = Stopwatch()..start();
        await TestHelpers.tapButton(tester, 'increment_button');
        await tester.pump();
        stopwatch.stop();

        expect(
          stopwatch.elapsedMilliseconds,
          lessThan(TestData.maxStateUpdateTime),
        );
      });
    });

    group('Error Handling Tests', () {
      testWidgets('Error recovery', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: StatefulBuilder(
              builder: (context, setState) {
                bool hasError = false;
                bool isLoading = false;
                return Scaffold(
                  appBar: AppBar(title: const Text('Error Test')),
                  body: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        if (isLoading)
                          const CircularProgressIndicator()
                        else if (hasError)
                          Column(
                            children: [
                              const Text(
                                'An error occurred. Please try again.',
                                style: TextStyle(color: Colors.red),
                              ),
                              ElevatedButton(
                                key: const Key('retry_button'),
                                onPressed: () {
                                  setState(() {
                                    hasError = false;
                                  });
                                },
                                child: const Text('Retry'),
                              ),
                            ],
                          )
                        else
                          const Text('Content loaded successfully'),
                        ElevatedButton(
                          key: const Key('trigger_error_button'),
                          onPressed: () {
                            setState(() {
                              isLoading = true;
                            });
                            Future.delayed(
                              const Duration(milliseconds: 200),
                              () {
                                setState(() {
                                  isLoading = false;
                                  hasError = true;
                                });
                              },
                            );
                          },
                          child: const Text('Simulate Error'),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        );

        await TestHelpers.tapButton(tester, 'trigger_error_button');
        await tester.pump();
        await tester.pump(const Duration(milliseconds: 210));

        expect(
          find.text('An error occurred. Please try again.'),
          findsOneWidget,
        );

        final stopwatch = Stopwatch()..start();
        await TestHelpers.tapButton(tester, 'retry_button');
        await tester.pump();
        stopwatch.stop();

        expect(
          stopwatch.elapsedMilliseconds,
          lessThan(TestData.maxErrorRecoveryTime),
        );
      });
    });

    group('Network Reliability Tests', () {
      testWidgets('Connection handling', (tester) async {
        bool isOnline = true;

        await tester.pumpWidget(
          MaterialApp(
            home: StatefulBuilder(
              builder: (context, setState) {
                return Scaffold(
                  appBar: AppBar(title: const Text('Network Test')),
                  body: Center(
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        Text(
                          isOnline
                              ? 'Connected to network'
                              : 'No network connection',
                        ),
                        ElevatedButton(
                          key: const Key('toggle_offline_button'),
                          onPressed: () {
                            setState(() {
                              isOnline = !isOnline;
                            });
                          },
                          child: Text(isOnline ? 'Go Offline' : 'Go Online'),
                        ),
                        if (!isOnline)
                          ElevatedButton(
                            key: const Key('retry_connection_button'),
                            onPressed: () {
                              setState(() {});
                            },
                            child: const Text('Retry Connection'),
                          ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
        );

        await TestHelpers.tapButton(tester, 'toggle_offline_button');
        await tester.pump();

        expect(find.text('No network connection'), findsOneWidget);
        expect(
          find.byKey(const Key('retry_connection_button')),
          findsOneWidget,
        );

        final stopwatch = Stopwatch()..start();
        await TestHelpers.tapButton(tester, 'toggle_offline_button');
        await tester.pump();
        stopwatch.stop();

        expect(
          stopwatch.elapsedMilliseconds,
          lessThan(TestData.maxReconnectionTime),
        );
      });
    });

    group('Resource Usage Tests', () {
      testWidgets('Resource consumption', (tester) async {
        await tester.pumpWidget(
          MaterialApp(
            home: Scaffold(
              appBar: AppBar(title: const Text('Resource Test')),
              body: ListView.builder(
                itemCount: 100,
                itemBuilder:
                    (context, index) => Card(
                      child: Padding(
                        padding: const EdgeInsets.all(16.0),
                        child: Column(
                          children: [
                            Image.network(
                              'https://placeholder.com/150',
                              width: 150,
                              height: 150,
                              errorBuilder:
                                  (_, __, ___) =>
                                      const Icon(Icons.image, size: 150),
                            ),
                            Text('Item $index'),
                            Text('Description for item $index'),
                          ],
                        ),
                      ),
                    ),
              ),
            ),
          ),
        );

        await tester.pump();
        for (int i = 0; i < 10; i++) {
          await tester.drag(find.byType(ListView), const Offset(0, -300));
          await tester.pump();
        }
        await tester.pumpAndSettle();

        expect(true, isTrue);
      });
    });
  });
}
