// This file contains test helpers for sync service tests
// It is not a test file itself, but provides implementations for real tests

import 'package:flutter_test/flutter_test.dart';

// A minimal test helper for sync data
class SimpleSyncData {
  final String id;
  final DateTime timestamp;
  final Map<String, dynamic> data;
  final bool isDeleted;

  SimpleSyncData({
    required this.id,
    required this.data,
    DateTime? timestamp,
    this.isDeleted = false,
  }) : timestamp = timestamp ?? DateTime.now();

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'timestamp': timestamp.toIso8601String(),
      'data': data,
      'isDeleted': isDeleted,
    };
  }
}

// Simple result class for sync operations
class SyncTestResult {
  final bool success;
  final int syncedItems;
  final int failedItems;
  final int conflictResolved;
  final int changesApplied;
  final dynamic error;

  SyncTestResult({
    required this.success,
    this.syncedItems = 0,
    this.failedItems = 0,
    this.conflictResolved = 0,
    this.changesApplied = 0,
    this.error,
  });
}

// A simple storage helper for testing
class StorageTestHelper {
  final Map<String, String> _storage = {};
  final List<Map<String, dynamic>> _pendingUploads = [];

  // Basic storage operations
  Future<void> write(String key, String value) async {
    _storage[key] = value;
  }

  Future<String?> read(String key) async {
    return _storage[key];
  }

  Future<void> delete(String key) async {
    _storage.remove(key);
  }

  Future<void> clear() async {
    _storage.clear();
  }

  // Sync-related operations
  void addPendingUpload(Map<String, dynamic> data) {
    _pendingUploads.add(data);
  }
}

// Simple network helper for testing
class NetworkTestHelper {
  bool _isConnected = true;

  bool get isConnected => _isConnected;

  void setConnected(bool connected) {
    _isConnected = connected;
  }
}

// Use a main function to prevent Flutter test runner errors
// even though this file is intended as a helper
void main() {
  // This is just a collection of helpers, not actual tests
  group('SyncServiceHelpers', () {
    test('This file contains only helper classes, not tests', () {
      expect(true, isTrue); // Trivial assertion to make the test pass
    });
  });
}
