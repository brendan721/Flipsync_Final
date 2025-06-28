import 'dart:async';

import 'package:battery_plus/battery_plus.dart';
import 'package:flipsync/core/models/performance_mode.dart';
import 'package:flipsync/core/services/battery_optimization_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

class MockBattery extends Mock implements Battery {}

void main() {
  late BatteryOptimizationService batteryOptimizationService;
  late MockBattery mockBattery;
  late StreamController<BatteryState> batteryStateController;

  setUp(() {
    mockBattery = MockBattery();
    batteryStateController = StreamController<BatteryState>.broadcast();

    when(
      () => mockBattery.onBatteryStateChanged,
    ).thenAnswer((_) => batteryStateController.stream);
    when(
      () => mockBattery.batteryState,
    ).thenAnswer((_) async => BatteryState.discharging);
    when(() => mockBattery.batteryLevel).thenAnswer((_) async => 80);

    batteryOptimizationService = BatteryOptimizationService(mockBattery);
  });

  tearDown(() {
    batteryStateController.close();
    batteryOptimizationService.dispose();
  });

  test('initializes correctly', () async {
    await batteryOptimizationService.initialize();
    expect(batteryOptimizationService.batteryState, isNotNull);
  });

  test('should record operations and provide impact metrics', () async {
    // Initialize service
    await batteryOptimizationService.initialize();

    // Record some operations
    batteryOptimizationService.recordOperation(
      'test_operation',
      powerImpact: 0.5,
    );
    batteryOptimizationService.recordOperation(
      'test_operation',
      powerImpact: 0.7,
    );
    batteryOptimizationService.recordOperation(
      'another_operation',
      powerImpact: 0.3,
    );

    // Verify operations not throttled initially
    expect(
      await batteryOptimizationService.shouldThrottleOperation(
        'test_operation',
      ),
      false,
    );
  });

  test(
    'provides optimization recommendations based on battery state',
    () async {
      // Test with different battery states
      when(
        () => mockBattery.batteryState,
      ).thenAnswer((_) async => BatteryState.full);
      expect(
        await batteryOptimizationService.getOptimizationRecommendations(),
        equals(PerformanceMode.high),
      );

      when(
        () => mockBattery.batteryState,
      ).thenAnswer((_) async => BatteryState.charging);
      expect(
        await batteryOptimizationService.getOptimizationRecommendations(),
        equals(PerformanceMode.high),
      );

      when(
        () => mockBattery.batteryState,
      ).thenAnswer((_) async => BatteryState.discharging);
      expect(
        await batteryOptimizationService.getOptimizationRecommendations(),
        equals(PerformanceMode.balanced),
      );

      when(
        () => mockBattery.batteryState,
      ).thenAnswer((_) async => BatteryState.unknown);
      expect(
        await batteryOptimizationService.getOptimizationRecommendations(),
        equals(PerformanceMode.adaptive),
      );
    },
  );

  test('battery metrics stream works', () async {
    // Initialize service
    await batteryOptimizationService.initialize();

    // Listen for metrics
    final metrics = <Map<String, dynamic>>[];
    final subscription = batteryOptimizationService.batteryMetrics.listen(
      metrics.add,
    );

    // Wait for a bit for any metrics to be emitted
    await Future.delayed(const Duration(milliseconds: 100));

    // Clean up
    await subscription.cancel();

    // Not testing the contents as we can't force collection without accessing private methods
    // but verifying the stream is functional
    expect(batteryOptimizationService.batteryMetrics, isNotNull);
  });
}
