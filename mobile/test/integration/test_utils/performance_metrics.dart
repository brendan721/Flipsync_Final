class LaunchMetrics {
  final Duration coldStartDuration;
  final Duration warmStartDuration;

  const LaunchMetrics({
    required this.coldStartDuration,
    required this.warmStartDuration,
  });
}

class ScrollMetrics {
  final double averageFrameTime;
  final int jankCount;

  const ScrollMetrics({
    required this.averageFrameTime,
    required this.jankCount,
  });
}

class AnimationMetrics {
  final int frameDropCount;

  const AnimationMetrics({
    required this.frameDropCount,
  });
}

class ApiMetrics {
  final double averageResponseTime;

  const ApiMetrics({
    required this.averageResponseTime,
  });
}

class BandwidthMetrics {
  final int totalTransferred;

  const BandwidthMetrics({
    required this.totalTransferred,
  });
}

class ConcurrencyMetrics {
  final double successRate;

  const ConcurrencyMetrics({
    required this.successRate,
  });
}

class DatabaseMetrics {
  final double averageWriteTime;
  final double averageReadTime;

  const DatabaseMetrics({
    this.averageWriteTime = 0.0,
    this.averageReadTime = 0.0,
  });
}

class BulkOperationMetrics {
  final double completionTime;

  const BulkOperationMetrics({
    required this.completionTime,
  });
}

class BatteryMetrics {
  final double batteryDrain;

  const BatteryMetrics({
    required this.batteryDrain,
  });
}

class CleanupMetrics {
  final double cleanupTime;

  const CleanupMetrics({
    required this.cleanupTime,
  });
}

class ConnectionMetrics {
  final int leakCount;

  const ConnectionMetrics({
    required this.leakCount,
  });
}

class InitializationMetrics {
  final double totalTime;

  const InitializationMetrics({
    required this.totalTime,
  });
}

class DependencyMetrics {
  final double loadTime;

  const DependencyMetrics({
    required this.loadTime,
  });
}

class SecurityMetrics {
  final bool isPassed;
  final String details;

  const SecurityMetrics({
    required this.isPassed,
    this.details = '',
  });
}

class UiResponseMetrics {
  final Duration tapResponseTime;
  final Duration scrollResponseTime;
  final Duration transitionDuration;
  final int frameDropsCount;
  final double fps;

  const UiResponseMetrics({
    required this.tapResponseTime,
    required this.scrollResponseTime,
    required this.transitionDuration,
    required this.frameDropsCount,
    required this.fps,
  });
}

class RenderMetrics {
  final Duration firstContentfulPaint;
  final Duration timeToInteractive;
  final Duration layoutTime;
  final int rebuildCount;
  final int widgetCount;

  const RenderMetrics({
    required this.firstContentfulPaint,
    required this.timeToInteractive,
    required this.layoutTime,
    required this.rebuildCount,
    required this.widgetCount,
  });
}

class AccessibilityMetrics {
  final bool isScreenReaderCompatible;
  final bool hasAdequateContrast;
  final bool hasTouchTargets;
  final Map<String, bool> semanticsLabels;

  const AccessibilityMetrics({
    required this.isScreenReaderCompatible,
    required this.hasAdequateContrast,
    required this.hasTouchTargets,
    required this.semanticsLabels,
  });
}

class CrossDeviceMetrics {
  final Map<String, bool> layoutValidation;
  final Map<String, double> renderTimes;
  final Map<String, int> memoryUsage;
  final Map<String, bool> featureAvailability;

  const CrossDeviceMetrics({
    required this.layoutValidation,
    required this.renderTimes,
    required this.memoryUsage,
    required this.featureAvailability,
  });
}

class StateManagementMetrics {
  final Duration stateUpdateTime;
  final int stateChangesCount;
  final Map<String, Duration> actionLatency;
  final int inconsistencyCount;

  const StateManagementMetrics({
    required this.stateUpdateTime,
    required this.stateChangesCount,
    required this.actionLatency,
    required this.inconsistencyCount,
  });
}

class ErrorHandlingMetrics {
  final Map<String, int> errorCounts;
  final Duration averageRecoveryTime;
  final double errorRecoveryRate;
  final Map<String, String> userFeedback;

  const ErrorHandlingMetrics({
    required this.errorCounts,
    required this.averageRecoveryTime,
    required this.errorRecoveryRate,
    required this.userFeedback,
  });
}

class NetworkReliabilityMetrics {
  final double connectionStability;
  final Duration reconnectionTime;
  final int dropoutCount;
  final Map<String, Duration> endpointLatency;

  const NetworkReliabilityMetrics({
    required this.connectionStability,
    required this.reconnectionTime,
    required this.dropoutCount,
    required this.endpointLatency,
  });
}

class ResourceUsageMetrics {
  final double cpuUsage;
  final double memoryUsage;
  final double diskUsage;
  final double networkUsage;
  final Duration gcPauseTime;

  const ResourceUsageMetrics({
    required this.cpuUsage,
    required this.memoryUsage,
    required this.diskUsage,
    required this.networkUsage,
    required this.gcPauseTime,
  });
}
