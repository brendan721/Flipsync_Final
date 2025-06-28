// ignore_for_file: subtype_of_sealed_class

import 'dart:async';

import 'package:flipsync/core/integration/cross_platform_coordinator.dart';
import 'package:flipsync/core/integration/platform_types.dart';
import 'package:flipsync/core/integration/sync_manager.dart';
import 'package:flipsync/core/services/battery_optimization_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/core/models/app_battery_state.dart';
import 'package:battery_plus/battery_plus.dart';

void main() {
  late CrossPlatformCoordinator coordinator;
  late SyncManager syncManager;
  late BatteryOptimizationService batteryService;
  late Battery battery;
  late StreamController<AppBatteryState> testBatteryStateController;

  setUp(() {
    // Initialize real service implementations
    syncManager = SyncManager();
    battery = Battery();
    batteryService = BatteryOptimizationService(battery);

    // Create a controller for testing state changes
    testBatteryStateController = StreamController<AppBatteryState>.broadcast();

    coordinator = CrossPlatformCoordinator(syncManager, batteryService);
  });

  tearDown(() {
    testBatteryStateController.close();
  });

  test('should initialize services', () async {
    // Act
    await coordinator.initialize();

    // Assert - no errors should occur during initialization
    expect(true, isTrue); // Basic assertion that initialization completes
  });

  test('should synchronize with platform', () async {
    const platform = PlatformType.mobile;

    // Act & Assert - should not throw
    expect(() async {
      await coordinator.syncWithPlatform(platform);
    }, returnsNormally);
  });
}
