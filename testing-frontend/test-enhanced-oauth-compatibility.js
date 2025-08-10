/**
 * Enhanced eBay OAuth V2 and Token Lifecycle Management Compatibility Test
 * Tests React frontend compatibility with the updated backend APIs
 */

const axios = require('axios');

const API_BASE_URL = 'http://174.138.77.110:8000';

class EnhancedOAuthCompatibilityTester {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });
    
    this.testResults = {
      timestamp: new Date().toISOString(),
      compatibility_issues: [],
      api_changes: [],
      frontend_updates_needed: []
    };
  }

  async runCompatibilityTests() {
    console.log('🔍 Testing React Frontend Compatibility with Enhanced eBay OAuth V2 System...\n');

    // Test 1: New Token Monitoring Endpoints
    await this.testTokenMonitoringEndpoints();
    
    // Test 2: Enhanced Error Response Formats
    await this.testEnhancedErrorFormats();
    
    // Test 3: Token Status Display Compatibility
    await this.testTokenStatusCompatibility();
    
    // Test 4: WebSocket Event Compatibility
    await this.testWebSocketEventCompatibility();
    
    // Test 5: OAuth Flow Compatibility
    await this.testOAuthFlowCompatibility();

    // Generate compatibility report
    this.generateCompatibilityReport();
    
    return this.testResults;
  }

  async testTokenMonitoringEndpoints() {
    console.log('📊 Testing Token Monitoring Endpoints...');
    
    const endpoints = [
      '/api/v1/ebay/tokens/dashboard',
      '/api/v1/ebay/tokens/status/testuser',
      '/api/v1/ebay/tokens/health',
      '/api/v1/ebay/oauth/status/testuser'
    ];

    for (const endpoint of endpoints) {
      try {
        const response = await this.client.get(endpoint);
        console.log(`✅ ${endpoint}: ${response.status}`);
        
        // Check if frontend expects different response format
        if (endpoint.includes('dashboard')) {
          this.analyzeTokenDashboardResponse(response.data);
        }
        
      } catch (error) {
        console.log(`❌ ${endpoint}: ${error.response?.status || 'Network Error'}`);
        
        if (error.response?.status === 404) {
          this.testResults.compatibility_issues.push({
            type: 'missing_endpoint',
            endpoint: endpoint,
            impact: 'Frontend may fail to load token status',
            recommendation: 'Update frontend to handle missing endpoints gracefully'
          });
        }
      }
    }
  }

  analyzeTokenDashboardResponse(data) {
    const expectedFields = ['summary', 'tokens_needing_attention', 'system_status'];
    const actualFields = Object.keys(data.data || {});
    
    const missingFields = expectedFields.filter(field => !actualFields.includes(field));
    
    if (missingFields.length > 0) {
      this.testResults.api_changes.push({
        type: 'response_format_change',
        endpoint: '/api/v1/ebay/tokens/dashboard',
        missing_fields: missingFields,
        impact: 'Frontend token dashboard may not display correctly'
      });
    }
  }

  async testEnhancedErrorFormats() {
    console.log('🚨 Testing Enhanced Error Response Formats...');
    
    try {
      // Test token refresh for non-existent user
      await this.client.post('/api/v1/ebay/tokens/refresh/nonexistent_user');
    } catch (error) {
      if (error.response?.data) {
        const errorData = error.response.data;
        
        // Check if error format matches frontend expectations
        const hasEnhancedFormat = errorData.success !== undefined && 
                                 errorData.message !== undefined &&
                                 errorData.data !== undefined;
        
        if (hasEnhancedFormat) {
          console.log('✅ Enhanced error format detected');
        } else {
          this.testResults.compatibility_issues.push({
            type: 'error_format_mismatch',
            issue: 'Backend error format may not match frontend expectations',
            current_format: errorData,
            recommendation: 'Update frontend error handling to match new format'
          });
        }
      }
    }
  }

  async testTokenStatusCompatibility() {
    console.log('🔑 Testing Token Status Display Compatibility...');
    
    try {
      const response = await this.client.get('/api/v1/ebay/oauth/status/testuser');
      const statusData = response.data;
      
      // Check if status response has fields that frontend expects
      const frontendExpectedFields = [
        'authenticated', 'user_id', 'environment', 'message'
      ];
      
      const missingFields = frontendExpectedFields.filter(
        field => !(field in statusData)
      );
      
      if (missingFields.length > 0) {
        this.testResults.frontend_updates_needed.push({
          component: 'EbayOAuthTester',
          issue: 'Token status display may be incomplete',
          missing_fields: missingFields,
          recommendation: 'Update status display logic to handle new response format'
        });
      }
      
    } catch (error) {
      console.log(`❌ Token status test failed: ${error.message}`);
    }
  }

  async testWebSocketEventCompatibility() {
    console.log('🔌 Testing WebSocket Event Compatibility...');
    
    // Simulate WebSocket events that the enhanced system might send
    const enhancedEvents = [
      {
        type: 'token_refresh_success',
        data: { user_id: 'testuser', new_expires_at: '2025-08-07T20:00:00Z' }
      },
      {
        type: 'token_cleared',
        data: { user_id: 'testuser', reason: 'encryption_key_mismatch' }
      },
      {
        type: 'reauth_required',
        data: { user_id: 'testuser', message: 'Token decryption failed - re-authentication required' }
      }
    ];
    
    // Check if frontend WebSocket service can handle these events
    this.testResults.frontend_updates_needed.push({
      component: 'WebSocketService',
      issue: 'May not handle new token lifecycle events',
      new_events: enhancedEvents.map(e => e.type),
      recommendation: 'Add event handlers for enhanced token lifecycle events'
    });
  }

  async testOAuthFlowCompatibility() {
    console.log('🔐 Testing OAuth Flow Compatibility...');
    
    try {
      // Test the OAuth initialization endpoint that frontend uses
      const response = await this.client.post('/api/v1/marketplace/ebay/oauth/authorize', {
        environment: 'sandbox',
        scopes: [
          'https://api.ebay.com/oauth/api_scope/sell.inventory',
          'https://api.ebay.com/oauth/api_scope/sell.account'
        ]
      });
      
      console.log('✅ OAuth initialization endpoint working');
      
    } catch (error) {
      if (error.response?.status === 404) {
        this.testResults.compatibility_issues.push({
          type: 'oauth_endpoint_missing',
          endpoint: '/api/v1/marketplace/ebay/oauth/authorize',
          impact: 'Frontend OAuth flow will fail',
          recommendation: 'Update frontend to use new OAuth V2 endpoints'
        });
      }
    }
  }

  generateCompatibilityReport() {
    console.log('\n📋 COMPATIBILITY ANALYSIS REPORT');
    console.log('=====================================\n');
    
    if (this.testResults.compatibility_issues.length === 0 && 
        this.testResults.api_changes.length === 0 && 
        this.testResults.frontend_updates_needed.length === 0) {
      console.log('✅ EXCELLENT: Frontend is fully compatible with enhanced backend!');
      return;
    }
    
    if (this.testResults.compatibility_issues.length > 0) {
      console.log('🚨 CRITICAL COMPATIBILITY ISSUES:');
      this.testResults.compatibility_issues.forEach((issue, i) => {
        console.log(`${i + 1}. ${issue.type}: ${issue.issue || issue.impact}`);
        console.log(`   Recommendation: ${issue.recommendation}\n`);
      });
    }
    
    if (this.testResults.api_changes.length > 0) {
      console.log('📝 API CHANGES DETECTED:');
      this.testResults.api_changes.forEach((change, i) => {
        console.log(`${i + 1}. ${change.type} in ${change.endpoint}`);
        console.log(`   Impact: ${change.impact}\n`);
      });
    }
    
    if (this.testResults.frontend_updates_needed.length > 0) {
      console.log('🔧 FRONTEND UPDATES RECOMMENDED:');
      this.testResults.frontend_updates_needed.forEach((update, i) => {
        console.log(`${i + 1}. Component: ${update.component}`);
        console.log(`   Issue: ${update.issue}`);
        console.log(`   Recommendation: ${update.recommendation}\n`);
      });
    }
  }
}

// Run the compatibility test
async function main() {
  const tester = new EnhancedOAuthCompatibilityTester();
  
  try {
    const results = await tester.runCompatibilityTests();
    
    // Save results to file
    const fs = require('fs');
    fs.writeFileSync(
      'enhanced-oauth-compatibility-results.json',
      JSON.stringify(results, null, 2)
    );
    
    console.log('\n💾 Results saved to: enhanced-oauth-compatibility-results.json');
    
  } catch (error) {
    console.error('❌ Compatibility test failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = EnhancedOAuthCompatibilityTester;
