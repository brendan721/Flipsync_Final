/**
 * FlipSync Environment Configuration
 * 
 * Provides proper environment-based configuration for API endpoints,
 * WebSocket URLs, and deployment settings.
 * 
 * ARCHITECTURE:
 * - Development: Uses proxy or direct backend access
 * - Production: Uses HTTPS through nginx proxy (Frontend → Nginx → Backend)
 */

/**
 * Detect the current deployment environment
 */
function detectEnvironment() {
  // Check if we're in a React development server
  if (process.env.NODE_ENV === 'development') {
    return 'development';
  }
  
  // Check hostname to determine production environment
  const hostname = window.location.hostname;
  
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'local';
  }
  
  if (hostname === 'flipsyncai.com' || hostname === 'www.flipsyncai.com') {
    return 'production';
  }
  
  // Default to production for unknown hostnames
  return 'production';
}

/**
 * Environment-specific configuration
 */
const ENVIRONMENT_CONFIG = {
  development: {
    // Development uses React proxy or relative URLs
    API_BASE_URL: '',
    WS_BASE_URL: 'ws://174.138.77.110:8000',
    OAUTH_REDIRECT_BASE: 'http://localhost:3000',
    ENVIRONMENT_NAME: 'Development',
    USE_HTTPS: false,
    ENABLE_DEBUG: true
  },
  
  local: {
    // Local testing against production backend
    API_BASE_URL: 'http://174.138.77.110:8000',
    WS_BASE_URL: 'ws://174.138.77.110:8000',
    OAUTH_REDIRECT_BASE: 'http://localhost:3000',
    ENVIRONMENT_NAME: 'Local Testing',
    USE_HTTPS: false,
    ENABLE_DEBUG: true
  },
  
  production: {
    // Production uses HTTPS through nginx proxy
    API_BASE_URL: 'https://flipsyncai.com',
    WS_BASE_URL: 'wss://flipsyncai.com',
    OAUTH_REDIRECT_BASE: 'https://flipsyncai.com',
    ENVIRONMENT_NAME: 'Production',
    USE_HTTPS: true,
    ENABLE_DEBUG: false
  }
};

/**
 * Get current environment configuration
 */
export function getEnvironmentConfig() {
  const environment = detectEnvironment();
  const config = ENVIRONMENT_CONFIG[environment];
  
  return {
    ...config,
    ENVIRONMENT: environment,
    DETECTED_HOSTNAME: window.location.hostname,
    DETECTED_PROTOCOL: window.location.protocol,
    TIMESTAMP: new Date().toISOString()
  };
}

/**
 * Get API base URL for the current environment
 */
export function getApiBaseUrl() {
  const config = getEnvironmentConfig();
  return config.API_BASE_URL;
}

/**
 * Get WebSocket URL for the current environment
 */
export function getWebSocketUrl(path = '/ws/flipsync') {
  const config = getEnvironmentConfig();
  return `${config.WS_BASE_URL}${path}`;
}

/**
 * Get OAuth redirect URL for the current environment
 */
export function getOAuthRedirectUrl(path = '/ebay-oauth') {
  const config = getEnvironmentConfig();
  return `${config.OAUTH_REDIRECT_BASE}${path}`;
}

/**
 * Validate current configuration
 */
export function validateConfiguration() {
  const config = getEnvironmentConfig();
  const issues = [];
  
  // Check for mixed content issues
  if (window.location.protocol === 'https:' && !config.USE_HTTPS) {
    issues.push({
      type: 'MIXED_CONTENT_ERROR',
      message: 'HTTPS page trying to use HTTP API endpoints',
      severity: 'CRITICAL',
      fix: 'Update API_BASE_URL to use HTTPS'
    });
  }
  
  // Check for direct backend access in production
  if (config.ENVIRONMENT === 'production' && config.API_BASE_URL.includes('174.138.77.110')) {
    issues.push({
      type: 'ARCHITECTURE_VIOLATION',
      message: 'Production frontend bypassing nginx proxy',
      severity: 'CRITICAL',
      fix: 'Use nginx proxy endpoints instead of direct backend access'
    });
  }
  
  // Check WebSocket protocol consistency
  const wsProtocol = config.WS_BASE_URL.startsWith('wss:') ? 'secure' : 'insecure';
  const pageProtocol = window.location.protocol === 'https:' ? 'secure' : 'insecure';
  
  if (wsProtocol !== pageProtocol) {
    issues.push({
      type: 'WEBSOCKET_PROTOCOL_MISMATCH',
      message: `WebSocket protocol (${wsProtocol}) doesn't match page protocol (${pageProtocol})`,
      severity: 'HIGH',
      fix: 'Ensure WebSocket and page protocols match'
    });
  }
  
  return {
    config,
    issues,
    isValid: issues.length === 0
  };
}

/**
 * Log configuration for debugging
 */
export function logConfiguration() {
  const validation = validateConfiguration();
  
  console.group('🔧 FlipSync Configuration');
  console.log('Environment:', validation.config.ENVIRONMENT);
  console.log('API Base URL:', validation.config.API_BASE_URL);
  console.log('WebSocket URL:', validation.config.WS_BASE_URL);
  console.log('OAuth Redirect:', validation.config.OAUTH_REDIRECT_BASE);
  console.log('Use HTTPS:', validation.config.USE_HTTPS);
  console.log('Debug Mode:', validation.config.ENABLE_DEBUG);
  
  if (validation.issues.length > 0) {
    console.group('⚠️ Configuration Issues');
    validation.issues.forEach(issue => {
      console.warn(`${issue.severity}: ${issue.message}`);
      console.log(`Fix: ${issue.fix}`);
    });
    console.groupEnd();
  } else {
    console.log('✅ Configuration is valid');
  }
  
  console.groupEnd();
  
  return validation;
}

// Export default configuration
export default getEnvironmentConfig();
