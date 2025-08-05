#!/usr/bin/env node
/**
 * FlipSync Integration Guide Code Examples Validation
 * Tests all JavaScript examples from FRONTEND_INTEGRATION_GUIDE.md against live backend
 */

const https = require('https');
const http = require('http');
const WebSocket = require('ws');

// Configuration from integration guide
const FLIPSYNC_CONFIG = {
  baseURL: 'http://174.138.77.110',
  wsURL: 'ws://174.138.77.110/ws/flipsync',
  apiVersion: 'v1',
  timeout: 30000,
  retryAttempts: 3
};

// Test results tracking
const testResults = {
  passed: 0,
  failed: 0,
  total: 0,
  details: []
};

// Helper function to make HTTP requests
const makeRequest = (url, options = {}) => {
  return new Promise((resolve, reject) => {
    const urlObj = new URL(url);
    const requestOptions = {
      hostname: urlObj.hostname,
      port: urlObj.port || (urlObj.protocol === 'https:' ? 443 : 80),
      path: urlObj.pathname + urlObj.search,
      method: options.method || 'GET',
      headers: options.headers || {},
      timeout: FLIPSYNC_CONFIG.timeout
    };

    const req = (urlObj.protocol === 'https:' ? https : http).request(requestOptions, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const jsonData = JSON.parse(data);
          resolve({ status: res.statusCode, data: jsonData, headers: res.headers });
        } catch (e) {
          resolve({ status: res.statusCode, data: data, headers: res.headers });
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => reject(new Error('Request timeout')));
    
    if (options.body) {
      req.write(typeof options.body === 'string' ? options.body : JSON.stringify(options.body));
    }
    
    req.end();
  });
};

// Test function wrapper
const runTest = async (testName, testFunction) => {
  testResults.total++;
  console.log(`\n🧪 Testing: ${testName}`);
  
  try {
    const result = await testFunction();
    if (result.success) {
      testResults.passed++;
      console.log(`✅ PASS: ${testName}`);
      if (result.details) console.log(`   ${result.details}`);
    } else {
      testResults.failed++;
      console.log(`❌ FAIL: ${testName}`);
      console.log(`   Error: ${result.error}`);
    }
    testResults.details.push({ name: testName, ...result });
  } catch (error) {
    testResults.failed++;
    console.log(`❌ FAIL: ${testName}`);
    console.log(`   Exception: ${error.message}`);
    testResults.details.push({ name: testName, success: false, error: error.message });
  }
};

