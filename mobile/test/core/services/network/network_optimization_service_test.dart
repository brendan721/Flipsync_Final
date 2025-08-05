import 'dart:async';
import 'dart:io';

import 'package:flipsync/core/models/app_battery_state.dart';
import 'package:flipsync/core/services/battery/battery_optimization_service.dart';
import 'package:flipsync/core/services/network/network_optimization_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:hive/hive.dart';

// Direct implementation of BatteryOptimizationService for testing
class TestBatteryOptimizationService implements BatteryOptimizationService {
  // Test controller to manage app battery state
  final _batteryStateController = StreamController<AppBatteryState>.broadcast();
  AppBatteryState _currentState = AppBatteryState.normal;

  // Operation tracking for test control
  final Map<String, int> _operationCounts = {};
  final Map<String, DateTime> _lastOperationTime = {};
  bool _shouldThrottle = false;

  TestBatteryOptimizationService() {
    _batteryStateController.add(_currentState);
  }

  @override
  Stream<AppBatteryState> get batteryState => _batteryStateController.stream;

  @override
  AppBatteryState get currentState => _currentState;

  void setShouldThrottle(bool value) {
    _shouldThrottle = value;
  }

  @override
  Future<bool> shouldThrottleOperation(String operationType) async {
    return _shouldThrottle;
  }

  @override
  void recordOperation(String operationType) {
    _operationCounts[operationType] =
        (_operationCounts[operationType] ?? 0) + 1;
    _lastOperationTime[operationType] = DateTime.now();
  }

  @override
  bool isEssentialOperation(String operationType) {
    return operationType == 'high_priority';
  }

  @override
  Map<String, int> getOperationCounts() {
    return Map.unmodifiable(_operationCounts);
  }

  @override
  void resetOperationCounts() {
    _operationCounts.clear();
    _lastOperationTime.clear();
  }

  @override
  void setBatteryState(AppBatteryState state) {
    _currentState = state;
    _batteryStateController.add(state);
  }

  @override
  void dispose() {
    _batteryStateController.close();
  }
}

// Create test classes
enum ConnectivityResult { wifi, mobile, none }

class TestConnectivity {
  final _controller = StreamController<ConnectivityResult>.broadcast();
  ConnectivityResult _lastResult = ConnectivityResult.wifi;

  TestConnectivity() {
    _controller.add(_lastResult);
  }

  Stream<ConnectivityResult> get onConnectivityChanged => _controller.stream;

  Future<ConnectivityResult> checkConnectivity() async {
    return _lastResult;
  }

  void changeConnectivity(ConnectivityResult result) {
    _lastResult = result;
    _controller.add(result);
  }

  void dispose() {
    _controller.close();
  }
}

void main() {
  late NetworkOptimizationService networkOptimizationService;
  late TestBatteryOptimizationService batteryService;
  late TestConnectivity connectivity;
  late Directory tempDir;

  setUpAll(() async {
    tempDir = await Directory.systemTemp.createTemp('hive_test_');
    Hive.init(tempDir.path);
  });

  setUp(() {
    batteryService = TestBatteryOptimizationService();
    connectivity = TestConnectivity();

    // Create NetworkOptimizationService with our test service
    networkOptimizationService = NetworkOptimizationService(batteryService);
  });

  tearDown(() async {
    networkOptimizationService.dispose();
    batteryService.dispose();
    connectivity.dispose();
  });

  tearDownAll(() async {
    await tempDir.delete(recursive: true);
  });

  group('NetworkOptimizationService', () {
    test('initializes correctly', () async {
      await networkOptimizationService.initialize();
      expect(networkOptimizationService.isInitialized, isTrue);
    });

    test('enqueues and processes high priority requests immediately', () async {
      await networkOptimizationService.initialize();

      final request = NetworkRequestFunction<String>((
        endpoint, {
        body,
        headers,
      }) async {
        return 'success';
      });

      final result = await networkOptimizationService.enqueueRequest(
        'test_endpoint',
        request,
        NetworkRequestPriority.high,
      );

      expect(result, equals('success'));
    });

    test('throttles requests when battery optimization recommends', () async {
      // Set up throttling behavior for this test
      batteryService.setShouldThrottle(true);

      await networkOptimizationService.initialize();

      var requestCount = 0;
      final request = NetworkRequestFunction<String>((
        endpoint, {
        body,
        headers,
      }) async {
        requestCount++;
        return 'success';
      });

      final result = await networkOptimizationService.enqueueRequest(
        'test_endpoint',
        request,
        NetworkRequestPriority.low,
      );

      expect(result, isNull);
      expect(requestCount, equals(0));
    });

    test('processes requests based on priority', () async {
      await networkOptimizationService.initialize();

      final processedRequests = <String>[];
      final request = NetworkRequestFunction<String>((
        endpoint, {
        body,
        headers,
      }) async {
        processedRequests.add(endpoint);
        return 'success';
      });

      // Enqueue requests with different priorities
      await Future.wait([
        networkOptimizationService.enqueueRequest(
          'low_priority',
          request,
          NetworkRequestPriority.low,
        ),
        networkOptimizationService.enqueueRequest(
          'medium_priority',
          request,
          NetworkRequestPriority.medium,
        ),
        networkOptimizationService.enqueueRequest(
          'high_priority',
          request,
          NetworkRequestPriority.high,
        ),
      ]);

      // High priority should be processed first
      expect(processedRequests[0], equals('high_priority'));
    });

    test('handles errors gracefully', () async {
      await networkOptimizationService.initialize();

      final request = NetworkRequestFunction<String>((
        endpoint, {
        body,
        headers,
      }) async {
        throw Exception('Network error');
      });

      expect(
        () => networkOptimizationService.enqueueRequest(
          'test_endpoint',
          request,
          NetworkRequestPriority.high,
        ),
        throwsException,
      );
    });
  });
}
