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
  Database
} from 'lucide-react';
import ReactJsonView from '@microlink/react-json-view';
import api from '../services/api';

const EbayOAuthTester = () => {
  const [ebayStatus, setEbayStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [oauthUrl, setOauthUrl] = useState('');
  const [testResults, setTestResults] = useState({});

  useEffect(() => {
    loadEbayStatus();
  }, []);

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

  const initiateOAuth = async () => {
    setIsLoading(true);
    try {
      const response = await api.initializeEbayOAuth();
      
      if (response.authorization_url) {
        setOauthUrl(response.authorization_url);
        setTestResults(prev => ({
          ...prev,
          oauth_init: {
            success: true,
            data: response,
            timestamp: new Date().toISOString()
          }
        }));
        toast.success('OAuth URL generated successfully');
      } else {
        throw new Error('No authorization URL received');
      }
    } catch (error) {
      console.error('Failed to initiate OAuth:', error);
      toast.error('Failed to initiate eBay OAuth');
      setTestResults(prev => ({
        ...prev,
        oauth_init: {
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
          onClick={loadEbayStatus}
          disabled={isLoading}
          className="btn-secondary disabled:opacity-50"
        >
          <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh
        </button>
      </div>

      {/* Current Status */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
          <Database className="w-5 h-5 mr-2" />
          Current eBay Integration Status
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
          <div className="flex space-x-4">
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
              Initialize OAuth Flow
            </button>
            
            <button
              onClick={testEbayConnection}
              disabled={isLoading}
              className="btn-secondary disabled:opacity-50"
            >
              <Globe className="w-4 h-4 mr-2" />
              Test Connection
            </button>
          </div>

          {oauthUrl && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h4 className="font-medium text-blue-900 mb-2">OAuth Authorization URL Generated</h4>
              <p className="text-sm text-blue-700 mb-3">
                Click the link below to authorize FlipSync with your eBay account:
              </p>
              <a
                href={oauthUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-blue-600 hover:text-blue-800 underline"
              >
                <ExternalLink className="w-4 h-4 mr-1" />
                Authorize with eBay
              </a>
            </div>
          )}
        </div>
      </div>

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
