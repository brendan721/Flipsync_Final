#!/usr/bin/env node

/**
 * Test Fixed Backend OAuth with Environment-Specific Credentials
 * This tests the updated backend that now properly handles sandbox vs production
 */

const axios = require('axios');

const BACKEND_API = 'http://174.138.77.110:8000';

async function testBackendOAuthGeneration() {
  console.log('🔧 Testing Fixed Backend OAuth Generation');
  console.log('=' .repeat(60));
  
  const environments = ['sandbox', 'production'];
  const results = {};
  
  for (const environment of environments) {
    console.log(`\n📡 Testing ${environment.toUpperCase()} OAuth Generation...`);
    
    try {
      const response = await axios.post(`${BACKEND_API}/api/v1/marketplace/ebay/oauth/authorize`, {
        environment: environment,
        scopes: [
          'https://api.ebay.com/oauth/api_scope/sell.inventory',
          'https://api.ebay.com/oauth/api_scope/sell.account',
          'https://api.ebay.com/oauth/api_scope/sell.fulfillment'
        ]
      }, {
        timeout: 15000,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer test-token' // Mock auth for testing
        }
      });
      
      console.log(`✅ ${environment.toUpperCase()} OAuth Generation:`);
      console.log(`   Status: ${response.status}`);
      console.log(`   Success: ${response.data.success}`);
      console.log(`   Environment: ${response.data.data?.environment}`);
      console.log(`   Client ID: ${response.data.data?.client_id}`);
      
      if (response.data.data?.authorization_url) {
        const url = new URL(response.data.data.authorization_url);
        console.log(`   Base URL: ${url.origin}${url.pathname}`);
        console.log(`   Client ID in URL: ${url.searchParams.get('client_id')}`);
        console.log(`   Redirect URI: ${url.searchParams.get('redirect_uri')}`);
      }
      
      results[environment] = {
        success: true,
        data: response.data.data,
        environment_correct: response.data.data?.environment === environment
      };
      
    } catch (error) {
      console.log(`❌ ${environment.toUpperCase()} OAuth Generation Failed:`);
      console.log(`   Error: ${error.message}`);
      
      if (error.response) {
        console.log(`   Status: ${error.response.status}`);
        console.log(`   Response: ${JSON.stringify(error.response.data, null, 2)}`);
      }
      
      results[environment] = {
        success: false,
        error: error.message,
        status: error.response?.status
      };
    }
  }
  
  return results;
}

async function testCredentialMapping() {
  console.log('\n🔍 Testing Credential Mapping');
  console.log('=' .repeat(60));
  
  const expectedCredentials = {
    sandbox: {
      client_id: 'BrendanB-Nashvill-SBX-aabfbb41d-097584ee',
      redirect_uri: 'Brendan_Blomfie-BrendanB-Nashvi-pzkbhtbtg',
      base_url: 'https://auth.sandbox.ebay.com/oauth2/authorize'
    },
    production: {
      client_id: 'BrendanB-Nashvill-PRD-7f5c11990-62c1c838',
      redirect_uri: 'Brendan_Blomfie-BrendanB-Nashvi-vuwrefym',
      base_url: 'https://auth.ebay.com/oauth2/authorize'
    }
  };
  
  console.log('Expected Credential Mapping:');
  for (const [env, creds] of Object.entries(expectedCredentials)) {
    console.log(`\n${env.toUpperCase()}:`);
    console.log(`   Client ID: ${creds.client_id}`);
    console.log(`   Redirect URI: ${creds.redirect_uri}`);
    console.log(`   Base URL: ${creds.base_url}`);
  }
  
  return expectedCredentials;
}