// Test 1: Health Check (from integration guide example)
const testHealthCheck = async () => {
  try {
    const response = await makeRequest(`${FLIPSYNC_CONFIG.baseURL}/api/v1/health`);
    
    if (response.status === 200 && response.data.status === 'ok') {
      return { 
        success: true, 
        details: `Status: ${response.data.status}, Response time: ${response.data.timestamp ? 'included' : 'missing'}` 
      };
    } else {
      return { 
        success: false, 
        error: `Expected 200 OK with status='ok', got ${response.status} with status='${response.data.status}'` 
      };
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
};

// Test 2: Agent Status Endpoint
const testAgentStatus = async () => {
  try {
    const response = await makeRequest(`${FLIPSYNC_CONFIG.baseURL}/api/v1/agents/status`);
    
    if (response.status === 200 && response.data.agents) {
      const agentCount = response.data.agents.length;
      return { 
        success: true, 
        details: `Found ${agentCount} agents, expected 4+1 architecture` 
      };
    } else {
      return { 
        success: false, 
        error: `Expected 200 OK with agents array, got ${response.status}` 
      };
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
};

// Test 3: AI Status Endpoint (recently fixed)
const testAIStatus = async () => {
  try {
    const response = await makeRequest(`${FLIPSYNC_CONFIG.baseURL}/api/v1/ai/status`);
    
    if (response.status === 200 && response.data.success) {
      return { 
        success: true, 
        details: `AI integration: ${response.data.ai_status.ai_integration}, adapter: ${response.data.ai_status.adapter_type}` 
      };
    } else {
      return { 
        success: false, 
        error: `Expected 200 OK with success=true, got ${response.status}` 
      };
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
};

// Test 4: Authentication Error Handling (recently improved)
const testAuthErrorHandling = async () => {
  try {
    const response = await makeRequest(`${FLIPSYNC_CONFIG.baseURL}/api/v1/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: 'test@example.com', password: 'invalid' })
    });
    
    // Should return 401 (invalid credentials) or 503 (service unavailable), not 500
    if (response.status === 401 || response.status === 503) {
      return { 
        success: true, 
        details: `Proper error handling: ${response.status} ${response.status === 401 ? 'Unauthorized' : 'Service Unavailable'}` 
      };
    } else if (response.status === 500) {
      return { 
        success: false, 
        error: `Still returning 500 error instead of proper 401/503` 
      };
    } else {
      return { 
        success: false, 
        error: `Unexpected status code: ${response.status}` 
      };
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
};

// Test 5: WebSocket Connection
const testWebSocket = () => {
  return new Promise((resolve) => {
    try {
      const ws = new WebSocket(FLIPSYNC_CONFIG.wsURL);
      let connected = false;
      
      const timeout = setTimeout(() => {
        if (!connected) {
          ws.terminate();
          resolve({ success: false, error: 'WebSocket connection timeout' });
        }
      }, 10000);
      
      ws.on('open', () => {
        connected = true;
        clearTimeout(timeout);
        
        // Send test message as shown in integration guide
        ws.send(JSON.stringify({ type: 'ping', data: 'test' }));
        
        setTimeout(() => {
          ws.close();
          resolve({ success: true, details: 'WebSocket connected and test message sent' });
        }, 1000);
      });
      
      ws.on('error', (error) => {
        clearTimeout(timeout);
        resolve({ success: false, error: `WebSocket error: ${error.message}` });
      });
      
    } catch (error) {
      resolve({ success: false, error: error.message });
    }
  });
};

// Test 6: API Client Class Example
const testAPIClientClass = async () => {
  try {
    // Simulate the FlipSyncAPI class from integration guide
    class FlipSyncAPI {
      constructor(baseURL, token = null) {
        this.baseURL = baseURL;
        this.token = token;
        this.headers = {
          'Content-Type': 'application/json',
          ...(token && { 'Authorization': `Bearer ${token}` })
        };
      }
      
      async get(endpoint) {
        const response = await makeRequest(`${this.baseURL}${endpoint}`, {
          headers: this.headers
        });
        return response;
      }
    }
    
    const api = new FlipSyncAPI(FLIPSYNC_CONFIG.baseURL);
    const response = await api.get('/api/v1/health');
    
    if (response.status === 200) {
      return { success: true, details: 'API client class works correctly' };
    } else {
      return { success: false, error: `API client returned ${response.status}` };
    }
  } catch (error) {
    return { success: false, error: error.message };
  }
};

// Main test runner
const runAllTests = async () => {
  console.log('🚀 FlipSync Integration Guide Code Examples Validation');
  console.log('=' * 60);
  console.log(`Testing against: ${FLIPSYNC_CONFIG.baseURL}`);
  console.log(`WebSocket URL: ${FLIPSYNC_CONFIG.wsURL}`);
  
  // Run all tests
  await runTest('Health Check Example', testHealthCheck);
  await runTest('Agent Status Endpoint', testAgentStatus);
  await runTest('AI Status Endpoint (Fixed)', testAIStatus);
  await runTest('Authentication Error Handling (Improved)', testAuthErrorHandling);
  await runTest('WebSocket Connection Example', testWebSocket);
  await runTest('API Client Class Example', testAPIClientClass);
  
  // Print summary
  console.log('\n' + '=' * 60);
  console.log('📊 TEST SUMMARY');
  console.log('=' * 60);
  console.log(`Total Tests: ${testResults.total}`);
  console.log(`✅ Passed: ${testResults.passed}`);
  console.log(`❌ Failed: ${testResults.failed}`);
  console.log(`📈 Success Rate: ${((testResults.passed / testResults.total) * 100).toFixed(1)}%`);
  
  if (testResults.failed > 0) {
    console.log('\n❌ FAILED TESTS:');
    testResults.details.filter(t => !t.success).forEach(test => {
      console.log(`  - ${test.name}: ${test.error}`);
    });
  }
  
  console.log('\n✅ VALIDATION COMPLETE');
  
  // Return results for further processing
  return testResults;
};

// Run tests if called directly
if (require.main === module) {
  runAllTests().catch(console.error);
}

module.exports = { runAllTests, FLIPSYNC_CONFIG };
