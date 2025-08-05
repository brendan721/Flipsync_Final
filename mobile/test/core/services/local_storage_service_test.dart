import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/core/services/local_storage_service.dart';
import 'package:hive/hive.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  late LocalStorageService storageService;
  late Directory tempDir;

  setUpAll(() async {
    tempDir = await Directory.systemTemp.createTemp('hive_test_');
    Hive.init(tempDir.path);
  });

  setUp(() async {
    storageService = LocalStorageService();
    await storageService.initialize(testDirectory: tempDir.path);
    await storageService.clear(); // Clear storage before each test
  });

  tearDown(() async {
    await storageService.dispose();
  });

  tearDownAll(() async {
    await tempDir.delete(recursive: true);
  });

  group('LocalStorageService', () {
    test('initializes correctly', () async {
      expect(await storageService.getSize(), equals(0));
    });

    test('writes and reads string value', () async {
      const key = 'test_key';
      const value = 'test_value';

      await storageService.write(key, value);
      final result = await storageService.read(key);

      expect(result, equals(value));
    });

    test('deletes value', () async {
      const key = 'test_key';
      const value = 'test_value';

      await storageService.write(key, value);
      await storageService.delete(key);
      final result = await storageService.read(key);

      expect(result, isNull);
    });

    test('clears all values', () async {
      await storageService.write('key1', 'value1');
      await storageService.write('key2', 'value2');
      await storageService.clear();

      expect(await storageService.getSize(), equals(0));
    });

    test('checks if key exists', () async {
      const key = 'test_key';
      const value = 'test_value';

      await storageService.write(key, value);
      final exists = await storageService.containsKey(key);

      expect(exists, isTrue);
    });

    test('gets all keys', () async {
      await storageService.write('key1', 'value1');
      await storageService.write('key2', 'value2');

      final keys = await storageService.getAllKeys();

      expect(keys, containsAll(['key1', 'key2']));
      expect(keys.length, equals(2));
    });

    test('handles large data', () async {
      final largeValue = 'x' * 1000000; // 1MB string
      await storageService.write('large_key', largeValue);
      final result = await storageService.read('large_key');

      expect(result, equals(largeValue));
    });

    test('handles concurrent operations', () async {
      final futures = List.generate(
          100, (index) => storageService.write('key_$index', 'value_$index'));

      await Future.wait(futures);
      expect(await storageService.getSize(), equals(100));
    });

    test('maintains data after reinitialization', () async {
      await storageService.write('persist_key', 'persist_value');
      await storageService.dispose();

      final newStorageService = LocalStorageService();
      await newStorageService.initialize(testDirectory: tempDir.path);

      final result = await newStorageService.read('persist_key');
      expect(result, equals('persist_value'));

      await newStorageService.dispose();
    });
  });
}