async function validateOAuthURLs(oauthResults, expectedCredentials) {
  console.log('\n✅ Validating OAuth URL Generation');
  console.log('=' .repeat(60));
  
  const validationResults = {};
  
  for (const [environment, result] of Object.entries(oauthResults)) {
    console.log(`\n🔍 Validating ${environment.toUpperCase()}:`);
    
    if (!result.success) {
      console.log(`   ❌ OAuth generation failed - cannot validate`);
      validationResults[environment] = { valid: false, reason: 'OAuth generation failed' };
      continue;
    }
    
    const expected = expectedCredentials[environment];
    const authUrl = result.data?.authorization_url;
    
    if (!authUrl) {
      console.log(`   ❌ No authorization URL generated`);
      validationResults[environment] = { valid: false, reason: 'No authorization URL' };
      continue;
    }
    
    try {
      const url = new URL(authUrl);
      const clientId = url.searchParams.get('client_id');
      const redirectUri = url.searchParams.get('redirect_uri');
      const baseUrl = `${url.origin}${url.pathname}`;
      
      const validations = {
        client_id: clientId === expected.client_id,
        redirect_uri: redirectUri === expected.redirect_uri,
        base_url: baseUrl === expected.base_url,
        environment: result.data?.environment === environment
      };
      
      const allValid = Object.values(validations).every(v => v);
      
      console.log(`   Client ID: ${validations.client_id ? '✅' : '❌'} ${clientId}`);
      console.log(`   Redirect URI: ${validations.redirect_uri ? '✅' : '❌'} ${redirectUri}`);
      console.log(`   Base URL: ${validations.base_url ? '✅' : '❌'} ${baseUrl}`);
      console.log(`   Environment: ${validations.environment ? '✅' : '❌'} ${result.data?.environment}`);
      console.log(`   Overall: ${allValid ? '✅ VALID' : '❌ INVALID'}`);
      
      validationResults[environment] = {
        valid: allValid,
        validations: validations,
        url: authUrl
      };
      
    } catch (error) {
      console.log(`   ❌ Invalid URL format: ${error.message}`);
      validationResults[environment] = { valid: false, reason: 'Invalid URL format' };
    }
  }
  
  return validationResults;
}

async function main() {
  try {
    console.log('🚀 Testing Fixed Backend OAuth Implementation');
    console.log('Testing environment-specific credential handling');
    console.log('=' .repeat(60));
    
    // Test OAuth generation for both environments
    const oauthResults = await testBackendOAuthGeneration();
    
    // Show expected credential mapping
    const expectedCredentials = await testCredentialMapping();
    
    // Validate OAuth URLs
    const validationResults = await validateOAuthURLs(oauthResults, expectedCredentials);
    
    // Generate summary
    console.log('\n🎯 BACKEND OAUTH FIX VALIDATION SUMMARY');
    console.log('=' .repeat(60));
    
    const sandboxValid = validationResults.sandbox?.valid;
    const productionValid = validationResults.production?.valid;
    
    console.log(`📊 Results:`);
    console.log(`   Sandbox OAuth: ${sandboxValid ? '✅ WORKING' : '❌ FAILED'}`);
    console.log(`   Production OAuth: ${productionValid ? '✅ WORKING' : '❌ FAILED'}`);
    
    if (sandboxValid && productionValid) {
      console.log('\n🎉 SUCCESS: Backend OAuth Fix Complete!');
      console.log('✅ Both sandbox and production environments working');
      console.log('✅ Environment-specific credentials properly handled');
      console.log('✅ OAuth URLs generated with correct parameters');
      console.log('✅ Ready for real OAuth testing with both environments');
      
    } else if (sandboxValid || productionValid) {
      console.log('\n⚠️  PARTIAL SUCCESS: Some environments working');
      console.log(`   Working: ${sandboxValid ? 'Sandbox' : 'Production'}`);
      console.log(`   Failed: ${!sandboxValid ? 'Sandbox' : 'Production'}`);
      
    } else {
      console.log('\n❌ FAILED: Backend OAuth fix not working');
      console.log('   Both environments failed validation');
      console.log('   Check backend implementation and credentials');
    }
    
    // Save results
    const fs = require('fs');
    const fullResults = {
      oauth_generation: oauthResults,
      validation_results: validationResults,
      expected_credentials: expectedCredentials,
      timestamp: new Date().toISOString(),
      summary: {
        sandbox_working: sandboxValid,
        production_working: productionValid,
        backend_fix_successful: sandboxValid && productionValid
      }
    };
    
    fs.writeFileSync('backend-oauth-fix-validation.json', JSON.stringify(fullResults, null, 2));
    console.log('\n📄 Results saved to: backend-oauth-fix-validation.json');
    
    return fullResults.summary.backend_fix_successful;
    
  } catch (error) {
    console.error('\n❌ Test execution failed:', error.message);
    return false;
  }
}

if (require.main === module) {
  main().then(success => {
    process.exit(success ? 0 : 1);
  });
}

module.exports = { testBackendOAuthGeneration, validateOAuthURLs };
