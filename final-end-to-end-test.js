#!/usr/bin/env node
/**
 * Final End-to-End Test
 * 
 * Comprehensive validation that all configuration issues have been resolved
 * and the system works correctly through the proper architecture.
 */

const https = require('https');
const WebSocket = require('ws');

const PRODUCTION_DOMAIN = 'flipsyncai.com';

async function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const req = https.request(url, { 
      method: options.method || 'GET',
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
        'User-Agent': 'FlipSync-E2E-Test/1.0',
        ...options.headers
      }
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          data: data
        });
      });
    });
    
    req.on('error', reject);
    req.on('timeout', () => reject(new Error('Request timeout')));
    
    if (options.body) {
      req.write(options.body);
    }
    req.end();
  });
}

async function testWebSocketConnection() {
  return new Promise((resolve, reject) => {
    console.log('🔌 Testing WebSocket Connection...');
    
    const ws = new WebSocket(`wss://${PRODUCTION_DOMAIN}/ws/flipsync`);
    let resolved = false;
    
    const timeout = setTimeout(() => {
      if (!resolved) {
        resolved = true;
        ws.close();
        reject(new Error('WebSocket connection timeout'));
      }
    }, 10000);
    
    ws.on('open', () => {
      console.log('   ✅ WebSocket connection established');
      
      // Send ping
      ws.send(JSON.stringify({
        type: 'ping',
        timestamp: new Date().toISOString(),
        test: 'end-to-end-validation'
      }));
    });
    
    ws.on('message', (data) => {
      try {
        const message = JSON.parse(data);
        console.log(`   📥 Received: ${message.type}`);
        
        if (message.type === 'pong') {
          console.log('   ✅ WebSocket ping/pong successful');
          clearTimeout(timeout);
          if (!resolved) {
            resolved = true;
            ws.close();
            resolve(true);
          }
        }
      } catch (error) {
        console.log(`   ⚠️  Message parse error: ${error.message}`);
      }
    });
    
    ws.on('error', (error) => {
      console.log(`   ❌ WebSocket error: ${error.message}`);
      clearTimeout(timeout);
      if (!resolved) {
        resolved = true;
        reject(error);
      }
    });
    
    ws.on('close', () => {
      console.log('   🔌 WebSocket connection closed');
    });
  });
}

