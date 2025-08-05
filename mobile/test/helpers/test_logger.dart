import 'dart:io';
import 'dart:convert';
import 'package:logger/logger.dart';

class TestLogger {
  static final _logFile = File('logs/test_execution.log');
  static final Logger _logger = Logger(
    printer: PrettyPrinter(
      methodCount: 0,
      errorMethodCount: 5,
      lineLength: 120,
      colors: false,
      printEmojis: false,
      printTime: true,
    ),
    output: MultiOutput([ConsoleOutput(), FileOutput(file: _logFile)]),
  );

  static void info(String message) {
    _logger.i(message);
  }

  static void error(String message, [dynamic error, StackTrace? stackTrace]) {
    _logger.e(message, error: error, stackTrace: stackTrace);
  }

  static void debug(String message) {
    _logger.d(message);
  }
}

class FileOutput extends LogOutput {
  final File file;
  final bool overrideExisting;
  final Encoding encoding;

  FileOutput({
    required this.file,
    this.overrideExisting = false,
    this.encoding = utf8,
  }) {
    if (!file.existsSync()) {
      file.createSync(recursive: true);
    } else if (overrideExisting) {
      file.writeAsStringSync('', encoding: encoding);
    }
  }

  @override
  void output(OutputEvent event) {
    final output = event.lines.join('\n');
    file.writeAsStringSync(
      '$output\n',
      encoding: encoding,
      mode: FileMode.append,
    );
  }
}
