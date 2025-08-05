import 'package:flipsync/core/integration/platform_conflict_resolver.dart';
import 'package:flipsync/core/models/sync_data.dart';
import 'package:flipsync/core/services/conflict/conflict_resolution_service.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';

// // // import 'platform_conflict_resolver_test.mocks.dart';
// Removed generated import // Removed generated import // Removed generated import

class MockConflictResolutionService extends Mock
    implements ConflictResolutionService {}

void main() {
  late PlatformConflictResolver resolver;
  late MockConflictResolutionService mockService;

  setUp(() {
    mockService = MockConflictResolutionService();
    resolver = PlatformConflictResolver(mockService);
  });

  test('resolves simple conflicts correctly', () async {
    final localData = SyncData(
      timestamp: DateTime.now(),
      data: {'key': 'local_value'},
      type: 'test',
    );
    final remoteData = SyncData(
      timestamp: DateTime.now().subtract(const Duration(minutes: 5)),
      data: {'key': 'remote_value'},
      type: 'test',
    );

    when(
      () => mockService.resolveConflict(
        localData: localData,
        remoteData: remoteData,
        strategy: any(named: 'strategy'),
      ),
    ).thenAnswer((_) async => localData);

    final result = await resolver.resolve(
      localData: localData,
      remoteData: remoteData,
    );

    expect(result, equals(localData));
    verify(
      () => mockService.resolveConflict(
        localData: localData,
        remoteData: remoteData,
        strategy: any(named: 'strategy'),
      ),
    ).called(1);
  });

  test('handles complex data structure conflicts', () async {
    final localData = SyncData(
      timestamp: DateTime.now(),
      data: {
        'nested': {'key': 'local_value'},
        'array': [1, 2, 3],
      },
      type: 'test',
    );
    final remoteData = SyncData(
      timestamp: DateTime.now(),
      data: {
        'nested': {'key': 'remote_value'},
        'array': [4, 5, 6],
      },
      type: 'test',
    );

    when(
      () => mockService.resolveConflict(
        localData: localData,
        remoteData: remoteData,
        strategy: any(named: 'strategy'),
      ),
    ).thenAnswer((_) async => localData);

    final result = await resolver.resolve(
      localData: localData,
      remoteData: remoteData,
    );

    expect(result, equals(localData));
    verify(
      () => mockService.resolveConflict(
        localData: localData,
        remoteData: remoteData,
        strategy: any(named: 'strategy'),
      ),
    ).called(1);
  });

  test('handles resolution errors gracefully', () async {
    final localData = SyncData(
      timestamp: DateTime.now(),
      data: {'key': 'local_value'},
      type: 'test',
    );
    final remoteData = SyncData(
      timestamp: DateTime.now(),
      data: {'key': 'remote_value'},
      type: 'test',
    );

    when(
      () => mockService.resolveConflict(
        localData: localData,
        remoteData: remoteData,
        strategy: any(named: 'strategy'),
      ),
    ).thenThrow(Exception('Resolution failed'));

    expect(
      () => resolver.resolve(localData: localData, remoteData: remoteData),
      throwsA(isA<Exception>()),
    );
  });
}
