#!/usr/bin/env node

// Test script to verify API connectivity from React frontend
const axios = require('axios');

const API_BASE = 'http://localhost:3001'; // React dev server with proxy

async function testEndpoint(name, endpoint) {
  try {
    console.log(`\n🧪 Testing ${name}...`);
    const response = await axios.get(`${API_BASE}${endpoint}`, { timeout: 5000 });
    console.log(`✅ ${name}: SUCCESS`);
    console.log(`   Status: ${response.status}`);
    console.log(`   Response: ${JSON.stringify(response.data).substring(0, 100)}...`);
    return true;
  } catch (error) {
    console.log(`❌ ${name}: FAILED`);
    console.log(`   Error: ${error.message}`);
    return false;
  }
}

async function runTests() {
  console.log('🚀 FlipSync 4+1 Architecture API Connectivity Test');
  console.log('=' .repeat(60));

  const tests = [
    ['System Health', '/api/v1/health'],
    ['4+1 Agents', '/api/v1/agents/4plus1/agents/'],
    ['Agent Decisions', '/api/v1/decisions/4plus1/decisions/'],
    ['Chat Agent Status', '/api/v1/chat/4plus1/chat/4plus1/agent-status'],
  ];

  let passed = 0;
  let total = tests.length;

  for (const [name, endpoint] of tests) {
    const success = await testEndpoint(name, endpoint);
    if (success) passed++;
  }

  console.log('\n' + '=' .repeat(60));
  console.log(`📊 Test Results: ${passed}/${total} tests passed`);
  
  if (passed === total) {
    console.log('🎉 All tests passed! Frontend is ready for testing.');
  } else {
    console.log('⚠️  Some tests failed. Check the errors above.');
  }
}

runTests().catch(console.error);
