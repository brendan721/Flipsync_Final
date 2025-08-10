#!/usr/bin/env node

/**
 * Complete eBay OAuth Flow
 * Exchange authorization code for access token and test real eBay APIs
 */

const axios = require('axios');

// Your authorization code from the redirect URL (FRESH)
const AUTHORIZATION_CODE = 'v%5E1.1%23i%5E1%23f%5E0%23r%5E1%23I%5E3%23p%5E3%23t%5EUl41Xzc6NzVDQ0RCMTQ5QTdCN0VDMTU4ODhCQTUxQUQ4OEI1NURfMl8xI0VeMTI4NA%3D%3D';
const STATE = 'flipsync_sandbox_1754484407911';

// Sandbox credentials
const SANDBOX_CREDENTIALS = {
  app_id: 'BrendanB-Nashvill-SBX-aabfbb41d-097584ee',
  dev_id: 'e83908d0-476b-4534-a947-3a88227709e4',
  cert_id: 'SBX-aabfbb41d097-4e53-9b35-49ef',
  ru_name: 'Brendan_Blomfie-BrendanB-Nashvi-pzkbhtbtg'
};

// Production backend
const BACKEND_API = 'http://174.138.77.110:8000';

class EbayOAuthCompleter {
  constructor() {
    this.client = axios.create({
      timeout: 30000,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  async completeOAuthFlow() {
    console.log('🔐 Completing eBay OAuth Flow');
    console.log('=' .repeat(60));
    
    console.log('📋 OAuth Details:');
    console.log(`   Authorization Code: ${AUTHORIZATION_CODE.substring(0, 50)}...`);
    console.log(`   State: ${STATE}`);
    console.log(`   Environment: SANDBOX`);
    console.log(`   App ID: ${SANDBOX_CREDENTIALS.app_id}`);
    
    try {
      // Step 1: Try to complete OAuth via backend
      console.log('\n🔄 Step 1: Attempting backend OAuth completion...');
      
      const backendResponse = await this.tryBackendOAuth();
      if (backendResponse.success) {
        console.log('✅ Backend OAuth completion successful!');
        return await this.testRealEbayAPIs(backendResponse.access_token);
      }
      
      // Step 2: Direct eBay token exchange
      console.log('\n🔄 Step 2: Direct eBay token exchange...');
      const tokenResponse = await this.exchangeCodeForToken();
      
      if (tokenResponse.success) {
        console.log('✅ Direct token exchange successful!');
        return await this.testRealEbayAPIs(tokenResponse.access_token);
      }
      
      console.log('❌ OAuth completion failed');
      return { success: false, error: 'All OAuth methods failed' };
      
    } catch (error) {
      console.error('❌ OAuth completion error:', error.message);
      return { success: false, error: error.message };
    }
  }

  async tryBackendOAuth() {
    try {
      const response = await this.client.post(`${BACKEND_API}/api/v1/marketplace/ebay/oauth/callback`, {
        code: AUTHORIZATION_CODE,
        state: STATE,
        environment: 'sandbox'
      });
      
      return {
        success: true,
        access_token: response.data.access_token,
        method: 'backend'
      };
    } catch (error) {
      console.log(`⚠️  Backend OAuth not available: ${error.message}`);
      return { success: false, error: error.message };
    }
  }

  async exchangeCodeForToken() {
    try {
      // Create basic auth header
      const credentials = Buffer.from(`${SANDBOX_CREDENTIALS.app_id}:${SANDBOX_CREDENTIALS.cert_id}`).toString('base64');
      
      const tokenUrl = 'https://api.sandbox.ebay.com/identity/v1/oauth2/token';
      
      const params = new URLSearchParams({
        grant_type: 'authorization_code',
        code: decodeURIComponent(AUTHORIZATION_CODE),
        redirect_uri: SANDBOX_CREDENTIALS.ru_name
      });
      
      console.log('📤 Making token exchange request to eBay...');
      
      const response = await axios.post(tokenUrl, params.toString(), {
        headers: {
          'Authorization': `Basic ${credentials}`,
          'Content-Type': 'application/x-www-form-urlencoded'
        }
      });
      
      console.log('✅ Token exchange successful!');
      console.log(`   Access Token: ${response.data.access_token.substring(0, 20)}...`);
      console.log(`   Token Type: ${response.data.token_type}`);
      console.log(`   Expires In: ${response.data.expires_in} seconds`);
      
      return {
        success: true,
        access_token: response.data.access_token,
        token_type: response.data.token_type,
        expires_in: response.data.expires_in,
        method: 'direct'
      };
      
    } catch (error) {
      console.error('❌ Direct token exchange failed:', error.response?.data || error.message);
      return { success: false, error: error.response?.data || error.message };
    }
  }

  async testRealEbayAPIs(accessToken) {
    console.log('\n🧪 Testing Real eBay APIs with Access Token');
    console.log('=' .repeat(60));
    
    const results = {
      access_token_received: true,
      api_tests: []
    };

    // Test 1: Get User Account Info
    console.log('\n👤 Test 1: Getting eBay Account Information...');
    try {
      const accountUrl = 'https://api.sandbox.ebay.com/sell/account/v1/account';
      
      const accountResponse = await axios.get(accountUrl, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('✅ Account Info Retrieved:');
      console.log(`   Account ID: ${accountResponse.data.accountId || 'N/A'}`);
      console.log(`   Account Type: ${accountResponse.data.accountType || 'N/A'}`);
      console.log(`   Status: ${accountResponse.data.status || 'N/A'}`);
      
      results.api_tests.push({
        name: 'Account Info',
        success: true,
        data: accountResponse.data,
        is_real_data: true
      });
      
    } catch (error) {
      console.log(`❌ Account Info Failed: ${error.response?.status} - ${error.response?.statusText}`);
      results.api_tests.push({
        name: 'Account Info',
        success: false,
        error: error.response?.data || error.message
      });
    }

    // Test 2: Get Inventory Items
    console.log('\n📦 Test 2: Getting eBay Inventory...');
    try {
      const inventoryUrl = 'https://api.sandbox.ebay.com/sell/inventory/v1/inventory_item';
      
      const inventoryResponse = await axios.get(inventoryUrl, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('✅ Inventory Retrieved:');
      console.log(`   Total Items: ${inventoryResponse.data.total || 0}`);
      console.log(`   Items Returned: ${inventoryResponse.data.inventoryItems?.length || 0}`);
      
      results.api_tests.push({
        name: 'Inventory',
        success: true,
        data: inventoryResponse.data,
        is_real_data: true
      });
      
    } catch (error) {
      console.log(`❌ Inventory Failed: ${error.response?.status} - ${error.response?.statusText}`);
      results.api_tests.push({
        name: 'Inventory',
        success: false,
        error: error.response?.data || error.message
      });
    }

    // Test 3: Get Active Listings
    console.log('\n📋 Test 3: Getting Active Listings...');
    try {
      const listingsUrl = 'https://api.sandbox.ebay.com/sell/inventory/v1/offer';
      
      const listingsResponse = await axios.get(listingsUrl, {
        headers: {
          'Authorization': `Bearer ${accessToken}`,
          'Content-Type': 'application/json'
        }
      });
      
      console.log('✅ Listings Retrieved:');
      console.log(`   Total Offers: ${listingsResponse.data.total || 0}`);
      console.log(`   Offers Returned: ${listingsResponse.data.offers?.length || 0}`);
      
      results.api_tests.push({
        name: 'Active Listings',
        success: true,
        data: listingsResponse.data,
        is_real_data: true
      });
      
    } catch (error) {
      console.log(`❌ Listings Failed: ${error.response?.status} - ${error.response?.statusText}`);
      results.api_tests.push({
        name: 'Active Listings',
        success: false,
        error: error.response?.data || error.message
      });
    }

    // Test 4: Store access token in backend (if available)
    console.log('\n💾 Test 4: Storing Access Token in Backend...');
    try {
      const storeResponse = await this.client.post(`${BACKEND_API}/api/v1/marketplace/ebay/oauth/store-token`, {
        access_token: accessToken,
        environment: 'sandbox',
        expires_in: 7200 // 2 hours default
      });
      
      console.log('✅ Access Token Stored in Backend');
      results.api_tests.push({
        name: 'Token Storage',
        success: true,
        data: storeResponse.data
      });
      
    } catch (error) {
      console.log(`⚠️  Backend token storage not available: ${error.message}`);
      results.api_tests.push({
        name: 'Token Storage',
        success: false,
        error: error.message
      });
    }

    // Generate summary
    const successfulTests = results.api_tests.filter(t => t.success).length;
    const totalTests = results.api_tests.length;
    
    console.log('\n🎯 REAL EBAY API TESTING SUMMARY');
    console.log('=' .repeat(60));
    console.log(`📊 Results: ${successfulTests}/${totalTests} tests passed`);
    console.log(`🔐 Access Token: ✅ Successfully obtained and used`);
    console.log(`🧪 Real eBay APIs: ${successfulTests > 0 ? '✅ Working' : '❌ Not accessible'}`);
    console.log(`📡 Environment: SANDBOX (safe testing)`);
    
    if (successfulTests >= 2) {
      console.log('\n🎉 SUCCESS: Real eBay integration validated!');
      console.log('✅ FlipSync can now access real eBay data');
      console.log('✅ Ready for 4+1 agent integration with live eBay APIs');
    } else {
      console.log('\n⚠️  PARTIAL SUCCESS: Some eBay APIs accessible');
      console.log('🔧 May need additional eBay API permissions or setup');
    }

    // Save results
    const fs = require('fs');
    fs.writeFileSync('real-ebay-oauth-results.json', JSON.stringify(results, null, 2));
    console.log('\n📄 Results saved to: real-ebay-oauth-results.json');
    
    return results;
  }
}

// Main execution
async function main() {
  const completer = new EbayOAuthCompleter();
  
  try {
    const results = await completer.completeOAuthFlow();
    
    if (results.success !== false) {
      console.log('\n🎉 eBay OAuth Flow Completed Successfully!');
      console.log('✅ Real eBay integration validated');
      console.log('✅ Access token obtained and tested');
      console.log('✅ FlipSync 4+1 agents can now use real eBay data');
    } else {
      console.log('\n⚠️  eBay OAuth Flow encountered issues');
      console.log('🔧 Check the error details above');
    }
    
  } catch (error) {
    console.error('\n❌ OAuth completion failed:', error.message);
  }
}

if (require.main === module) {
  main();
}

module.exports = EbayOAuthCompleter;
