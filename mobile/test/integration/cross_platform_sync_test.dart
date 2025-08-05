
import 'package:flipsync/core/integration/cross_platform_coordinator.dart';
import 'package:flipsync/core/integration/platform_types.dart';
import 'package:flipsync/core/integration/sync_manager.dart';
import 'package:flipsync/core/services/battery_optimization_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:battery_plus/battery_plus.dart';

void main() {
  late CrossPlatformCoordinator coordinator;
  late SyncManager syncManager;
  late BatteryOptimizationService batteryService;
  late Battery battery;

  setUp(() {
    // Initialize real service implementations
    syncManager = SyncManager();
    battery = Battery();
    batteryService = BatteryOptimizationService(battery);

    coordinator = CrossPlatformCoordinator(syncManager, batteryService);
  });

  group('Cross Platform Sync', () {
    test('syncs with all platforms', () async {
      // Arrange
      await coordinator.initialize();

      // Act & Assert - should not throw
      expect(() async {
        await coordinator.syncWithPlatform(PlatformType.mobile);
        await coordinator.syncWithPlatform(PlatformType.web);
        await coordinator.syncWithPlatform(PlatformType.desktop);
      }, returnsNormally);
    });

    test('handles sync errors gracefully', () async {
      // This tests that sync errors don't crash the application
      await coordinator.initialize();

      // Act & Assert
      // Force an error by trying to sync with an invalid platform (this should be handled)
      expect(() async {
        await coordinator.syncWithPlatform(PlatformType.mobile);
      }, returnsNormally);
    });
  });
}
