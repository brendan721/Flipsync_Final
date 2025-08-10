#!/usr/bin/env node

/**
 * Test OAuth Callback with Backend
 * This tests the actual backend callback handling with your OAuth code
 */

const axios = require('axios');

const BACKEND_API = 'http://174.138.77.110:8000';

// Your actual OAuth callback data
const OAUTH_DATA = {
  state: 'flipsync_sandbox_1754486008184',
  code: 'v%5E1.1%23i%5E1%23I%5E3%23r%5E1%23f%5E0%23p%5E3%23t%5EUl41XzA6OUFGNTZDMDYzN0QxOTIwM0I0QjE2QjFEMzY2QUI2M0FfMF8xI0VeMTI4NA%3D%3D',
  expires_in: 299
};

async function testBackendCallback() {
  console.log('🔄 Testing Backend OAuth Callback Processing');
  console.log('=' .repeat(60));
  console.log(`Backend: ${BACKEND_API}`);
  console.log(`State: ${OAUTH_DATA.state}`);
  console.log(`Code: ${OAUTH_DATA.code.substring(0, 50)}...`);
  
  try {
    // Test 1: GET request (browser simulation)
    console.log('\n📡 Test 1: GET request (simulating browser callback)...');
    const getResponse = await axios.get(`${BACKEND_API}/api/v1/marketplace/ebay/oauth/callback`, {
      params: OAUTH_DATA,
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
      },
      timeout: 30000
    });
    
    console.log(`✅ GET Response Status: ${getResponse.status}`);
    console.log(`   Content Type: ${getResponse.headers['content-type']}`);
    
    if (getResponse.headers['content-type']?.includes('text/html')) {
      console.log('   ✅ Received HTML response (expected for browser)');
      // Check if HTML contains success indicators
      const html = getResponse.data;
      const isSuccess = html.includes('success') || html.includes('✅') || html.includes('connected');
      console.log(`   OAuth Success: ${isSuccess ? '✅ YES' : '❌ NO'}`);
      
      if (isSuccess) {
        console.log('   🎉 Backend successfully processed OAuth callback!');
        console.log('   💾 Access token should now be stored in Redis');
      }
    } else {
      console.log('   📄 Response Data:', JSON.stringify(getResponse.data, null, 2));
    }
    
  } catch (error) {
    console.log(`❌ GET request failed:`);
    console.log(`   Status: ${error.response?.status || 'No response'}`);
    console.log(`   Error: ${error.response?.data || error.message}`);
  }
  
  try {
    // Test 2: POST request (API simulation)
    console.log('\n📡 Test 2: POST request (simulating API callback)...');
    const postResponse = await axios.post(`${BACKEND_API}/api/v1/marketplace/ebay/oauth/callback`, {
      ...OAUTH_DATA,
      environment: 'sandbox'
    }, {
      headers: {
        'Content-Type': 'application/json'
      },
      timeout: 30000
    });
    
    console.log(`✅ POST Response Status: ${postResponse.status}`);
    console.log('   📄 Response Data:', JSON.stringify(postResponse.data, null, 2));
    
    if (postResponse.data.success) {
      console.log('   🎉 Backend successfully processed OAuth callback via POST!');
      console.log('   💾 Access token should now be stored in Redis');
    }
    
  } catch (error) {
    console.log(`❌ POST request failed:`);
    console.log(`   Status: ${error.response?.status || 'No response'}`);
    console.log(`   Error: ${error.response?.data || error.message}`);
  }
}

async function testTokenStorage() {
  console.log('\n💾 Testing Token Storage in Backend');
  console.log('=' .repeat(40));
  
  try {
    // Test eBay status to see if tokens are stored
    const statusResponse = await axios.get(`${BACKEND_API}/api/v1/marketplace/ebay/status`, {
      timeout: 10000
    });
    
    console.log('✅ eBay Status Response:');
    console.log(JSON.stringify(statusResponse.data, null, 2));
    
    const hasToken = statusResponse.data.oauth_token_valid;
    console.log(`\n🔑 OAuth Token Status: ${hasToken ? '✅ VALID' : '❌ INVALID/MISSING'}`);
    
    if (hasToken) {
      console.log('🎉 SUCCESS: OAuth token is stored and valid in backend!');
    } else {
      console.log('⚠️  Token not found or invalid - callback may not have processed correctly');
    }
    
  } catch (error) {
    console.log(`❌ Status check failed: ${error.message}`);
  }
}

async function testEbayAPIAccess() {
  console.log('\n🔌 Testing eBay API Access with Stored Token');
  console.log('=' .repeat(50));
  
  try {
    // Test eBay listings endpoint
    const listingsResponse = await axios.get(`${BACKEND_API}/api/v1/marketplace/ebay/listings`, {
      timeout: 15000
    });
    
    console.log('✅ eBay Listings Response:');
    console.log(JSON.stringify(listingsResponse.data, null, 2));
    
    const hasListings = listingsResponse.data.active_listings?.length > 0;
    console.log(`\n📋 Active Listings: ${hasListings ? listingsResponse.data.active_listings.length : 0}`);
    
    if (listingsResponse.data.success) {
      console.log('🎉 SUCCESS: Backend can access eBay API with stored token!');
    }
    
  } catch (error) {
    console.log(`❌ eBay API access failed:`);
    console.log(`   Status: ${error.response?.status || 'No response'}`);
    console.log(`   Error: ${error.response?.data || error.message}`);
  }
}

async function main() {
  console.log('🧪 FlipSync OAuth Callback Backend Test');
  console.log('=' .repeat(60));
  console.log(`Time: ${new Date().toISOString()}`);
  
  await testBackendCallback();
  await testTokenStorage();
  await testEbayAPIAccess();
  
  console.log('\n📋 SUMMARY');
  console.log('=' .repeat(30));
  console.log('This test validates:');
  console.log('1. ✅ Backend can process OAuth callbacks');
  console.log('2. ✅ Tokens are stored in Redis');
  console.log('3. ✅ Backend can access eBay APIs with stored tokens');
  console.log('\nIf all tests pass, the OAuth flow is working correctly!');
  console.log('The issue is just that the RuName needs to be mapped to the correct callback URL in eBay Developer Console.');
}

if (require.main === module) {
  main().catch(console.error);
}
