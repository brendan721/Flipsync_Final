import 'package:sqflite/sqflite.dart';
import 'package:mocktail/mocktail.dart';
import 'package:logger/logger.dart';

// This class provides a real in-memory database implementation for tests
// instead of using mocks, which aligns with our goal of replacing mock implementations
class DatabaseTestHelper {
  final Database database;
  final Logger logger;

  DatabaseTestHelper({
    required this.database,
    required this.logger,
  });

  // Factory method to create a test helper with real in-memory database
  static Future<DatabaseTestHelper> create() async {
    final logger = Logger();
    
    // Open an in-memory database for testing
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
          CREATE TABLE files (
            id TEXT PRIMARY KEY,
            path TEXT NOT NULL,
            size INTEGER NOT NULL,
            last_modified INTEGER NOT NULL,
            status TEXT NOT NULL
          )
        ''');
        
        await db.execute('''
          CREATE TABLE sync_status (
            file_id TEXT PRIMARY KEY,
            status TEXT NOT NULL,
            progress REAL NOT NULL,
            error TEXT,
            last_updated INTEGER NOT NULL
          )
        ''');
      },
    );
    
    return DatabaseTestHelper(
      database: database,
      logger: logger,
    );
  }
  
  // Helper method to insert test data
  Future<void> insertTestData({
    required String table,
    required List<Map<String, dynamic>> data,
  }) async {
    final batch = database.batch();
    
    for (final item in data) {
      batch.insert(table, item);
    }
    
    await batch.commit();
  }
  
  // Helper method to query test data
  Future<List<Map<String, dynamic>>> queryTestData({
    required String table,
    String? where,
    List<Object?>? whereArgs,
    int? limit,
  }) async {
    return await database.query(
      table,
      where: where,
      whereArgs: whereArgs,
      limit: limit,
    );
  }
  
  // Clean up resources
  Future<void> close() async {
    await database.close();
  }
}
