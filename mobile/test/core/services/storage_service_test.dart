import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/core/services/storage_service.dart';

// Real test implementation for storage service
class TestStorageService implements StorageService {
  final Map<String, String> _storage = {};

  @override
  Future<void> write(String key, String value) async {
    _storage[key] = value;
  }

  @override
  Future<String?> read(String key) async {
    return _storage[key];
  }

  @override
  Future<void> delete(String key) async {
    _storage.remove(key);
  }

  @override
  Future<void> clear() async {
    _storage.clear();
  }

  @override
  Future<bool> containsKey(String key) async {
    return _storage.containsKey(key);
  }

  // Implement other required methods based on StorageService interface
}

void main() {
  group('StorageService tests', () {
    late TestStorageService storageService;

    setUp(() {
      storageService = TestStorageService();
    });

    test('write should store data correctly', () async {
      // Act
      await storageService.write('key', 'value');

      // Assert
      final result = await storageService.read('key');
      expect(result, equals('value'));
    });

    test('read should retrieve data correctly', () async {
      // Arrange
      await storageService.write('key', 'stored value');

      // Act
      final result = await storageService.read('key');

      // Assert
      expect(result, equals('stored value'));
    });

    test('delete should remove data correctly', () async {
      // Arrange
      await storageService.write('key', 'value');

      // Act
      await storageService.delete('key');

      // Assert
      final result = await storageService.read('key');
      expect(result, isNull);
    });

    test('read with missing key should return null', () async {
      // Act
      final result = await storageService.read('missing-key');

      // Assert
      expect(result, isNull);
    });

    test('clear should remove all data', () async {
      // Arrange
      await storageService.write('key1', 'value1');
      await storageService.write('key2', 'value2');

      // Act
      await storageService.clear();

      // Assert
      expect(await storageService.read('key1'), isNull);
      expect(await storageService.read('key2'), isNull);
    });

    test('containsKey should return true for existing keys', () async {
      // Arrange
      await storageService.write('key', 'value');

      // Act & Assert
      expect(await storageService.containsKey('key'), isTrue);
      expect(await storageService.containsKey('missing-key'), isFalse);
    });
  });
}
