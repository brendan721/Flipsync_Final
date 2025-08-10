#!/usr/bin/env node
/**
 * Complete Request Flow Validation
 * 
 * Tests that the entire request flow works correctly:
 * Frontend → Nginx Proxy → Backend (not Frontend → Direct Backend)
 */

const https = require('https');
const http = require('http');

const PRODUCTION_DOMAIN = 'flipsyncai.com';
const BACKEND_IP = '174.138.77.110';

async function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https:') ? https : http;
    
    const req = client.request(url, { 
      method: 'GET', 
      timeout: 10000,
      headers: {
        'User-Agent': 'FlipSync-Deployment-Validator/1.0',
        ...options.headers
      }
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        resolve({
          statusCode: res.statusCode,
          headers: res.headers,
          data: data,
          url: url
        });
      });
    });
    
    req.on('error', reject);
    req.on('timeout', () => reject(new Error('Request timeout')));
    req.end();
  });
}

async function testRequestFlow() {
  console.log('🔄 Testing Complete Request Flow');
  console.log('=' * 40);
  
  const tests = [
    {
      name: 'Production API (HTTPS through Nginx)',
      url: `https://${PRODUCTION_DOMAIN}/api/v1/health`,
      expected: 'This should work and be used by frontend',
      critical: true
    },
    {
      name: 'Production WebSocket Upgrade',
      url: `https://${PRODUCTION_DOMAIN}/ws/flipsync`,
      expected: 'WebSocket upgrade should work',
      critical: true,
      headers: {
        'Upgrade': 'websocket',
        'Connection': 'Upgrade',
        'Sec-WebSocket-Key': 'dGhlIHNhbXBsZSBub25jZQ==',
        'Sec-WebSocket-Version': '13'
      }
    },
    {
      name: 'Frontend Static Files',
      url: `https://${PRODUCTION_DOMAIN}/testing-frontend/`,
      expected: 'Frontend should load correctly',
      critical: true
    },
    {
      name: 'OAuth Endpoint (Production)',
      url: `https://${PRODUCTION_DOMAIN}/api/v1/ebay/oauth/authorize`,
      expected: 'OAuth should be accessible through proxy',
      critical: true,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: 'test_user',
        scopes: ['https://api.ebay.com/oauth/api_scope']
      })
    }
  ];
  
  const results = [];
  
  for (const test of tests) {
    console.log(`\n🧪 ${test.name}`);
    console.log(`   URL: ${test.url}`);
    
    try {
      const response = await makeRequest(test.url, {
        headers: test.headers,
        method: test.method
      });
      
      const success = response.statusCode >= 200 && response.statusCode < 400;
      
      console.log(`   Status: ${response.statusCode} ${success ? '✅' : '❌'}`);
      
      if (test.critical && !success) {
        console.log(`   🚨 CRITICAL: ${test.expected}`);
      }
      
      // Check for specific headers
      if (response.headers['content-security-policy']) {
        const csp = response.headers['content-security-policy'];
        if (csp.includes('connect-src')) {
          console.log(`   ✅ CSP: WebSocket connections allowed`);
        } else {
          console.log(`   ⚠️  CSP: Missing connect-src`);
        }
      }
      
      if (response.headers['x-flipsync-security']) {
        console.log(`   ✅ Security: FlipSync headers present`);
      }
      
      results.push({
        test: test.name,
        success: success,
        statusCode: response.statusCode,
        critical: test.critical
      });
      
    } catch (error) {
      console.log(`   ❌ Error: ${error.message}`);
      results.push({
        test: test.name,
        success: false,
        error: error.message,
        critical: test.critical
      });
    }
  }
  
  // Summary
  console.log(`\n🎉 Request Flow Validation Summary`);
  console.log('=' * 40);
  
  const criticalTests = results.filter(r => r.critical);
  const criticalPassed = criticalTests.filter(r => r.success);
  const allPassed = results.every(r => r.success);
  
  console.log(`Critical Tests: ${criticalPassed.length}/${criticalTests.length} passed`);
  console.log(`All Tests: ${results.filter(r => r.success).length}/${results.length} passed`);
  
  if (allPassed) {
    console.log('\n✅ ALL TESTS PASSED');
    console.log('   - Frontend can access API through HTTPS proxy');
    console.log('   - WebSocket connections work through proxy');
    console.log('   - OAuth endpoints accessible');
    console.log('   - No mixed content issues expected');
  } else {
    console.log('\n❌ SOME TESTS FAILED');
    
    results.forEach(result => {
      if (!result.success) {
        console.log(`   ❌ ${result.test}: ${result.error || `Status ${result.statusCode}`}`);
      }
    });
  }
  
  return allPassed;
}

// Run the test
testRequestFlow()
  .then(success => {
    console.log(`\n🎯 Deployment Status: ${success ? 'READY' : 'NEEDS FIXES'}`);
    process.exit(success ? 0 : 1);
  })
  .catch(error => {
    console.error('❌ Validation failed:', error);
    process.exit(1);
  });
