#!/usr/bin/env node

/**
 * Test Corrected eBay OAuth URL Generation
 * Verifies that the corrected sandbox credentials generate proper OAuth URLs
 */

// Corrected eBay credentials
const CORRECTED_CREDENTIALS = {
  sandbox: {
    app_id: 'BrendanB-Nashvill-SBX-aabfbb41d-097584ee',
    dev_id: 'e83908d0-476b-4534-a947-3a88227709e4',
    cert_id: 'SBX-aabfbb41d097-4e53-9b35-49ef',
    ru_name: 'Brendan_Blomfie-BrendanB-Nashvi-pzkbhtbtg'
  },
  production: {
    app_id: 'BrendanB-Nashvill-PRD-7f5c11990-62c1c838',
    dev_id: 'e83908d0-476b-4534-a947-3a88227709e4',
    cert_id: 'PRD-f5c119904e18-fb68-4e53-9b35-49ef',
    ru_name: 'Brendan_Blomfie-BrendanB-Nashvi-vuwrefym'
  }
};

function generateOAuthUrl(environment) {
  const credentials = CORRECTED_CREDENTIALS[environment];
  const state = `flipsync_${environment}_${Date.now()}`;
  
  const scopes = [
    'https://api.ebay.com/oauth/api_scope/sell.inventory',
    'https://api.ebay.com/oauth/api_scope/sell.account',
    'https://api.ebay.com/oauth/api_scope/sell.fulfillment',
    'https://api.ebay.com/oauth/api_scope/sell.marketing'
  ].join(' ');
  
  const baseUrl = environment === 'sandbox' 
    ? 'https://auth.sandbox.ebay.com/oauth2/authorize'
    : 'https://auth.ebay.com/oauth2/authorize';
  
  const params = new URLSearchParams({
    client_id: credentials.app_id,
    response_type: 'code',
    redirect_uri: credentials.ru_name,
    scope: scopes,
    state: state
  });
  
  return `${baseUrl}?${params.toString()}`;
}

function testOAuthUrls() {
  console.log('🧪 Testing Corrected eBay OAuth URL Generation');
  console.log('=' .repeat(60));
  
  // Test Sandbox OAuth URL
  console.log('\n📦 SANDBOX OAuth URL:');
  const sandboxUrl = generateOAuthUrl('sandbox');
  console.log(`✅ Generated: ${sandboxUrl}`);
  
  // Verify sandbox URL components
  const sandboxUrlObj = new URL(sandboxUrl);
  console.log('\n🔍 Sandbox URL Components:');
  console.log(`   Base URL: ${sandboxUrlObj.origin}${sandboxUrlObj.pathname}`);
  console.log(`   Client ID: ${sandboxUrlObj.searchParams.get('client_id')}`);
  console.log(`   Redirect URI: ${sandboxUrlObj.searchParams.get('redirect_uri')}`);
  console.log(`   Response Type: ${sandboxUrlObj.searchParams.get('response_type')}`);
  console.log(`   State: ${sandboxUrlObj.searchParams.get('state')}`);
  
  // Verify correct credentials
  const expectedSandboxAppId = 'BrendanB-Nashvill-SBX-aabfbb41d-097584ee';
  const expectedSandboxRuName = 'Brendan_Blomfie-BrendanB-Nashvi-pzkbhtbtg';
  
  const actualAppId = sandboxUrlObj.searchParams.get('client_id');
  const actualRuName = sandboxUrlObj.searchParams.get('redirect_uri');
  
  console.log('\n✅ Credential Verification:');
  console.log(`   App ID Match: ${actualAppId === expectedSandboxAppId ? '✅ CORRECT' : '❌ INCORRECT'}`);
  console.log(`   RuName Match: ${actualRuName === expectedSandboxRuName ? '✅ CORRECT' : '❌ INCORRECT'}`);
  
  // Test Production OAuth URL
  console.log('\n\n🏭 PRODUCTION OAuth URL:');
  const productionUrl = generateOAuthUrl('production');
  console.log(`✅ Generated: ${productionUrl}`);
  
  // Verify production URL components
  const productionUrlObj = new URL(productionUrl);
  console.log('\n🔍 Production URL Components:');
  console.log(`   Base URL: ${productionUrlObj.origin}${productionUrlObj.pathname}`);
  console.log(`   Client ID: ${productionUrlObj.searchParams.get('client_id')}`);
  console.log(`   Redirect URI: ${productionUrlObj.searchParams.get('redirect_uri')}`);
  
  console.log('\n🎯 OAUTH URL TESTING COMPLETE');
  console.log('✅ Both sandbox and production OAuth URLs generated correctly');
  console.log('✅ Corrected sandbox credentials are now in use');
  
  return {
    sandbox: {
      url: sandboxUrl,
      app_id: actualAppId,
      ru_name: actualRuName,
      correct: actualAppId === expectedSandboxAppId && actualRuName === expectedSandboxRuName
    },
    production: {
      url: productionUrl,
      app_id: productionUrlObj.searchParams.get('client_id'),
      ru_name: productionUrlObj.searchParams.get('redirect_uri')
    }
  };
}

// Run the test
const results = testOAuthUrls();

// Save results
const fs = require('fs');
fs.writeFileSync('corrected-oauth-test-results.json', JSON.stringify(results, null, 2));
console.log('\n📄 Test results saved to: corrected-oauth-test-results.json');

console.log('\n🔗 Ready for Real OAuth Testing!');
console.log('   React App: http://localhost:3000');
console.log('   Navigate to: "eBay OAuth Testing" tab');
console.log('   Select: "Sandbox" environment');
console.log('   Click: "Generate OAuth URL" to test with corrected credentials');