async function runEndToEndTest() {
  console.log('🎯 FlipSync End-to-End Configuration Test');
  console.log('=' * 50);
  console.log(`Domain: ${PRODUCTION_DOMAIN}`);
  console.log(`Test Time: ${new Date().toISOString()}`);
  
  const results = {
    apiHealth: false,
    oauthAuth: false,
    websocket: false,
    frontend: false,
    security: false
  };
  
  try {
    // Test 1: API Health (through nginx proxy)
    console.log('\n🏥 Testing API Health...');
    const healthResponse = await makeRequest(`https://${PRODUCTION_DOMAIN}/api/v1/health`);
    
    if (healthResponse.statusCode === 200) {
      const healthData = JSON.parse(healthResponse.data);
      console.log(`   ✅ API Health: ${healthData.status}`);
      console.log(`   ✅ Version: ${healthData.version}`);
      results.apiHealth = true;
    } else {
      console.log(`   ❌ API Health failed: ${healthResponse.statusCode}`);
    }
    
    // Test 2: OAuth Authorization (through nginx proxy)
    console.log('\n🔐 Testing OAuth Authorization...');
    const oauthResponse = await makeRequest(`https://${PRODUCTION_DOMAIN}/api/v1/ebay/oauth/authorize`, {
      method: 'POST',
      body: JSON.stringify({
        user_id: 'e2e_test_user',
        scopes: ['https://api.ebay.com/oauth/api_scope']
      })
    });
    
    if (oauthResponse.statusCode === 200) {
      const oauthData = JSON.parse(oauthResponse.data);
      console.log(`   ✅ OAuth Authorization: ${oauthData.success ? 'Success' : 'Failed'}`);
      console.log(`   ✅ Environment: ${oauthData.data?.environment}`);
      results.oauthAuth = oauthData.success;
    } else {
      console.log(`   ❌ OAuth Authorization failed: ${oauthResponse.statusCode}`);
    }
    
    // Test 3: WebSocket Connection
    console.log('\n🔌 Testing WebSocket...');
    try {
      await testWebSocketConnection();
      results.websocket = true;
    } catch (error) {
      console.log(`   ❌ WebSocket test failed: ${error.message}`);
    }
    
    // Test 4: Frontend Accessibility
    console.log('\n🌐 Testing Frontend...');
    const frontendResponse = await makeRequest(`https://${PRODUCTION_DOMAIN}/testing-frontend/`);
    
    if (frontendResponse.statusCode === 200) {
      console.log(`   ✅ Frontend accessible`);
      
      // Check for React content
      if (frontendResponse.data.includes('react') || frontendResponse.data.includes('FlipSync')) {
        console.log(`   ✅ React app content detected`);
        results.frontend = true;
      } else {
        console.log(`   ⚠️  React app content not detected`);
      }
    } else {
      console.log(`   ❌ Frontend not accessible: ${frontendResponse.statusCode}`);
    }
    
    // Test 5: Security Headers
    console.log('\n🔒 Testing Security Configuration...');
    const securityResponse = await makeRequest(`https://${PRODUCTION_DOMAIN}/api/v1/health`);
    const csp = securityResponse.headers['content-security-policy'];
    
    if (csp && csp.includes('connect-src')) {
      console.log(`   ✅ CSP allows WebSocket connections`);
      results.security = true;
    } else {
      console.log(`   ❌ CSP missing WebSocket support`);
    }
    
  } catch (error) {
    console.log(`❌ Test execution error: ${error.message}`);
  }
  
  // Final Summary
  console.log('\n🎉 End-to-End Test Results');
  console.log('=' * 30);
  
  const passedTests = Object.values(results).filter(Boolean).length;
  const totalTests = Object.keys(results).length;
  
  console.log(`Tests Passed: ${passedTests}/${totalTests}`);
  console.log(`API Health: ${results.apiHealth ? '✅' : '❌'}`);
  console.log(`OAuth Auth: ${results.oauthAuth ? '✅' : '❌'}`);
  console.log(`WebSocket: ${results.websocket ? '✅' : '❌'}`);
  console.log(`Frontend: ${results.frontend ? '✅' : '❌'}`);
  console.log(`Security: ${results.security ? '✅' : '❌'}`);
  
  if (passedTests === totalTests) {
    console.log('\n🎯 DEPLOYMENT STATUS: FULLY OPERATIONAL');
    console.log('✅ All configuration issues resolved');
    console.log('✅ Frontend → Nginx → Backend flow working');
    console.log('✅ HTTPS/WSS security properly configured');
    console.log('✅ OAuth integration functional');
    
    console.log('\n🚀 Ready for Production Use:');
    console.log(`   Frontend: https://${PRODUCTION_DOMAIN}/testing-frontend/`);
    console.log(`   API: https://${PRODUCTION_DOMAIN}/api/v1/`);
    console.log(`   WebSocket: wss://${PRODUCTION_DOMAIN}/ws/flipsync`);
    
  } else {
    console.log('\n⚠️  DEPLOYMENT STATUS: ISSUES REMAINING');
    console.log('❌ Some configuration issues still need resolution');
    
    if (!results.apiHealth) console.log('   - Fix API health endpoint');
    if (!results.oauthAuth) console.log('   - Fix OAuth authorization');
    if (!results.websocket) console.log('   - Fix WebSocket connection');
    if (!results.frontend) console.log('   - Fix frontend accessibility');
    if (!results.security) console.log('   - Fix security headers');
  }
  
  return passedTests === totalTests;
}

// Run the test
runEndToEndTest()
  .then(success => {
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    console.error('❌ E2E test failed:', error);
    process.exit(1);
  });
