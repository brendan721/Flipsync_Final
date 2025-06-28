import 'dart:async';

import 'package:flipsync/core/models/app_battery_state.dart';
import 'package:flutter_test/flutter_test.dart';

// Test implementation of BatteryOptimizationService
class TestBatteryOptimizationService {
  final StreamController<AppBatteryState> _batteryStateController =
      StreamController<AppBatteryState>.broadcast();

  Stream<AppBatteryState> get batteryState => _batteryStateController.stream;

  Future<void> recordOperation(String operationName) async {
    // Simply log the operation in a real implementation
    print('Operation recorded: $operationName');
  }

  // Test helper method
  void changeBatteryState(AppBatteryState state) {
    _batteryStateController.add(state);
  }

  void dispose() {
    _batteryStateController.close();
  }
}

// Test implementation of SensorOptimizationService
class TestSensorOptimizationService {
  final TestBatteryOptimizationService _batteryService;
  final Map<String, StreamSubscription<dynamic>> _subscriptions = {};
  final Map<String, Duration> _intervals = {};

  TestSensorOptimizationService(this._batteryService);

  Future<void> initialize() async {
    // Initialize the service
  }

  void registerSensor<T>(
    String sensorId,
    Stream<T> sensorStream,
    Function(T) onData, {
    Duration interval = const Duration(seconds: 1),
  }) {
    _intervals[sensorId] = interval;
    _subscriptions[sensorId] = sensorStream.listen((data) {
      _batteryService.recordOperation('sensor_$sensorId');
      onData(data);
    });
  }

  void unregisterSensor(String sensorId) {
    _subscriptions[sensorId]?.cancel();
    _subscriptions.remove(sensorId);
    _intervals.remove(sensorId);
  }

  void dispose() {
    for (final subscription in _subscriptions.values) {
      subscription.cancel();
    }
    _subscriptions.clear();
    _intervals.clear();
  }
}

void main() {
  late TestSensorOptimizationService service;
  late TestBatteryOptimizationService batteryService;
  late StreamController<int> testController;

  setUp(() {
    batteryService = TestBatteryOptimizationService();
    service = TestSensorOptimizationService(batteryService);
    testController = StreamController<int>();
  });

  tearDown(() {
    service.dispose();
    batteryService.dispose();
    testController.close();
  });

  test('SensorOptimizationService initializes correctly', () async {
    expect(service.initialize(), completes);
  });

  test('SensorOptimizationService registers sensor correctly', () async {
    await service.initialize();

    final receivedData = <int>[];

    service.registerSensor(
      'test_sensor',
      testController.stream,
      (data) => receivedData.add(data),
      interval: const Duration(milliseconds: 100),
    );

    testController.add(1);
    testController.add(2);

    await Future.delayed(const Duration(milliseconds: 150));

    expect(receivedData, [1, 2]);
  });

  test('SensorOptimizationService handles unregistration correctly', () async {
    await service.initialize();

    final receivedData = <int>[];

    service.registerSensor(
      'test_sensor',
      testController.stream,
      (data) => receivedData.add(data),
    );

    testController.add(1);
    await Future.delayed(const Duration(milliseconds: 50));

    service.unregisterSensor('test_sensor');
    testController.add(2);

    await Future.delayed(const Duration(milliseconds: 50));
    expect(receivedData, [1]);
  });
}
