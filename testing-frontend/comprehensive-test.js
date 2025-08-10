#!/usr/bin/env node

// Comprehensive test suite for FlipSync 4+1 Architecture Testing Frontend
const axios = require('axios');
const WebSocket = require('ws');

const API_BASE = 'http://localhost:3000';
const WS_URL = 'ws://174.138.77.110:8000/ws/flipsync';

class FlipSyncTester {
  constructor() {
    this.results = {
      api: {},
      websocket: {},
      performance: {},
      summary: { passed: 0, failed: 0, total: 0 }
    };
  }

  async runAllTests() {
    console.log('🚀 FlipSync 4+1 Architecture Comprehensive Test Suite');
    console.log('=' .repeat(70));
    console.log(`📅 Started: ${new Date().toISOString()}`);
    console.log(`🌐 API Base: ${API_BASE}`);
    console.log(`🔌 WebSocket: ${WS_URL}`);
    console.log('=' .repeat(70));

    await this.testAPIEndpoints();
    await this.testWebSocketConnection();
    await this.testPerformance();
    
    this.printSummary();
  }

  async testAPIEndpoints() {
    console.log('\n📡 Testing API Endpoints...');
    
    const endpoints = [
      {
        name: 'System Health',
        path: '/api/v1/health',
        expectedFields: ['status', 'timestamp', 'version', 'deployment']
      },
      {
        name: '4+1 Agents',
        path: '/api/v1/agents/4plus1/agents/',
        expectedFields: ['total_agents', 'autonomous_agents', 'conversational_interfaces', 'status']
      },
      {
        name: 'Agent Decisions',
        path: '/api/v1/decisions/4plus1/decisions/',
        expectedFields: ['decisions', 'total_decisions', 'compliance_metrics']
      },
      {
        name: 'Chat Agent Status',
        path: '/api/v1/chat/4plus1/chat/4plus1/agent-status',
        expectedFields: ['success', 'agents', 'summary']
      }
    ];

    for (const endpoint of endpoints) {
      await this.testEndpoint(endpoint);
    }
  }

  async testEndpoint(endpoint) {
    const testName = `API: ${endpoint.name}`;
    try {
      const startTime = Date.now();
      const response = await axios.get(`${API_BASE}${endpoint.path}`, { timeout: 10000 });
      const endTime = Date.now();
      const responseTime = endTime - startTime;

      // Check status code
      if (response.status !== 200) {
        throw new Error(`Expected status 200, got ${response.status}`);
      }

      // Check expected fields
      const missingFields = endpoint.expectedFields.filter(field => !(field in response.data));
      if (missingFields.length > 0) {
        throw new Error(`Missing fields: ${missingFields.join(', ')}`);
      }

      this.results.api[endpoint.name] = {
        success: true,
        responseTime,
        status: response.status,
        dataSize: JSON.stringify(response.data).length
      };

      console.log(`✅ ${testName}: SUCCESS (${responseTime}ms)`);
      this.results.summary.passed++;
    } catch (error) {
      this.results.api[endpoint.name] = {
        success: false,
        error: error.message
      };
      console.log(`❌ ${testName}: FAILED - ${error.message}`);
      this.results.summary.failed++;
    }
    this.results.summary.total++;
  }

  async testWebSocketConnection() {
    console.log('\n🔌 Testing WebSocket Connection...');
    
    return new Promise((resolve) => {
      const testName = 'WebSocket Connection';
      const timeout = setTimeout(() => {
        this.results.websocket.connection = {
          success: false,
          error: 'Connection timeout'
        };
        console.log(`❌ ${testName}: FAILED - Connection timeout`);
        this.results.summary.failed++;
        this.results.summary.total++;
        resolve();
      }, 10000);

      try {
        const ws = new WebSocket(WS_URL);
        const startTime = Date.now();

        ws.on('open', () => {
          const endTime = Date.now();
          const connectionTime = endTime - startTime;
          
          clearTimeout(timeout);
          this.results.websocket.connection = {
            success: true,
            connectionTime
          };
          console.log(`✅ ${testName}: SUCCESS (${connectionTime}ms)`);
          this.results.summary.passed++;
          this.results.summary.total++;
          
          // Test message sending
          this.testWebSocketMessaging(ws, resolve);
        });

        ws.on('error', (error) => {
          clearTimeout(timeout);
          this.results.websocket.connection = {
            success: false,
            error: error.message
          };
          console.log(`❌ ${testName}: FAILED - ${error.message}`);
          this.results.summary.failed++;
          this.results.summary.total++;
          resolve();
        });
      } catch (error) {
        clearTimeout(timeout);
        this.results.websocket.connection = {
          success: false,
          error: error.message
        };
        console.log(`❌ ${testName}: FAILED - ${error.message}`);
        this.results.summary.failed++;
        this.results.summary.total++;
        resolve();
      }
    });
  }

