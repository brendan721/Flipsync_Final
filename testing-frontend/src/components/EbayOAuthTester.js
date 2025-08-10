import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import {
  ExternalLink,
  CheckCircle,
  XCircle,
  RefreshCw,
  AlertTriangle,
  Key,
  Globe,
  Database,
  Settings,
  TestTube,
  Shield,
  Clock,
  Activity
} from 'lucide-react';
import ReactJsonView from '@microlink/react-json-view';
import api from '../services/api';
import websocket from '../services/websocket';

const EbayOAuthTester = () => {
  const [ebayStatus, setEbayStatus] = useState(null);
  const [tokenDashboard, setTokenDashboard] = useState(null);
  const [oauthStatus, setOauthStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [oauthUrl, setOauthUrl] = useState('');
  const [testResults, setTestResults] = useState({});
  const [environment, setEnvironment] = useState('sandbox'); // sandbox or production
  const [tokenEvents, setTokenEvents] = useState([]);
  // V2 OAuth system handles credentials internally - no frontend credential management needed

  useEffect(() => {
    loadEbayStatus();
    loadEnhancedTokenData();
    setupWebSocketListeners();

    return () => {
      // Cleanup WebSocket listeners
      websocket.off('token_status_changed', handleTokenStatusChange);
    };
  }, []);

  const setupWebSocketListeners = () => {
    websocket.on('token_status_changed', handleTokenStatusChange);
  };

  const handleTokenStatusChange = (eventData) => {
    console.log('🔔 Token status changed:', eventData);

    // Add to event log
    setTokenEvents(prev => [{
      timestamp: new Date().toISOString(),
      ...eventData
    }, ...prev.slice(0, 9)]); // Keep last 10 events

    // Show toast notification
    switch (eventData.type) {
      case 'refresh_success':
        toast.success(`Token refreshed for ${eventData.user_id}`);
        break;
      case 'token_cleared':
        toast.warning(`Token cleared for ${eventData.user_id}: ${eventData.reason}`);
        break;
      case 'reauth_required':
        toast.error(`Re-authentication required for ${eventData.user_id}`);
        break;
      case 'refresh_failed':
        toast.error(`Token refresh failed for ${eventData.user_id}`);
        break;
      default:
        toast.info(eventData.message);
    }

    // Reload token data
    loadEnhancedTokenData();
  };

  const loadEbayStatus = async () => {
    setIsLoading(true);
    try {
      const status = await api.getEbayStatus();
      setEbayStatus(status);

      // Update test results based on status
      setTestResults(prev => ({
        ...prev,
        status_check: {
          success: true,
          data: status,
          timestamp: new Date().toISOString()
        }
      }));
    } catch (error) {
      console.error('Failed to load eBay status:', error);
      toast.error('Failed to load eBay status');
      setTestResults(prev => ({
        ...prev,
        status_check: {
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        }
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const loadEnhancedTokenData = async () => {
    try {
      // Load token dashboard
      const dashboard = await api.getEbayTokenDashboard();
      setTokenDashboard(dashboard);

      // Load OAuth status for testuser
      const oauthStatus = await api.getEbayOAuthStatus('testuser');
      setOauthStatus(oauthStatus);

      setTestResults(prev => ({
        ...prev,
        enhanced_token_data: {
          success: true,
          dashboard: dashboard,
          oauth_status: oauthStatus,
          timestamp: new Date().toISOString()
        }
      }));

    } catch (error) {
      console.error('Failed to load enhanced token data:', error);
      setTestResults(prev => ({
        ...prev,
        enhanced_token_data: {
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        }
      }));
    }
  };

  // Removed direct OAuth URL generation - now using V2 OAuth system exclusively

  const initiateOAuth = async () => {
    setIsLoading(true);
    try {
      console.log('Using V2 OAuth system exclusively');

      // Use V2 OAuth system exclusively
      const response = await api.initializeEbayOAuth({
        user_id: 'testuser',
        scopes: [
          'https://api.ebay.com/oauth/api_scope/sell.inventory',
          'https://api.ebay.com/oauth/api_scope/sell.account',
          'https://api.ebay.com/oauth/api_scope/sell.fulfillment',
          'https://api.ebay.com/oauth/api_scope/sell.marketing'
        ]
      });

      if (response.success && response.data.authorization_url) {
        setOauthUrl(response.data.authorization_url);
        setTestResults(prev => ({
          ...prev,
          oauth_v2: {
            success: true,
            data: response.data,
            timestamp: new Date().toISOString(),
            note: 'V2 OAuth system - secure state parameter'
          }
        }));
        console.log('V2 OAuth URL generated successfully');
        toast.success('V2 OAuth URL generated successfully');
      } else {
        throw new Error(response.message || 'Failed to generate OAuth URL');
      }

    } catch (error) {
      console.error('V2 OAuth generation failed:', error);
      toast.error('V2 OAuth URL generation failed');
      setTestResults(prev => ({
        ...prev,
        oauth_error: {
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        }
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const testEbayConnection = async () => {
    setIsLoading(true);
    try {
      // Test multiple eBay endpoints
      const tests = [
        { name: 'eBay Status', endpoint: 'getEbayStatus' },
        { name: 'eBay Listings', endpoint: 'getEbayListings' }
      ];

      const results = {};
      
      for (const test of tests) {
        try {
          const result = await api[test.endpoint]();
          results[test.name] = {
            success: true,
            data: result,
            timestamp: new Date().toISOString()
          };
        } catch (error) {
          results[test.name] = {
            success: false,
            error: error.message,
            timestamp: new Date().toISOString()
          };
        }
      }

      setTestResults(prev => ({
        ...prev,
        connection_tests: results
      }));

      const successCount = Object.values(results).filter(r => r.success).length;
      toast.success(`Connection tests completed: ${successCount}/${tests.length} passed`);
      
    } catch (error) {
      console.error('Connection test failed:', error);
      toast.error('Connection test failed');
    } finally {
      setIsLoading(false);
    }
  };

  const testTokenRefresh = async () => {
    setIsLoading(true);
    try {
      const response = await api.refreshEbayToken('testuser');

      setTestResults(prev => ({
        ...prev,
        token_refresh: {
          success: response.success,
          data: response,
          timestamp: new Date().toISOString()
        }
      }));

      if (response.success) {
        toast.success('Token refresh test completed successfully');
      } else {
        toast.warning(`Token refresh test: ${response.message}`);
      }

      // Reload token data after refresh attempt
      await loadEnhancedTokenData();

    } catch (error) {
      console.error('Token refresh test failed:', error);
      toast.error('Token refresh test failed');
      setTestResults(prev => ({
        ...prev,
        token_refresh: {
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        }
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const testRealEbayAPI = async () => {
    setIsLoading(true);
    try {
      // Test multiple real eBay API endpoints
      const tests = [];

      // Test 1: Get eBay status (this endpoint exists)
      try {
        const statusResponse = await api.getEbayStatus();
        tests.push({
          name: 'eBay Status',
          success: true,
          data: statusResponse
        });
      } catch (error) {
        tests.push({
          name: 'eBay Status',
          success: false,
          error: error.message
        });
      }

      // Test 2: Get eBay inventory (correct endpoint path)
      try {
        const inventoryResponse = await api.get('/api/v1/marketplace/ebay/inventory');
        tests.push({
          name: 'eBay Inventory',
          success: true,
          data: inventoryResponse
        });
      } catch (error) {
        tests.push({
          name: 'eBay Inventory',
          success: false,
          error: error.message
        });
      }

      // Test 3: Get eBay listings (using existing method)
      try {
        const listingsResponse = await api.getEbayListings();
        tests.push({
          name: 'eBay Listings',
          success: true,
          data: listingsResponse
        });
      } catch (error) {
        tests.push({
          name: 'eBay Listings',
          success: false,
          error: error.message
        });
      }

      const successfulTests = tests.filter(t => t.success).length;
      const testResult = {
        success: successfulTests > 0,
        total_tests: tests.length,
        successful_tests: successfulTests,
        tests: tests,
        environment: environment,
        timestamp: new Date().toISOString()
      };

      setTestResults(prev => ({
        ...prev,
        real_api_test: testResult
      }));

      if (successfulTests > 0) {
        toast.success(`Real eBay API test: ${successfulTests}/${tests.length} tests passed`);
      } else {
        toast.error('All real eBay API tests failed - OAuth may be required');
      }

    } catch (error) {
      console.error('Real eBay API test failed:', error);
      toast.error('Real eBay API test failed');
      setTestResults(prev => ({
        ...prev,
        real_api_test: {
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        }
      }));
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status) => {
    if (status === true || status === 'ok') return 'text-green-600';
    if (status === false || status === 'error') return 'text-red-600';
    return 'text-yellow-600';
  };

  const getStatusIcon = (status) => {
    if (status === true || status === 'ok') return <CheckCircle className="w-4 h-4 text-green-600" />;
    if (status === false || status === 'error') return <XCircle className="w-4 h-4 text-red-600" />;
    return <AlertTriangle className="w-4 h-4 text-yellow-600" />;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">eBay OAuth Testing</h2>
          <p className="text-gray-600 mt-1">
            Test eBay OAuth flow and validate production API connectivity
          </p>
        </div>
        <button
          onClick={() => {
            loadEbayStatus();
            loadEnhancedTokenData();
          }}
          disabled={isLoading}
          className="btn-secondary disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh All
        </button>
      </div>

      {/* Environment Selection */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Settings className="w-5 h-5 mr-2" />
          Environment Configuration
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              eBay Environment
            </label>
            <select
              value={environment}
              onChange={(e) => setEnvironment(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="sandbox">Sandbox (Testing)</option>
              <option value="production">Production (Live)</option>
            </select>
            <p className="text-sm text-gray-500 mt-1">
              {environment === 'sandbox'
                ? 'Safe testing environment with fake data'
                : 'Live eBay environment with real data'}
            </p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              V2 OAuth Configuration
            </label>
            <div className="bg-gray-50 p-3 rounded-md">
              <p className="text-sm"><strong>System:</strong> V2 OAuth (Secure)</p>
              <p className="text-sm"><strong>Environment:</strong> {environment.toUpperCase()}</p>
              <p className="text-sm"><strong>Credentials:</strong> Managed by backend</p>
            </div>
          </div>
        </div>
      </div>

      {/* Enhanced Token Dashboard */}
      {tokenDashboard && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Shield className="w-5 h-5 mr-2" />
            Enhanced Token Lifecycle Dashboard
          </h3>

          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <Activity className="w-4 h-4 text-blue-600" />
              </div>
              <p className="text-sm font-medium text-gray-900">Active Tokens</p>
              <p className="text-sm text-blue-600">
                {tokenDashboard.data?.summary?.total_active_tokens || 0}
              </p>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <AlertTriangle className="w-4 h-4 text-yellow-600" />
              </div>
              <p className="text-sm font-medium text-gray-900">Need Attention</p>
              <p className="text-sm text-yellow-600">
                {tokenDashboard.data?.summary?.tokens_needing_attention || 0}
              </p>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                {tokenDashboard.data?.system_status === 'healthy' ? (
                  <CheckCircle className="w-4 h-4 text-green-600" />
                ) : (
                  <XCircle className="w-4 h-4 text-red-600" />
                )}
              </div>
              <p className="text-sm font-medium text-gray-900">System Status</p>
              <p className={`text-sm ${tokenDashboard.data?.system_status === 'healthy' ? 'text-green-600' : 'text-red-600'}`}>
                {tokenDashboard.data?.system_status || 'Unknown'}
              </p>
            </div>

            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <Globe className="w-4 h-4 text-purple-600" />
              </div>
              <p className="text-sm font-medium text-gray-900">Environments</p>
              <p className="text-sm text-purple-600">
                Sandbox: {tokenDashboard.data?.summary?.environment_distribution?.sandbox || 0} |
                Prod: {tokenDashboard.data?.summary?.environment_distribution?.production || 0}
              </p>
            </div>
          </div>

          {/* OAuth Status for testuser */}
          {oauthStatus && (
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="font-medium text-gray-900 mb-2">OAuth Status (testuser)</h4>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-gray-500">Authenticated</p>
                  <p className={`text-sm font-medium ${oauthStatus.data?.authenticated ? 'text-green-600' : 'text-red-600'}`}>
                    {oauthStatus.data?.authenticated ? 'Yes' : 'No'}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">User ID</p>
                  <p className="text-sm font-medium text-gray-900">{oauthStatus.data?.user_id}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Environment</p>
                  <p className="text-sm font-medium text-blue-600">{oauthStatus.data?.environment}</p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">Status</p>
                  <p className="text-sm font-medium text-gray-600">{oauthStatus.data?.message}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Current Status */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Database className="w-5 h-5 mr-2" />
          Legacy eBay Integration Status
        </h3>
        
        {ebayStatus ? (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                {getStatusIcon(ebayStatus.is_initialized)}
              </div>
              <p className="text-sm font-medium text-gray-900">Initialized</p>
              <p className={`text-sm ${getStatusColor(ebayStatus.is_initialized)}`}>
                {ebayStatus.is_initialized ? 'Yes' : 'No'}
              </p>
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                {getStatusIcon(ebayStatus.oauth_token_valid)}
              </div>
              <p className="text-sm font-medium text-gray-900">OAuth Token</p>
              <p className={`text-sm ${getStatusColor(ebayStatus.oauth_token_valid)}`}>
                {ebayStatus.oauth_token_valid ? 'Valid' : 'Invalid'}
              </p>
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <Globe className="w-4 h-4 text-blue-600" />
              </div>
              <p className="text-sm font-medium text-gray-900">Environment</p>
              <p className="text-sm text-blue-600">{ebayStatus.environment}</p>
            </div>
            
            <div className="text-center">
              <div className="flex items-center justify-center mb-2">
                <Key className="w-4 h-4 text-purple-600" />
              </div>
              <p className="text-sm font-medium text-gray-900">Active Listings</p>
              <p className="text-sm text-purple-600">{ebayStatus.active_listings}</p>
            </div>
          </div>
        ) : (
          <div className="text-center py-4">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-flipsync-600 mx-auto"></div>
            <p className="text-gray-600 mt-2">Loading eBay status...</p>
          </div>
        )}
      </div>

      {/* OAuth Flow Testing */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">OAuth Flow Testing</h3>
        
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <button
              onClick={initiateOAuth}
              disabled={isLoading}
              className="btn-primary disabled:opacity-50"
            >
              {isLoading ? (
                <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Key className="w-4 h-4 mr-2" />
              )}
              Generate V2 OAuth URL
            </button>

            <button
              onClick={testTokenRefresh}
              disabled={isLoading}
              className="btn-secondary disabled:opacity-50"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Test Token Refresh
            </button>

            <button
              onClick={testEbayConnection}
              disabled={isLoading}
              className="btn-secondary disabled:opacity-50"
            >
              <Globe className="w-4 h-4 mr-2" />
              Test Basic Connection
            </button>

            <button
              onClick={testRealEbayAPI}
              disabled={isLoading}
              className="btn-accent disabled:opacity-50"
            >
              <TestTube className="w-4 h-4 mr-2" />
              Test Real eBay APIs
            </button>
          </div>

          {oauthUrl && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">
                🔗 {environment.toUpperCase()} OAuth Authorization URL Generated
              </h4>
              <div className="bg-green-100 border border-green-300 rounded px-3 py-2 mb-3">
                <p className="text-sm text-green-800">
                  ✅ <strong>V2 OAuth System Active</strong> - Secure state parameter validation
                </p>
              </div>
              <p className="text-sm text-blue-700 mb-3">
                Click the link below to authorize FlipSync with your eBay account using the V2 OAuth system:
              </p>

              <div className="mb-4">
                <a
                  href={oauthUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
                >
                  <ExternalLink className="w-4 h-4 mr-2" />
                  Authorize with eBay {environment.charAt(0).toUpperCase() + environment.slice(1)}
                </a>
              </div>

              <details className="text-sm">
                <summary className="cursor-pointer text-blue-700 hover:text-blue-900">
                  Show OAuth URL Details
                </summary>
                <div className="mt-2 p-2 bg-white rounded border">
                  <p className="break-all text-xs text-gray-600">{oauthUrl}</p>
                </div>
              </details>

              <div className="mt-3 text-xs text-blue-600">
                <p>• Environment: {environment.toUpperCase()}</p>
                <p>• System: V2 OAuth (Backend Managed)</p>
                <p>• After authorization, you'll be redirected to complete the OAuth flow</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Token Lifecycle Events */}
      {tokenEvents.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Clock className="w-5 h-5 mr-2" />
            Real-time Token Events
          </h3>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {tokenEvents.map((event, index) => (
              <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center space-x-3">
                  <div className={`w-2 h-2 rounded-full ${
                    event.type === 'refresh_success' || event.type === 'proactive_refresh' ? 'bg-green-500' :
                    event.type === 'token_cleared' || event.type === 'reauth_required' ? 'bg-red-500' :
                    'bg-yellow-500'
                  }`}></div>
                  <div>
                    <p className="text-sm font-medium text-gray-900">{event.message}</p>
                    <p className="text-xs text-gray-500">
                      {event.user_id} • {new Date(event.timestamp).toLocaleTimeString()}
                    </p>
                  </div>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  event.type === 'refresh_success' || event.type === 'proactive_refresh' ? 'bg-green-100 text-green-800' :
                  event.type === 'token_cleared' || event.type === 'reauth_required' ? 'bg-red-100 text-red-800' :
                  'bg-yellow-100 text-yellow-800'
                }`}>
                  {event.type.replace('_', ' ')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Test Results */}
      {Object.keys(testResults).length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Results</h3>
          <ReactJsonView
            src={testResults}
            theme="rjv-default"
            collapsed={1}
            displayDataTypes={false}
            displayObjectSize={false}
            enableClipboard={true}
            name="test_results"
          />
        </div>
      )}
    </div>
  );
};

export default EbayOAuthTester;
