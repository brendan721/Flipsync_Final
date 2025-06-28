import 'package:dio/dio.dart';
import 'package:logger/logger.dart';
import 'package:mocktail/mocktail.dart';
import 'package:sqflite/sqflite.dart';

// Mock classes
class MockDio extends Mock implements Dio {}

// We'll use a real database for new tests, but keep the mock for backward compatibility
class MockDatabase extends Mock implements Database {}

class MockLogger extends Mock implements Logger {}

class MockBatch extends Mock implements Batch {}

class MockResponse extends Mock implements Response {}

class MockRequestOptions extends Mock implements RequestOptions {}

class RepositoryTestHelper {
  final MockDio dio;
  final Database database;
  final MockLogger logger;
  final MockBatch batch;

  RepositoryTestHelper._internal({
    required this.dio,
    required this.database,
    required this.logger,
    required this.batch,
  }) {
    _setupMockRegistrations();
    _setupCommonBehavior();
  }

  // Factory constructor to create a RepositoryTestHelper with a real database
  static Future<RepositoryTestHelper> create() async {
    final dio = MockDio();
    final logger = MockLogger();
    final batch = MockBatch();

    // Create a real in-memory database using our test helper
    final database = await openDatabase(
      inMemoryDatabasePath,
      version: 1,
      onCreate: (db, version) async {
        // Create test tables
        await db.execute('''
          CREATE TABLE alerts (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL
          )
        ''');

        await db.execute('''
          CREATE TABLE inventory (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL
          )
        ''');

        await db.execute('''
          CREATE TABLE metrics (
            id TEXT PRIMARY KEY,
            data TEXT NOT NULL
          )
        ''');
      },
    );

    return RepositoryTestHelper._internal(
      dio: dio,
      database: database,
      logger: logger,
      batch: batch,
    );
  }

  // Legacy constructor for backward compatibility
  factory RepositoryTestHelper() {
    final dio = MockDio();
    final logger = MockLogger();
    final batch = MockBatch();

    // Create a mock database for backward compatibility
    final database = MockDatabase();

    // Setup common database behavior
    when(() => database.batch()).thenReturn(batch);
    when(() => batch.commit(noResult: true)).thenAnswer((_) async => []);

    // Setup default database query behavior
    when(() => database.query(
          any(),
          columns: any(named: 'columns'),
          where: any(named: 'where'),
          whereArgs: any(named: 'whereArgs'),
          orderBy: any(named: 'orderBy'),
          limit: any(named: 'limit'),
        )).thenAnswer((_) async => []);

    final helper = RepositoryTestHelper._internal(
      dio: dio,
      database: database as Database,
      logger: logger,
      batch: batch,
    );

    return helper;
  }

  void _setupMockRegistrations() {
    // Register fallback values for common types
    registerFallbackValue(RequestOptions(path: ''));
    registerFallbackValue(Response(requestOptions: RequestOptions(path: '')));
    registerFallbackValue(<String, dynamic>{});
    registerFallbackValue(<String, String>{});
  }

  void _setupCommonBehavior() {
    // Setup common database behavior
    when(() => database.batch()).thenReturn(batch);
    when(() => batch.commit(noResult: true)).thenAnswer((_) async => []);

    // Setup default database query behavior
    when(() => database.query(
          any(),
          columns: any(named: 'columns'),
          where: any(named: 'where'),
          whereArgs: any(named: 'whereArgs'),
          orderBy: any(named: 'orderBy'),
          limit: any(named: 'limit'),
        )).thenAnswer((_) async => []);

    // Setup common logger behavior
    when(() => logger.d(any())).thenReturn(null);
    when(() => logger.e(any())).thenReturn(null);
    when(() => logger.i(any())).thenReturn(null);
    when(() => logger.w(any())).thenReturn(null);
  }

  // Common API success response setup
  void setupApiSuccess({
    required String endpoint,
    required Map<String, dynamic> responseData,
    Map<String, dynamic>? queryParams,
    Map<String, dynamic>? data,
    String method = 'GET',
  }) {
    final response = Response(
      data: responseData,
      requestOptions: RequestOptions(path: endpoint),
    );

    if (method == 'GET') {
      if (queryParams != null) {
        when(() => dio.get(endpoint, queryParameters: any(named: 'queryParameters')))
            .thenAnswer((_) async => response);
      } else {
        when(() => dio.get(endpoint)).thenAnswer((_) async => response);
      }
    } else if (method == 'PUT') {
      if (data != null) {
        when(() => dio.put(endpoint, data: data)).thenAnswer((_) async => response);
      } else {
        when(() => dio.put(endpoint)).thenAnswer((_) async => response);
      }
    }
  }

  // Common API error setup
  void setupApiError({
    required String endpoint,
    String errorMessage = 'Network error',
    int? statusCode,
    Map<String, dynamic>? queryParams,
    Map<String, dynamic>? data,
    String method = 'GET',
  }) {
    final error = DioException(
      requestOptions: RequestOptions(path: endpoint),
      error: errorMessage,
      response: statusCode != null
          ? Response(
              statusCode: statusCode,
              requestOptions: RequestOptions(path: endpoint),
            )
          : null,
    );

    if (method == 'GET') {
      if (queryParams != null) {
        when(() => dio.get(endpoint, queryParameters: any(named: 'queryParameters')))
            .thenThrow(error);
      } else {
        when(() => dio.get(endpoint)).thenThrow(error);
      }
    } else if (method == 'PUT') {
      if (data != null) {
        when(() => dio.put(endpoint, data: data)).thenThrow(error);
      } else {
        when(() => dio.put(endpoint)).thenThrow(error);
      }
    }
  }

  // Setup cache data
  void setupCacheData({
    required String table,
    required List<Map<String, dynamic>> data,
    String? where,
    List<Object?>? whereArgs,
    int? limit,
  }) {
    if (where != null || whereArgs != null || limit != null) {
      when(() => database.query(
            table,
            where: where,
            whereArgs: whereArgs,
            limit: limit,
          )).thenAnswer((_) async => data);
    } else {
      when(() => database.query(table)).thenAnswer((_) async => data);
    }
  }

  // Verify API call
  void verifyApiCall(
    String endpoint, {
    int times = 1,
    Map<String, dynamic>? queryParams,
    Map<String, dynamic>? data,
    String method = 'GET',
  }) {
    if (method == 'GET') {
      if (queryParams != null) {
        verify(() => dio.get(endpoint, queryParameters: any(named: 'queryParameters')))
            .called(times);
      } else {
        verify(() => dio.get(endpoint)).called(times);
      }
    } else if (method == 'PUT') {
      if (data != null) {
        verify(() => dio.put(endpoint, data: data)).called(times);
      } else {
        verify(() => dio.put(endpoint)).called(times);
      }
    }
  }

  // Verify cache access
  void verifyCacheAccess(String table, {int times = 1}) {
    verify(() => database.query(table)).called(times);
  }

  // Verify error logging
  void verifyErrorLogged({int times = 1}) {
    verify(() => logger.e(any())).called(times);
  }

  // Setup batch operations
  void setupBatchOperation() {
    when(() => batch.insert(
          any(),
          any(),
          conflictAlgorithm: any(named: 'conflictAlgorithm'),
        )).thenReturn(batch);
  }

  // Verify batch commit
  void verifyBatchCommit({int times = 1}) {
    verify(() => batch.commit(noResult: true)).called(times);
  }
}
