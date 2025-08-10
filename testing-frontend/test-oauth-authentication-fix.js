#!/usr/bin/env node

/**
 * Test OAuth Authentication Fix
 * This script tests the fixed authentication flow for eBay OAuth generation
 */

const axios = require('axios');

const BACKEND_API = 'http://174.138.77.110:8000';

async function testAuthenticationFlow() {
  console.log('🔐 Testing Authentication Flow for OAuth');
  console.log('=' .repeat(60));
  
  try {
    // Step 1: Login with test credentials
    console.log('\n🔑 Step 1: Logging in with test credentials...');
    const loginResponse = await axios.post(`${BACKEND_API}/api/v1/auth/login`, {
      email: 'test@example.com',
      password: 'SecurePassword!'
    }, {
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (loginResponse.data.access_token) {
      console.log('✅ Login successful!');
      console.log(`   Token: ${loginResponse.data.access_token.substring(0, 20)}...`);
      
      const token = loginResponse.data.access_token;
      
      // Step 2: Test token validation
      console.log('\n🔍 Step 2: Validating token...');
      const validateResponse = await axios.get(`${BACKEND_API}/api/v1/auth/validate-token`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        timeout: 10000
      });
      
      console.log('✅ Token validation successful!');
      console.log(`   User: ${JSON.stringify(validateResponse.data.user || 'No user data')}`);
      
      // Step 3: Test OAuth generation with authenticated token
      console.log('\n🔗 Step 3: Testing OAuth generation with authenticated token...');
      
      const environments = ['sandbox', 'production'];
      const results = {};
      
      for (const environment of environments) {
        try {
          console.log(`\n📡 Testing ${environment.toUpperCase()} OAuth generation...`);
          
          const oauthResponse = await axios.post(`${BACKEND_API}/api/v1/marketplace/ebay/oauth/authorize`, {
            environment: environment,
            scopes: [
              'https://api.ebay.com/oauth/api_scope/sell.inventory',
              'https://api.ebay.com/oauth/api_scope/sell.account',
              'https://api.ebay.com/oauth/api_scope/sell.fulfillment'
            ]
          }, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            timeout: 15000
          });
          
          console.log(`✅ ${environment.toUpperCase()} OAuth generation successful!`);
          console.log(`   Status: ${oauthResponse.status}`);
          
          if (oauthResponse.data.authorization_url) {
            console.log(`   URL Generated: ${oauthResponse.data.authorization_url.substring(0, 80)}...`);
            results[environment] = {
              success: true,
              status: oauthResponse.status,
              authorization_url: oauthResponse.data.authorization_url,
              state: oauthResponse.data.state
            };
          } else {
            console.log(`   ⚠️  No authorization URL in response`);
            results[environment] = {
              success: false,
              error: 'No authorization URL returned',
              response: oauthResponse.data
            };
          }
          
        } catch (error) {
          console.log(`❌ ${environment.toUpperCase()} OAuth generation failed:`);
          console.log(`   Status: ${error.response?.status || 'No response'}`);
          console.log(`   Error: ${error.response?.data?.detail || error.message}`);
          
          results[environment] = {
            success: false,
            status: error.response?.status,
            error: error.response?.data?.detail || error.message
          };
        }
      }
      
      // Step 4: Summary
      console.log('\n📊 AUTHENTICATION FIX TEST RESULTS');
      console.log('=' .repeat(60));
      console.log(`✅ Login: SUCCESS`);
      console.log(`✅ Token Validation: SUCCESS`);
      console.log(`✅ Sandbox OAuth: ${results.sandbox?.success ? 'SUCCESS' : 'FAILED'}`);
      console.log(`✅ Production OAuth: ${results.production?.success ? 'SUCCESS' : 'FAILED'}`);
      
      const successCount = Object.values(results).filter(r => r.success).length;
      console.log(`\n🎯 Overall Success Rate: ${successCount}/2 OAuth endpoints working`);
      
      if (successCount === 2) {
        console.log('\n🎉 AUTHENTICATION FIX SUCCESSFUL!');
        console.log('   The React app should now be able to generate OAuth URLs');
        console.log('   when properly authenticated with test credentials.');
      } else {
        console.log('\n⚠️  PARTIAL SUCCESS - Some OAuth endpoints still failing');
      }
      
      return {
        authentication_working: true,
        oauth_results: results,
        overall_success: successCount === 2
      };
      
    } else {
      console.log('❌ Login failed - no access token received');
      return { authentication_working: false, error: 'No access token' };
    }
    
  } catch (error) {
    console.log('❌ Authentication test failed:');
    console.log(`   Status: ${error.response?.status || 'No response'}`);
    console.log(`   Error: ${error.response?.data?.detail || error.message}`);
    
    return {
      authentication_working: false,
      error: error.response?.data?.detail || error.message,
      status: error.response?.status
    };
  }
}

async function testHealthEndpoints() {
  console.log('\n🏥 Testing Health Endpoints');
  console.log('=' .repeat(40));
  
  const endpoints = [
    '/api/v1/health',
    '/api/v1/agents/4plus1/agents/',
    '/api/v1/decisions/4plus1/decisions/'
  ];
  
  for (const endpoint of endpoints) {
    try {
      const response = await axios.get(`${BACKEND_API}${endpoint}`, {
        timeout: 5000
      });
      console.log(`✅ ${endpoint}: ${response.status}`);
    } catch (error) {
      console.log(`❌ ${endpoint}: ${error.response?.status || 'Failed'}`);
    }
  }
}

// Run the tests
async function main() {
  console.log('🧪 FlipSync OAuth Authentication Fix Test');
  console.log('=' .repeat(60));
  console.log(`Backend: ${BACKEND_API}`);
  console.log(`Time: ${new Date().toISOString()}`);
  
  await testHealthEndpoints();
  const results = await testAuthenticationFlow();
  
  console.log('\n📝 Test completed. Results saved to backend-oauth-fix-validation.json');
  
  // Save results
  const fs = require('fs');
  const finalResults = {
    ...results,
    timestamp: new Date().toISOString(),
    backend_url: BACKEND_API,
    test_credentials: {
      email: 'test@example.com',
      password: 'SecurePassword!'
    }
  };
  
  fs.writeFileSync('backend-oauth-fix-validation.json', JSON.stringify(finalResults, null, 2));
}

if (require.main === module) {
  main().catch(console.error);
}
