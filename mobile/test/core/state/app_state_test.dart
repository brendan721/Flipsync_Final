import 'package:bloc_test/bloc_test.dart';
import 'package:flipsync/core/state/app_state.dart';
import 'package:flutter_test/flutter_test.dart';

// Using real classes instead of mocks for testing
void main() {
  group('AppState', () {
    test('supports value equality', () {
      expect(AppState(), equals(AppState()));
    });

    test('copyWith returns same object if no properties are passed', () {
      expect(AppState().copyWith(), equals(AppState()));
    });

    test('copyWith returns new object with updated properties', () {
      final state = AppState();
      final newState = state.copyWith(
        status: AppStatus.authenticated,
        userId: 'test-user',
        isConnected: true,
      );

      expect(newState.status, equals(AppStatus.authenticated));
      expect(newState.userId, equals('test-user'));
      expect(newState.isConnected, isTrue);
    });
  });

  group('AppBloc', () {
    late AppBloc appBloc;

    setUp(() {
      appBloc = AppBloc();
    });

    tearDown(() {
      appBloc.close();
    });

    test('initial state is correct', () {
      expect(appBloc.state, equals(AppState()));
    });

    blocTest<AppBloc, AppState>(
      'emits [AppStatus.unauthenticated] when AppStarted is added',
      build: () => AppBloc(),
      act: (bloc) => bloc.add(AppStarted()),
      expect:
          () => [
            isA<AppState>()
                .having((s) => s.status, 'status', AppStatus.unauthenticated)
                .having(
                  (s) => s.metrics.stateChangesCount,
                  'stateChangesCount',
                  1,
                ),
          ],
    );

    blocTest<AppBloc, AppState>(
      'emits authenticated state when UserAuthenticated is added',
      build: () => AppBloc(),
      act: (bloc) => bloc.add(const UserAuthenticated('test-user')),
      expect:
          () => [
            isA<AppState>()
                .having((s) => s.status, 'status', AppStatus.authenticated)
                .having((s) => s.userId, 'userId', 'test-user')
                .having(
                  (s) => s.metrics.stateChangesCount,
                  'stateChangesCount',
                  1,
                ),
          ],
    );

    blocTest<AppBloc, AppState>(
      'emits unauthenticated state when UserLoggedOut is added',
      build: () => AppBloc(),
      seed:
          () => AppState(
            status: AppStatus.authenticated,
            userId: 'test-user',
            isConnected: true,
          ),
      act: (bloc) => bloc.add(UserLoggedOut()),
      expect:
          () => [
            isA<AppState>()
                .having((s) => s.status, 'status', AppStatus.unauthenticated)
                .having((s) => s.userId, 'userId', null)
                .having((s) => s.isConnected, 'isConnected', false)
                .having((s) => s.notifications, 'notifications', isEmpty)
                .having(
                  (s) => s.metrics.stateChangesCount,
                  'stateChangesCount',
                  1,
                ),
          ],
    );

    blocTest<AppBloc, AppState>(
      'updates connection state when ConnectionStateChanged is added',
      build: () => AppBloc(),
      act: (bloc) => bloc.add(const ConnectionStateChanged(true)),
      expect:
          () => [
            isA<AppState>()
                .having((s) => s.isConnected, 'isConnected', true)
                .having(
                  (s) => s.metrics.stateChangesCount,
                  'stateChangesCount',
                  1,
                ),
          ],
    );

    blocTest<AppBloc, AppState>(
      'adds notification when NotificationReceived is added',
      build: () => AppBloc(),
      act: (bloc) => bloc.add(const NotificationReceived({'message': 'test'})),
      expect:
          () => [
            isA<AppState>()
                .having(
                  (s) => s.notifications,
                  'notifications',
                  equals([
                    {'message': 'test'},
                  ]),
                )
                .having(
                  (s) => s.metrics.stateChangesCount,
                  'stateChangesCount',
                  1,
                ),
          ],
    );

    blocTest<AppBloc, AppState>(
      'updates pipeline state when PipelineStateChanged is added',
      build: () => AppBloc(),
      act:
          (bloc) => bloc.add(
            const PipelineStateChanged(
              pipelineId: 'test-pipeline',
              status: PipelineStatus.running,
              stageStates: {
                'stage1': {
                  'status': 'running',
                  'metrics': {'progress': 50},
                  'processed_items': ['item1'],
                  'failed_items': {},
                  'stage_data': {'key': 'value'},
                },
              },
            ),
          ),
      expect:
          () => [
            isA<AppState>()
                .having(
                  (s) => s.pipelineStatuses,
                  'pipelineStatuses',
                  equals({'test-pipeline': PipelineStatus.running}),
                )
                .having(
                  (s) => s.pipelineStages['test-pipeline']?['stage1']?.status,
                  'stage status',
                  equals('running'),
                )
                .having(
                  (s) => s.pipelineStages['test-pipeline']?['stage1']?.metrics,
                  'stage metrics',
                  equals({'progress': 50}),
                )
                .having(
                  (s) => s.metrics.stateChangesCount,
                  'stateChangesCount',
                  1,
                ),
          ],
    );
  });
}
