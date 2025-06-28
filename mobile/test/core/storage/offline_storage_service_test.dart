import 'dart:io';
import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/core/storage/offline_storage_service.dart';
import 'package:path_provider_platform_interface/path_provider_platform_interface.dart';
import 'package:plugin_platform_interface/plugin_platform_interface.dart';

class FakePathProviderPlatform extends Fake
    with MockPlatformInterfaceMixin
    implements PathProviderPlatform {
  @override
  Future<String> getApplicationDocumentsPath() async {
    return '.';
  }
}

void main() {
  late OfflineStorageService storageService;
  late Directory tempDir;

  // Register the platform instance
  setUpAll(() {
    PathProviderPlatform.instance = FakePathProviderPlatform();
  });

  setUp(() async {
    TestWidgetsFlutterBinding.ensureInitialized();
    tempDir = await Directory.systemTemp.createTemp();

    // Initialize the storage service
    storageService = OfflineStorageService();
    await storageService.initialize();
  });

  tearDown(() async {
    // Clean up after tests
    await tempDir.delete(recursive: true);
  });

  group('Offline Storage Service', () {
    test('can be instantiated', () {
      // This is a basic test to ensure the service can be instantiated
      expect(storageService, isNotNull);
      expect(storageService, isA<OfflineStorageService>());
    });
  });
}
