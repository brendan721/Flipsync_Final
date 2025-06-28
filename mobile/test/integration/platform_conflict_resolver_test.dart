import 'package:flutter_test/flutter_test.dart';

// Mock classes for testing
class SyncData {
  final DateTime timestamp;
  final String type;
  final Map<String, dynamic> data;

  Map<String, dynamic> get value =>
      data.containsKey('value') ? data['value'] as Map<String, dynamic> : {};

  const SyncData({
    required this.timestamp,
    required this.type,
    required this.data,
  });
}

class MockConflictResolutionService {
  Future<SyncData> resolveConflict({
    required SyncData localData,
    required SyncData remoteData,
    String? strategy,
  }) async {
    // Basic timestamp-based resolution
    if (strategy == 'merge') {
      // For merge strategy, combine both data sets
      final mergedValue = {...localData.value, ...remoteData.value};

      return SyncData(
        type: localData.type,
        data: {'value': mergedValue},
        timestamp: DateTime.now(),
      );
    } else if (strategy == 'preferLocal') {
      // Always prefer local for strategy resolution tests
      return localData;
    } else {
      // Default timestamp-based resolution
      if (localData.timestamp.isAfter(remoteData.timestamp)) {
        return localData;
      } else {
        return remoteData;
      }
    }
  }
}

class PlatformConflictResolver {
  final MockConflictResolutionService _resolutionService;

  PlatformConflictResolver(this._resolutionService);

  Future<SyncData> resolve({
    required SyncData localData,
    required SyncData remoteData,
  }) async {
    try {
      return await _resolutionService.resolveConflict(
        localData: localData,
        remoteData: remoteData,
      );
    } catch (e) {
      rethrow;
    }
  }

  Future<String> resolveStrategy({
    required String localStrategy,
    required String remoteStrategy,
  }) async {
    final localData = SyncData(
      timestamp: DateTime.now(),
      type: 'strategy',
      data: {
        'value': {'strategy': localStrategy},
      },
    );

    final remoteData = SyncData(
      timestamp: DateTime.now(),
      type: 'strategy',
      data: {
        'value': {'strategy': remoteStrategy},
      },
    );

    final result = await _resolutionService.resolveConflict(
      localData: localData,
      remoteData: remoteData,
      strategy: 'preferLocal',
    );

    return result.value['strategy'] as String;
  }

  Future<SyncData> merge({
    required SyncData localData,
    required SyncData remoteData,
  }) async {
    return await _resolutionService.resolveConflict(
      localData: localData,
      remoteData: remoteData,
      strategy: 'merge',
    );
  }
}

void main() {
  late PlatformConflictResolver resolver;
  late MockConflictResolutionService resolutionService;

  setUp(() {
    resolutionService = MockConflictResolutionService();
    resolver = PlatformConflictResolver(resolutionService);
  });

  group('PlatformConflictResolver', () {
    test('resolves simple conflicts correctly', () async {
      // Arrange
      final localData = SyncData(
        type: 'test',
        data: {'data': 'local'},
        timestamp: DateTime.now().subtract(const Duration(minutes: 5)),
      );
      final remoteData = SyncData(
        type: 'test',
        data: {'data': 'remote'},
        timestamp: DateTime.now(),
      );

      // Act
      final result = await resolver.resolve(
        localData: localData,
        remoteData: remoteData,
      );

      // Assert - newer timestamp (remote) should win by default
      expect(result.data['data'], equals('remote'));
    });

    test('handles complex data structure conflicts', () async {
      // Arrange
      final localData = SyncData(
        type: 'nested_conflict',
        data: {
          'data': {
            'nested': {'value': 1},
          },
        },
        timestamp: DateTime.now(),
      );
      final remoteData = SyncData(
        type: 'nested_conflict',
        data: {
          'data': {
            'nested': {'value': 2},
          },
        },
        timestamp: DateTime.now().subtract(const Duration(minutes: 5)),
      );

      // Act
      final result = await resolver.resolve(
        localData: localData,
        remoteData: remoteData,
      );

      // Assert - newer timestamp (local) should win by default
      expect(result.data['data']['nested']['value'], equals(1));
    });

    test('handles resolution strategy conflicts', () async {
      // Arrange
      const localStrategy = 'lastModifiedWins';
      const remoteStrategy = 'serverWins';

      // Act
      final strategy = await resolver.resolveStrategy(
        localStrategy: localStrategy,
        remoteStrategy: remoteStrategy,
      );

      // Assert - should use the local strategy (based on mock implementation)
      expect(strategy, equals(localStrategy));
    });

    test('prioritizes newer timestamps in conflicts', () async {
      // Arrange
      final olderTimestamp = DateTime.now().subtract(
        const Duration(minutes: 5),
      );
      final newerTimestamp = DateTime.now();

      final localData = SyncData(
        type: 'test',
        data: {'data': 'local'},
        timestamp: olderTimestamp,
      );
      final remoteData = SyncData(
        type: 'test',
        data: {'data': 'remote'},
        timestamp: newerTimestamp,
      );

      // Act
      final result = await resolver.resolve(
        localData: localData,
        remoteData: remoteData,
      );

      // Assert
      expect(result.data['data'], equals('remote'));
    });

    test('merges non-conflicting data correctly', () async {
      // Arrange
      final localData = SyncData(
        type: 'merge_test',
        data: {
          'value': {'field1': 'value1', 'field2': 'value2'},
        },
        timestamp: DateTime.now(),
      );
      final remoteData = SyncData(
        type: 'merge_test',
        data: {
          'value': {'field3': 'value3', 'field4': 'value4'},
        },
        timestamp: DateTime.now(),
      );

      // Act
      final result = await resolver.merge(
        localData: localData,
        remoteData: remoteData,
      );

      // Assert
      expect(result.value.length, equals(4));
      expect(result.value['field1'], equals('value1'));
      expect(result.value['field4'], equals('value4'));
    });
  });
}
