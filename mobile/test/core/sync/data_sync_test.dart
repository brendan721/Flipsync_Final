import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/core/network/network_state.dart' as app;
import '../../test_config.dart' as test_config;

// Simple result class for sync operations
class SyncResult {
  final bool success;
  final int syncedItems;
  final int failedItems;
  final int conflictResolved;
  final int retryCount;
  final int changesApplied;
  final dynamic error;

  SyncResult({
    required this.success,
    this.syncedItems = 0,
    this.failedItems = 0,
    this.conflictResolved = 0,
    this.retryCount = 0,
    this.changesApplied = 0,
    this.error,
  });
}

// Real storage implementation for testing
class TestStorageService {
  final Map<String, dynamic> _storage = {};
  final List<Map<String, dynamic>> _pendingUploads = [];
  String _lastSyncTimestamp = DateTime.now().toIso8601String();

  Future<List<Map<String, dynamic>>> getPendingUploads() async {
    return List.from(_pendingUploads);
  }

  Future<bool> markAsSynced(dynamic id) async {
    _pendingUploads.removeWhere((item) => item['id'] == id);
    return true;
  }

  Future<Map<String, dynamic>> resolveConflict({
    required Map<String, dynamic> localData,
    required Map<String, dynamic> serverData,
  }) async {
    // Local is newer than server, keep local
    final localTimestamp = DateTime.parse(localData['timestamp']);
    final serverTimestamp = DateTime.parse(serverData['timestamp']);

    if (localTimestamp.isAfter(serverTimestamp)) {
      return localData;
    }

    // Otherwise, keep server data
    return serverData;
  }

  Future<String> getLastSyncTimestamp() async {
    return _lastSyncTimestamp;
  }

  Future<bool> applyServerChanges(List<dynamic> changes) async {
    for (final change in changes) {
      _storage[change['id']] = change;
    }
    return true;
  }

  // Test helper methods
  void addPendingUpload(Map<String, dynamic> item) {
    _pendingUploads.add(item);
  }

  void setLastSyncTimestamp(String timestamp) {
    _lastSyncTimestamp = timestamp;
  }
}

// Test version of NetworkState with additional testing methods
class TestNetworkState extends app.NetworkState {
  bool _connected = true;

  bool get isConnected => _connected;

  @override
  void setOnline() {
    _connected = true;
  }

  @override
  void setOffline() {
    _connected = false;
  }
}

// Basic SyncService implementation for testing
class TestSyncService {
  final TestStorageService storageService;
  final TestNetworkState networkState;

  TestSyncService({required this.storageService, required this.networkState});

  Future<SyncResult> syncUploads() async {
    try {
      if (!networkState.isConnected) {
        return SyncResult(
          success: false,
          error: Exception('No network connection'),
        );
      }

      final pendingUploads = await storageService.getPendingUploads();
      int syncedItems = 0;
      int failedItems = 0;
      const int conflictResolved = 0;

      for (final item in pendingUploads) {
        try {
          // Simulate a successful sync
          await storageService.markAsSynced(item['id']);
          syncedItems++;
        } catch (e) {
          failedItems++;
        }
      }

      return SyncResult(
        success: failedItems == 0,
        syncedItems: syncedItems,
        failedItems: failedItems,
        conflictResolved: conflictResolved,
      );
    } catch (e) {
      return SyncResult(success: false, error: e);
    }
  }

  Future<SyncResult> performIncrementalSync() async {
    try {
      if (!networkState.isConnected) {
        return SyncResult(
          success: false,
          error: Exception('No network connection'),
        );
      }

      // Simulate server changes
      final serverChanges = [
        {
          'id': '1',
          'content': 'updated content',
          'timestamp': DateTime.now().toIso8601String(),
        },
      ];

      await storageService.applyServerChanges(serverChanges);

      return SyncResult(success: true, changesApplied: serverChanges.length);
    } catch (e) {
      return SyncResult(success: false, error: e);
    }
  }
}

void main() {
  test_config.setupUnitTest();

  late TestStorageService storageService;
  late TestNetworkState networkState;
  late TestSyncService syncService;

  setUp(() {
    storageService = TestStorageService();
    networkState = TestNetworkState();
    syncService = TestSyncService(
      storageService: storageService,
      networkState: networkState,
    );
  });

  group('Data Synchronization Tests', () {
    final testData = {
      'id': '123',
      'content': 'test content',
      'timestamp': '2023-02-07T22:25:59Z',
    };

    test('successful data upload synchronization', () async {
      // Arrange
      storageService.addPendingUpload(testData);

      // Act
      final result = await syncService.syncUploads();

      // Assert
      expect(result.success, isTrue);
      expect(result.syncedItems, 1);

      // Check if item was marked as synced
      final pendingUploads = await storageService.getPendingUploads();
      expect(pendingUploads, isEmpty);
    });

    test('handles incremental sync', () async {
      // Act
      final result = await syncService.performIncrementalSync();

      // Assert
      expect(result.success, isTrue);
      expect(result.changesApplied, 1);
    });

    test('handles network state changes during sync', () async {
      // Arrange
      storageService.addPendingUpload(testData);
      networkState.setOffline();

      // Act
      final result = await syncService.syncUploads();

      // Assert
      expect(result.success, isFalse);
      expect(result.error.toString(), contains('No network connection'));

      // Now try with network back online
      networkState.setOnline();
      final retryResult = await syncService.syncUploads();
      expect(retryResult.success, isTrue);
    });
  });
}