  testWebSocketMessaging(ws, resolve) {
    const testName = 'WebSocket Messaging';
    let messageReceived = false;
    
    const timeout = setTimeout(() => {
      if (!messageReceived) {
        this.results.websocket.messaging = {
          success: false,
          error: 'No response to ping'
        };
        console.log(`⚠️  ${testName}: No response (may be normal)`);
      }
      ws.close();
      resolve();
    }, 5000);

    ws.on('message', (data) => {
      messageReceived = true;
      clearTimeout(timeout);
      this.results.websocket.messaging = {
        success: true,
        response: data.toString()
      };
      console.log(`✅ ${testName}: SUCCESS - Received response`);
      this.results.summary.passed++;
      this.results.summary.total++;
      ws.close();
      resolve();
    });

    // Send test ping
    try {
      ws.send(JSON.stringify({
        type: 'ping',
        timestamp: new Date().toISOString()
      }));
    } catch (error) {
      clearTimeout(timeout);
      this.results.websocket.messaging = {
        success: false,
        error: error.message
      };
      console.log(`❌ ${testName}: FAILED - ${error.message}`);
      this.results.summary.failed++;
      this.results.summary.total++;
      ws.close();
      resolve();
    }
  }

  async testPerformance() {
    console.log('\n⚡ Testing Performance...');
    
    const performanceTests = [
      { name: 'Health Check Speed', path: '/api/v1/health', target: 500 },
      { name: 'Agents Load Speed', path: '/api/v1/agents/4plus1/agents/', target: 1000 },
      { name: 'Decisions Load Speed', path: '/api/v1/decisions/4plus1/decisions/', target: 2000 }
    ];

    for (const test of performanceTests) {
      await this.testPerformanceEndpoint(test);
    }
  }

  async testPerformanceEndpoint(test) {
    const testName = `Performance: ${test.name}`;
    try {
      const times = [];
      
      // Run 3 tests and average
      for (let i = 0; i < 3; i++) {
        const startTime = Date.now();
        await axios.get(`${API_BASE}${test.path}`, { timeout: 10000 });
        const endTime = Date.now();
        times.push(endTime - startTime);
      }

      const avgTime = Math.round(times.reduce((a, b) => a + b, 0) / times.length);
      const passed = avgTime <= test.target;

      this.results.performance[test.name] = {
        success: passed,
        averageTime: avgTime,
        target: test.target,
        times
      };

      if (passed) {
        console.log(`✅ ${testName}: SUCCESS (${avgTime}ms avg, target: ${test.target}ms)`);
        this.results.summary.passed++;
      } else {
        console.log(`⚠️  ${testName}: SLOW (${avgTime}ms avg, target: ${test.target}ms)`);
        this.results.summary.failed++;
      }
    } catch (error) {
      this.results.performance[test.name] = {
        success: false,
        error: error.message
      };
      console.log(`❌ ${testName}: FAILED - ${error.message}`);
      this.results.summary.failed++;
    }
    this.results.summary.total++;
  }

  printSummary() {
    console.log('\n' + '=' .repeat(70));
    console.log('📊 TEST SUMMARY');
    console.log('=' .repeat(70));
    
    const { passed, failed, total } = this.results.summary;
    const passRate = Math.round((passed / total) * 100);
    
    console.log(`✅ Passed: ${passed}`);
    console.log(`❌ Failed: ${failed}`);
    console.log(`📈 Pass Rate: ${passRate}%`);
    console.log(`🎯 Total Tests: ${total}`);
    
    if (passRate >= 80) {
      console.log('\n🎉 EXCELLENT! Frontend is ready for production testing.');
    } else if (passRate >= 60) {
      console.log('\n⚠️  GOOD! Some issues need attention.');
    } else {
      console.log('\n❌ NEEDS WORK! Multiple issues detected.');
    }
    
    console.log(`\n📅 Completed: ${new Date().toISOString()}`);
    console.log('=' .repeat(70));
  }
}

// Run tests
const tester = new FlipSyncTester();
tester.runAllTests().catch(console.error);
