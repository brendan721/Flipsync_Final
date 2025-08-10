import React, { useState, useEffect } from 'react';
import { AlertTriangle, CheckCircle, Settings, Globe, Wifi, Shield } from 'lucide-react';
import { validateConfiguration, getEnvironmentConfig } from '../config/environment.js';

/**
 * Configuration Validator Component
 * 
 * Displays current environment configuration and validates for issues.
 * Helps catch configuration problems before they cause runtime errors.
 */
const ConfigurationValidator = () => {
  const [validation, setValidation] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // Validate configuration on component mount
    const result = validateConfiguration();
    setValidation(result);
    
    // Auto-expand if there are issues
    if (result.issues.length > 0) {
      setIsExpanded(true);
    }
    
    // Log configuration for debugging
    console.group('🔧 Configuration Validation');
    console.log('Environment:', result.config.ENVIRONMENT);
    console.log('Valid:', result.isValid);
    console.log('Issues:', result.issues.length);
    console.groupEnd();
  }, []);

  if (!validation) {
    return (
      <div className="bg-gray-100 p-4 rounded-lg">
        <div className="flex items-center space-x-2">
          <Settings className="w-4 h-4 animate-spin" />
          <span>Loading configuration...</span>
        </div>
      </div>
    );
  }

  const { config, issues, isValid } = validation;

  return (
    <div className={`border rounded-lg p-4 ${isValid ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'}`}>
      {/* Header */}
      <div 
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center space-x-2">
          {isValid ? (
            <CheckCircle className="w-5 h-5 text-green-600" />
          ) : (
            <AlertTriangle className="w-5 h-5 text-red-600" />
          )}
          <h3 className="font-semibold">
            Configuration Status: {isValid ? 'Valid' : `${issues.length} Issues`}
          </h3>
        </div>
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <span>{config.ENVIRONMENT_NAME}</span>
          <Settings className={`w-4 h-4 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="mt-4 space-y-4">
          {/* Configuration Summary */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Globe className="w-4 h-4 text-blue-600" />
                <span className="font-medium">API Configuration</span>
              </div>
              <div className="text-sm space-y-1 ml-6">
                <div>Base URL: <code className="bg-gray-200 px-1 rounded">{config.API_BASE_URL || 'Relative URLs'}</code></div>
                <div>Protocol: <span className={config.USE_HTTPS ? 'text-green-600' : 'text-orange-600'}>{config.USE_HTTPS ? 'HTTPS' : 'HTTP'}</span></div>
                <div>Environment: <span className="font-medium">{config.ENVIRONMENT}</span></div>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex items-center space-x-2">
                <Wifi className="w-4 h-4 text-purple-600" />
                <span className="font-medium">WebSocket Configuration</span>
              </div>
              <div className="text-sm space-y-1 ml-6">
                <div>Base URL: <code className="bg-gray-200 px-1 rounded">{config.WS_BASE_URL}</code></div>
                <div>Protocol: <span className={config.WS_BASE_URL.startsWith('wss:') ? 'text-green-600' : 'text-orange-600'}>{config.WS_BASE_URL.startsWith('wss:') ? 'WSS (Secure)' : 'WS (Insecure)'}</span></div>
                <div>Endpoint: <code className="bg-gray-200 px-1 rounded">/ws/flipsync</code></div>
              </div>
            </div>
          </div>

          {/* Security Status */}
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Shield className="w-4 h-4 text-green-600" />
              <span className="font-medium">Security Status</span>
            </div>
            <div className="text-sm space-y-1 ml-6">
              <div>Page Protocol: <span className="font-medium">{config.DETECTED_PROTOCOL}</span></div>
              <div>Hostname: <span className="font-medium">{config.DETECTED_HOSTNAME}</span></div>
              <div>Debug Mode: <span className={config.ENABLE_DEBUG ? 'text-orange-600' : 'text-green-600'}>{config.ENABLE_DEBUG ? 'Enabled' : 'Disabled'}</span></div>
            </div>
          </div>

          {/* Issues */}
          {issues.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium text-red-600 flex items-center space-x-2">
                <AlertTriangle className="w-4 h-4" />
                <span>Configuration Issues</span>
              </h4>
              <div className="space-y-2">
                {issues.map((issue, index) => (
                  <div key={index} className="bg-red-100 border border-red-200 rounded p-3">
                    <div className="font-medium text-red-800">{issue.type}</div>
                    <div className="text-red-700 text-sm">{issue.message}</div>
                    <div className="text-red-600 text-sm mt-1">
                      <strong>Fix:</strong> {issue.fix}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Architecture Flow */}
          <div className="space-y-2">
            <h4 className="font-medium">Request Flow Architecture</h4>
            <div className="text-sm bg-gray-100 p-3 rounded">
              {config.ENVIRONMENT === 'production' ? (
                <div>
                  <div className="font-medium text-green-600">✅ Production Flow (Correct):</div>
                  <div className="mt-1">Frontend → Nginx Proxy → Backend</div>
                  <div className="text-xs text-gray-600 mt-1">
                    HTTPS requests to flipsyncai.com are proxied to backend
                  </div>
                </div>
              ) : (
                <div>
                  <div className="font-medium text-blue-600">🔧 Development Flow:</div>
                  <div className="mt-1">Frontend → {config.API_BASE_URL ? 'Direct Backend' : 'React Proxy'} → Backend</div>
                  <div className="text-xs text-gray-600 mt-1">
                    {config.API_BASE_URL ? 'Direct connection for testing' : 'Using React dev server proxy'}
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Timestamp */}
          <div className="text-xs text-gray-500 border-t pt-2">
            Configuration validated at: {config.TIMESTAMP}
          </div>
        </div>
      )}
    </div>
  );
};

export default ConfigurationValidator;
