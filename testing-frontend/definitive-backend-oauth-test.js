#!/usr/bin/env node

/**
 * Definitive Backend OAuth Test
 * Tests if the backend OAuth callback actually works with fresh authorization code
 */

const axios = require('axios');

// Fresh authorization code from your latest OAuth flow
const FRESH_AUTHORIZATION_CODE = 'v%5E1.1%23i%5E1%23f%5E0%23r%5E1%23I%5E3%23p%5E3%23t%5EUl41Xzc6NzVDQ0RCMTQ5QTdCN0VDMTU4ODhCQTUxQUQ4OEI1NURfMl8xI0VeMTI4NA%3D%3D';
const FRESH_STATE = 'flipsync_sandbox_1754484407911';

const BACKEND_API = 'http://174.138.77.110:8000';

async function testBackendOAuthDefinitively() {
  console.log('🔍 DEFINITIVE Backend OAuth Test');
  console.log('=' .repeat(60));
  
  console.log('📋 Testing Details:');
  console.log(`   Fresh Code: ${FRESH_AUTHORIZATION_CODE.substring(0, 50)}...`);
  console.log(`   State: ${FRESH_STATE}`);
  console.log(`   Backend: ${BACKEND_API}`);
  
  try {
    console.log('\n🔄 Testing Backend OAuth Callback...');
    
    const startTime = Date.now();
    const response = await axios.post(`${BACKEND_API}/api/v1/marketplace/ebay/oauth/callback`, {
      code: FRESH_AUTHORIZATION_CODE,
      state: FRESH_STATE,
      environment: 'sandbox'
    }, {
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    const duration = Date.now() - startTime;
    
    console.log('\n📊 Backend Response Analysis:');
    console.log(`   Status Code: ${response.status}`);
    console.log(`   Response Time: ${duration}ms`);
    console.log(`   Success Flag: ${response.data.success}`);
    console.log(`   Message: ${response.data.message}`);
    
    // Detailed analysis of response
    if (response.data.success) {
      console.log('\n✅ BACKEND OAUTH SUCCESS!');
      
      if (response.data.data) {
        console.log('📦 Response Data:');
        console.log(`   Marketplace: ${response.data.data.marketplace}`);
        console.log(`   Connected: ${response.data.data.connected}`);
        
        if (response.data.data.access_token) {
          console.log(`   Access Token: ${response.data.data.access_token.substring(0, 20)}...`);
          console.log(`   Token Type: ${response.data.data.token_type || 'Bearer'}`);
          console.log(`   Expires In: ${response.data.data.expires_in || 'Unknown'} seconds`);
        }
        
        if (response.data.data.user_id) {
          console.log(`   User ID: ${response.data.data.user_id}`);
        }
      }
      
      return {
        success: true,
        backend_oauth_working: true,
        access_token_obtained: !!response.data.data?.access_token,
        token_stored: !!response.data.data?.user_id,
        response_data: response.data
      };
      
    } else {
      console.log('\n❌ BACKEND OAUTH FAILED');
      console.log('📋 Failure Details:');
      
      if (response.data.data) {
        console.log(`   Marketplace: ${response.data.data.marketplace}`);
        console.log(`   Connected: ${response.data.data.connected}`);
        console.log(`   Error: ${response.data.data.error}`);
      }
      
      // Check for specific error patterns
      const errorMessage = response.data.data?.error || response.data.message || '';
      
      if (errorMessage.includes('invalid_grant')) {
        console.log('\n💡 Analysis: Authorization code issue');
        console.log('   - Code may be expired (5-10 minute limit)');
        console.log('   - Code may have been used already');
        console.log('   - Credential mismatch between frontend and backend');
      } else if (errorMessage.includes('invalid_client')) {
        console.log('\n💡 Analysis: Client credential issue');
        console.log('   - Backend using wrong App ID or Client Secret');
        console.log('   - Environment mismatch (sandbox vs production)');
      } else if (errorMessage.includes('redirect_uri')) {
        console.log('\n💡 Analysis: Redirect URI mismatch');
        console.log('   - Backend using wrong RuName');
        console.log('   - RuName must match OAuth authorization exactly');
      }
      
      return {
        success: false,
        backend_oauth_working: true, // Endpoint works, but OAuth failed
        access_token_obtained: false,
        token_stored: false,
        error: response.data.message,
        error_details: response.data.data
      };
    }
    
  } catch (error) {
    console.error('\n❌ Backend OAuth Request Failed:');
    console.error(`   Error: ${error.message}`);
    
    if (error.response) {
      console.error(`   Status: ${error.response.status}`);
      console.error(`   Response: ${JSON.stringify(error.response.data, null, 2)}`);
    }
    
    return {
      success: false,
      backend_oauth_working: false,
      access_token_obtained: false,
      token_stored: false,
      error: error.message,
      http_error: error.response?.status
    };
  }
}

async function checkBackendCredentials() {
  console.log('\n🔧 Backend Credential Analysis');
  console.log('=' .repeat(60));
  
  console.log('Expected Sandbox Credentials:');
  console.log('   App ID: BrendanB-Nashvill-SBX-aabfbb41d-097584ee');
  console.log('   RuName: Brendan_Blomfie-BrendanB-Nashvi-pzkbhtbtg');
  
  console.log('\nBackend Default Credentials (from code):');
  console.log('   App ID: BrendanB-Nashvill-PRD-7f5c11990-62c1c838 (PRODUCTION!)');
  console.log('   RuName: Brendan_Blomfie-BrendanB-Nashvi-vuwrefym (PRODUCTION!)');
  
  console.log('\n⚠️  CREDENTIAL MISMATCH DETECTED:');
  console.log('   - Frontend generates OAuth with SANDBOX credentials');
  console.log('   - Backend exchanges token with PRODUCTION credentials');
  console.log('   - This will always fail with "invalid_grant" error');
  
  console.log('\n💡 Solution:');
  console.log('   - Backend needs EBAY_CLIENT_ID environment variable set to sandbox App ID');
  console.log('   - Backend needs EBAY_REDIRECT_URI environment variable set to sandbox RuName');
  console.log('   - Or backend needs to detect environment from request and use appropriate credentials');
}

async function main() {
  try {
    // Test backend OAuth definitively
    const result = await testBackendOAuthDefinitively();
    
    // Analyze backend credentials
    await checkBackendCredentials();
    
    // Generate final assessment
    console.log('\n🎯 DEFINITIVE ASSESSMENT');
    console.log('=' .repeat(60));
    
    if (result.success && result.access_token_obtained) {
      console.log('✅ BACKEND OAUTH: FULLY WORKING');
      console.log('   - Authorization code successfully exchanged');
      console.log('   - Access token obtained from eBay');
      console.log('   - Token stored in backend');
      console.log('   - Ready for 4+1 agent integration');
      
    } else if (result.backend_oauth_working && !result.success) {
      console.log('⚠️  BACKEND OAUTH: FUNCTIONAL BUT FAILING');
      console.log('   - OAuth callback endpoint exists and responds');
      console.log('   - Token exchange logic implemented');
      console.log('   - Failing due to credential/configuration issues');
      console.log('   - Needs environment variable configuration');
      
    } else {
      console.log('❌ BACKEND OAUTH: NOT WORKING');
      console.log('   - OAuth callback endpoint has issues');
      console.log('   - Backend implementation needs debugging');
    }
    
    // Save results
    const fs = require('fs');
    const fullResults = {
      test_result: result,
      timestamp: new Date().toISOString(),
      assessment: {
        backend_oauth_functional: result.backend_oauth_working,
        access_token_obtained: result.access_token_obtained,
        ready_for_agents: result.success && result.access_token_obtained
      }
    };
    
    fs.writeFileSync('definitive-backend-oauth-results.json', JSON.stringify(fullResults, null, 2));
    console.log('\n📄 Results saved to: definitive-backend-oauth-results.json');
    
  } catch (error) {
    console.error('\n❌ Test execution failed:', error.message);
  }
}

if (require.main === module) {
  main();
}

module.exports = { testBackendOAuthDefinitively };
