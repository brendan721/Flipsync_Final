import 'package:flutter_test/flutter_test.dart';
import 'package:flipsync/core/services/test_service.dart';

void main() {
  group('TestService tests', () {
    late TestService testService;

    setUp(() {
      testService = TestService();
    });

    test('getMessage should return the correct message', () {
      expect(testService.getMessage(), equals('Test service is working!'));
    });
  });
}
