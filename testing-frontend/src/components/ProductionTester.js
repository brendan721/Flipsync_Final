import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { 
  Zap, 
  AlertTriangle, 
  Shield, 
  Database,
  Server,
  Globe,
  Users,
  Clock,
  CheckCircle,
  XCircle,
  Play,
  Pause,
  Square,
  BarChart3,
  TrendingUp,
  Activity,
  RefreshCw
} from 'lucide-react';
// Using CSS-based visualizations instead of recharts for better compatibility
import api from '../services/api';

const ProductionTester = () => {
  const [activeTest, setActiveTest] = useState(null);
  const [testResults, setTestResults] = useState({});
  const [systemMetrics, setSystemMetrics] = useState({});
  const [loadTestConfig, setLoadTestConfig] = useState({
    concurrentUsers: 100,
    duration: 300, // seconds
    rampUpTime: 60, // seconds
    testType: 'gradual' // gradual, spike, sustained
  });
  const [isRunning, setIsRunning] = useState(false);
  const [testProgress, setTestProgress] = useState(0);

  // Production-like test scenarios
  const testScenarios = {
    black_friday: {
      name: 'Black Friday Load Test',
      description: 'Simulate Black Friday traffic with 10x normal load',
      icon: Zap,
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      config: {
        concurrentUsers: 1000,
        duration: 1800, // 30 minutes
        rampUpTime: 300, // 5 minutes
        peakMultiplier: 10,
        scenarios: [
          'Product search and browsing',
          'Listing creation and optimization',
          'Market analysis requests',
          'Inventory management operations',
          'Real-time chat interactions'
        ]
      }
    },
    bulk_processing: {
      name: 'Bulk Product Processing',
      description: 'Process 1000+ products simultaneously',
      icon: Database,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      config: {
        productCount: 1000,
        batchSize: 50,
        processingTypes: [
          'Market analysis',
          'Content generation',
          'Pricing optimization',
          'Inventory updates'
        ]
      }
    },
    failover_testing: {
      name: 'Failover & Recovery Testing',
      description: 'Test system resilience and error recovery',
      icon: Shield,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      config: {
        failureScenarios: [
          'Database connection loss',
          'External API timeouts',
          'Agent service failures',
          'Network partitions'
        ],
        recoveryTime: 30, // seconds
        redundancyLevel: 'high'
      }
    },
    integration_testing: {
      name: 'External Integration Testing',
      description: 'Test all external service integrations',
      icon: Globe,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      config: {
        services: [
          'eBay API',
          'Amazon MWS',
          'Shipping APIs',
          'Payment processors',
          'Analytics services'
        ],
        testDepth: 'comprehensive'
      }
    },
    performance_benchmark: {
      name: 'Performance Benchmarking',
      description: 'Comprehensive performance testing and optimization',
      icon: TrendingUp,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      config: {
        benchmarkTypes: [
          'Response time optimization',
          'Throughput maximization',
          'Resource utilization',
          'Scalability limits'
        ],
        targetMetrics: {
          responseTime: 200, // ms
          throughput: 1000, // requests/second
          errorRate: 0.01 // 1%
        }
      }
    }
  };

  useEffect(() => {
    if (isRunning && activeTest) {
      const interval = setInterval(() => {
        updateTestProgress();
        collectSystemMetrics();
      }, 1000);
      
      return () => clearInterval(interval);
    }
  }, [isRunning, activeTest]);

  const startTest = async (testKey) => {
    const test = testScenarios[testKey];
    if (!test) return;

    setActiveTest({ key: testKey, ...test });
    setIsRunning(true);
    setTestProgress(0);
    setTestResults({});

    toast.info(`Starting ${test.name}...`);

    try {
      await executeProductionTest(testKey, test);
    } catch (error) {
      console.error('Test execution failed:', error);
      toast.error(`Test failed: ${error.message}`);
      setIsRunning(false);
    }
  };

  const executeProductionTest = async (testKey, test) => {
    const startTime = Date.now();
    const testDuration = test.config.duration || 300;
    
    // Initialize test metrics
    const metrics = {
      startTime,
      testType: testKey,
      config: test.config,
      results: {
        totalRequests: 0,
        successfulRequests: 0,
        failedRequests: 0,
        averageResponseTime: 0,
        peakResponseTime: 0,
        throughput: 0,
        errorRate: 0
      },
      timeline: []
    };

    // Simulate different test types
    switch (testKey) {
      case 'black_friday':
        await executeLoadTest(metrics);
        break;
      case 'bulk_processing':
        await executeBulkProcessingTest(metrics);
        break;
      case 'failover_testing':
        await executeFailoverTest(metrics);
        break;
      case 'integration_testing':
        await executeIntegrationTest(metrics);
        break;
      case 'performance_benchmark':
        await executePerformanceBenchmark(metrics);
        break;
      default:
        await executeGenericTest(metrics);
    }

    // Finalize results
    metrics.endTime = Date.now();
    metrics.totalDuration = metrics.endTime - metrics.startTime;
    
    setTestResults(metrics);
    setIsRunning(false);
    setTestProgress(100);
    
    toast.success(`${test.name} completed successfully`);
  };

  const executeLoadTest = async (metrics) => {
    const { concurrentUsers, duration, rampUpTime } = loadTestConfig;
    const totalSteps = Math.floor(duration / 5); // Update every 5 seconds
    
    for (let step = 0; step < totalSteps; step++) {
      if (!isRunning) break;
      
      // Simulate ramping up users
      const currentUsers = Math.min(
        concurrentUsers,
        Math.floor((concurrentUsers * step * 5) / rampUpTime)
      );
      
      // Simulate requests and responses
      const requestsThisStep = currentUsers * (Math.random() * 3 + 1); // 1-4 requests per user per 5s
      const responseTime = Math.random() * 500 + 100; // 100-600ms
      const errorRate = Math.random() * 0.05; // 0-5% error rate
      
      metrics.results.totalRequests += requestsThisStep;
      metrics.results.successfulRequests += Math.floor(requestsThisStep * (1 - errorRate));
      metrics.results.failedRequests += Math.ceil(requestsThisStep * errorRate);
      metrics.results.averageResponseTime = (metrics.results.averageResponseTime + responseTime) / 2;
      metrics.results.peakResponseTime = Math.max(metrics.results.peakResponseTime, responseTime);
      
      // Add timeline data point
      metrics.timeline.push({
        time: new Date().toLocaleTimeString(),
        users: currentUsers,
        responseTime: responseTime,
        throughput: requestsThisStep / 5, // requests per second
        errorRate: errorRate * 100
      });
      
      setTestProgress((step / totalSteps) * 100);
      await new Promise(resolve => setTimeout(resolve, 5000));
    }
    
    metrics.results.throughput = metrics.results.totalRequests / (duration / 1000);
    metrics.results.errorRate = (metrics.results.failedRequests / metrics.results.totalRequests) * 100;
  };

  const executeBulkProcessingTest = async (metrics) => {
    const { productCount, batchSize } = testScenarios.bulk_processing.config;
    const batches = Math.ceil(productCount / batchSize);
    
    for (let batch = 0; batch < batches; batch++) {
      if (!isRunning) break;
      
      const batchStartTime = Date.now();
      
      // Simulate batch processing
      try {
        // Simulate API calls for batch processing
        const batchResults = await Promise.allSettled([
          simulateAgentCall('market', { products: batchSize }),
          simulateAgentCall('content', { products: batchSize }),
          simulateAgentCall('logistics', { products: batchSize })
        ]);
        
        const batchEndTime = Date.now();
        const batchDuration = batchEndTime - batchStartTime;
        
        metrics.results.totalRequests += batchSize;
        metrics.results.successfulRequests += batchResults.filter(r => r.status === 'fulfilled').length * (batchSize / 3);
        metrics.results.failedRequests += batchResults.filter(r => r.status === 'rejected').length * (batchSize / 3);
        
        metrics.timeline.push({
          time: new Date().toLocaleTimeString(),
          batch: batch + 1,
          processed: (batch + 1) * batchSize,
          batchTime: batchDuration,
          throughput: batchSize / (batchDuration / 1000)
        });
        
        setTestProgress(((batch + 1) / batches) * 100);
        
      } catch (error) {
        metrics.results.failedRequests += batchSize;
      }
      
      // Brief delay between batches
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  };

  const executeFailoverTest = async (metrics) => {
    const scenarios = testScenarios.failover_testing.config.failureScenarios;
    
    for (let i = 0; i < scenarios.length; i++) {
      if (!isRunning) break;
      
      const scenario = scenarios[i];
      const testStartTime = Date.now();
      
      // Simulate failure scenario
      toast.warning(`Simulating: ${scenario}`);
      
      // Simulate system response to failure
      await new Promise(resolve => setTimeout(resolve, 2000)); // Failure detection time
      
      // Simulate recovery
      const recoveryStartTime = Date.now();
      await new Promise(resolve => setTimeout(resolve, Math.random() * 10000 + 5000)); // 5-15s recovery
      const recoveryEndTime = Date.now();
      
      const recoveryTime = recoveryEndTime - recoveryStartTime;
      const totalTime = recoveryEndTime - testStartTime;
      
      metrics.timeline.push({
        time: new Date().toLocaleTimeString(),
        scenario,
        recoveryTime,
        totalTime,
        status: recoveryTime < 30000 ? 'success' : 'warning'
      });
      
      setTestProgress(((i + 1) / scenarios.length) * 100);
    }
  };

  const executeIntegrationTest = async (metrics) => {
    const services = testScenarios.integration_testing.config.services;
    
    for (let i = 0; i < services.length; i++) {
      if (!isRunning) break;
      
      const service = services[i];
      const testStartTime = Date.now();
      
      try {
        // Simulate service integration test
        await simulateServiceTest(service);
        
        const testEndTime = Date.now();
        const responseTime = testEndTime - testStartTime;
        
        metrics.results.successfulRequests++;
        metrics.timeline.push({
          time: new Date().toLocaleTimeString(),
          service,
          responseTime,
          status: 'success'
        });
        
      } catch (error) {
        metrics.results.failedRequests++;
        metrics.timeline.push({
          time: new Date().toLocaleTimeString(),
          service,
          error: error.message,
          status: 'failed'
        });
      }
      
      setTestProgress(((i + 1) / services.length) * 100);
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
  };

  const executePerformanceBenchmark = async (metrics) => {
    const benchmarks = testScenarios.performance_benchmark.config.benchmarkTypes;
    const targets = testScenarios.performance_benchmark.config.targetMetrics;
    
    for (let i = 0; i < benchmarks.length; i++) {
      if (!isRunning) break;
      
      const benchmark = benchmarks[i];
      
      // Run performance test
      const results = await runPerformanceBenchmark(benchmark, targets);
      
      metrics.timeline.push({
        time: new Date().toLocaleTimeString(),
        benchmark,
        ...results
      });
      
      setTestProgress(((i + 1) / benchmarks.length) * 100);
    }
  };

  const executeGenericTest = async (metrics) => {
    // Generic test implementation
    for (let i = 0; i < 10; i++) {
      if (!isRunning) break;
      
      await new Promise(resolve => setTimeout(resolve, 1000));
      setTestProgress((i + 1) * 10);
    }
  };

  // Helper functions for simulations
  const simulateAgentCall = async (agentType, payload) => {
    const delay = Math.random() * 2000 + 500; // 500-2500ms
    await new Promise(resolve => setTimeout(resolve, delay));
    
    if (Math.random() < 0.95) { // 95% success rate
      return { success: true, agentType, payload, responseTime: delay };
    } else {
      throw new Error(`${agentType} agent timeout`);
    }
  };

  const simulateServiceTest = async (service) => {
    const delay = Math.random() * 3000 + 1000; // 1-4s
    await new Promise(resolve => setTimeout(resolve, delay));
    
    if (Math.random() < 0.9) { // 90% success rate for external services
      return { success: true, service, responseTime: delay };
    } else {
      throw new Error(`${service} integration failed`);
    }
  };

  const runPerformanceBenchmark = async (benchmark, targets) => {
    const iterations = 100;
    const results = [];
    
    for (let i = 0; i < iterations; i++) {
      const startTime = Date.now();
      await simulateAgentCall('test', { benchmark });
      const endTime = Date.now();
      results.push(endTime - startTime);
    }
    
    const avgResponseTime = results.reduce((a, b) => a + b, 0) / results.length;
    const maxResponseTime = Math.max(...results);
    const minResponseTime = Math.min(...results);
    
    return {
      avgResponseTime,
      maxResponseTime,
      minResponseTime,
      targetMet: avgResponseTime <= targets.responseTime,
      iterations
    };
  };

  const updateTestProgress = () => {
    // This is handled by individual test functions
  };

  const collectSystemMetrics = () => {
    // Simulate real-time system metrics collection
    setSystemMetrics(prev => ({
      ...prev,
      timestamp: Date.now(),
      cpu: Math.random() * 80 + 10,
      memory: Math.random() * 70 + 20,
      network: Math.random() * 50 + 10,
      activeConnections: Math.floor(Math.random() * 1000 + 100),
      requestsPerSecond: Math.floor(Math.random() * 500 + 50)
    }));
  };

  const stopTest = () => {
    setIsRunning(false);
    setActiveTest(null);
    setTestProgress(0);
    toast.info('Test stopped');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Production Testing Environment</h2>
            <p className="text-gray-600">Simulate real-world production scenarios and stress testing</p>
          </div>
          
          {activeTest && (
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                Progress: {Math.round(testProgress)}%
              </div>
              <button
                onClick={stopTest}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center space-x-2"
              >
                <Square className="w-4 h-4" />
                <span>Stop Test</span>
              </button>
            </div>
          )}
        </div>

        {/* Progress Bar */}
        {activeTest && (
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>{activeTest.name}</span>
              <span>{Math.round(testProgress)}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${testProgress}%` }}
              ></div>
            </div>
          </div>
        )}
      </div>

      {/* Test Scenarios */}
      {!activeTest && (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
          {Object.entries(testScenarios).map(([key, scenario]) => (
            <TestScenarioCard
              key={key}
              scenarioKey={key}
              scenario={scenario}
              onStart={startTest}
              disabled={isRunning}
            />
          ))}
        </div>
      )}

      {/* Active Test Monitoring */}
      {activeTest && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Real-time Metrics */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Real-time System Metrics</h3>
            <div className="grid grid-cols-2 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{systemMetrics.cpu?.toFixed(1) || 0}%</div>
                <div className="text-sm text-gray-600">CPU Usage</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{systemMetrics.memory?.toFixed(1) || 0}%</div>
                <div className="text-sm text-gray-600">Memory Usage</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">{systemMetrics.activeConnections || 0}</div>
                <div className="text-sm text-gray-600">Active Connections</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{systemMetrics.requestsPerSecond || 0}</div>
                <div className="text-sm text-gray-600">Requests/sec</div>
              </div>
            </div>
          </div>

          {/* Test Configuration */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Configuration</h3>
            <div className="space-y-3">
              {Object.entries(activeTest.config).map(([key, value]) => (
                <div key={key} className="flex justify-between">
                  <span className="text-gray-600 capitalize">{key.replace(/([A-Z])/g, ' $1').toLowerCase()}:</span>
                  <span className="font-medium text-gray-900">
                    {Array.isArray(value) ? `${value.length} items` : String(value)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Test Results */}
      {testResults.timeline && testResults.timeline.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Results Timeline</h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {testResults.timeline.map((entry, index) => (
              <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                <span className="text-sm text-gray-600">{entry.time}</span>
                <span className="text-sm font-medium text-gray-900">
                  {entry.scenario || entry.service || entry.benchmark || `Step ${index + 1}`}
                </span>
                <span className={`text-sm ${
                  entry.status === 'success' ? 'text-green-600' :
                  entry.status === 'failed' ? 'text-red-600' :
                  'text-yellow-600'
                }`}>
                  {entry.responseTime ? `${Math.round(entry.responseTime)}ms` : entry.status || 'OK'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// Test Scenario Card Component
const TestScenarioCard = ({ scenarioKey, scenario, onStart, disabled }) => {
  const Icon = scenario.icon;

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center space-x-3 mb-4">
        <div className={`p-2 rounded-lg ${scenario.bgColor}`}>
          <Icon className={`w-6 h-6 ${scenario.color}`} />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">{scenario.name}</h3>
        </div>
      </div>
      
      <p className="text-gray-700 mb-4">{scenario.description}</p>
      
      <div className="space-y-2 mb-4">
        {scenario.config.scenarios && (
          <div className="text-sm text-gray-600">
            <strong>Scenarios:</strong> {scenario.config.scenarios.length} types
          </div>
        )}
        {scenario.config.concurrentUsers && (
          <div className="text-sm text-gray-600">
            <strong>Load:</strong> {scenario.config.concurrentUsers} concurrent users
          </div>
        )}
        {scenario.config.duration && (
          <div className="text-sm text-gray-600">
            <strong>Duration:</strong> {Math.round(scenario.config.duration / 60)} minutes
          </div>
        )}
      </div>
      
      <button
        onClick={() => onStart(scenarioKey)}
        disabled={disabled}
        className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center space-x-2"
      >
        <Play className="w-4 h-4" />
        <span>Start Test</span>
      </button>
    </div>
  );
};

export default ProductionTester;
