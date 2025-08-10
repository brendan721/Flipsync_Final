import axios from 'axios';
import { getApiBaseUrl, logConfiguration } from '../config/environment.js';

// FlipSync API Configuration - Environment-based
const API_BASE_URL = getApiBaseUrl();

// Log configuration for debugging
if (process.env.NODE_ENV === 'development') {
  logConfiguration();
}

class FlipSyncAPI {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token (optional for testing)
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('flipsync_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor for error handling (simplified for testing)
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        // Don't redirect on auth errors for testing frontend
        console.warn('API Error:', error.response?.status, error.message);
        return Promise.reject(error);
      }
    );
  }

  // Health & Status (4+1 Architecture)
  async getHealth() {
    const response = await this.client.get('/api/v1/health');
    return response.data;
  }

  // 4+1 Architecture Endpoints (Confirmed Working)
  async get4Plus1Agents() {
    const response = await this.client.get('/api/v1/agents/4plus1/agents/');
    return response.data;
  }

  async get4Plus1Decisions() {
    const response = await this.client.get('/api/v1/decisions/4plus1/decisions/');
    return response.data;
  }

  async getChatAgentStatus() {
    const response = await this.client.get('/api/v1/chat/4plus1/chat/4plus1/agent-status');
    return response.data;
  }

  // Legacy endpoints (may not exist, with fallback)
  async getAgentStatus() {
    try {
      const response = await this.client.get('/api/v1/agents/status');
      return response.data;
    } catch (error) {
      console.warn('Legacy agent status endpoint not available, using 4+1 architecture');
      return await this.get4Plus1Agents();
    }
  }

  async getAIStatus() {
    try {
      const response = await this.client.get('/api/v1/ai/status');
      return response.data;
    } catch (error) {
      console.warn('AI status endpoint not available');
      return { status: 'not_available', error: 'Endpoint not implemented' };
    }
  }

  // eBay Integration (with fallback handling)
  async getEbayStatus() {
    try {
      const response = await this.client.get('/api/v1/ebay/status');
      return response.data;
    } catch (error) {
      console.warn('eBay status endpoint not available');
      return { status: 'not_available', error: 'Endpoint not implemented' };
    }
  }

  // Enhanced eBay OAuth V2 and Token Lifecycle Management
  async getEbayTokenDashboard() {
    try {
      const response = await this.client.get('/api/v1/ebay/tokens/dashboard');
      return response.data;
    } catch (error) {
      console.warn('eBay token dashboard endpoint not available:', error.message);
      throw error;
    }
  }

  async getEbayOAuthStatus(userId = 'testuser') {
    try {
      const response = await this.client.get(`/api/v1/ebay/oauth/status/${userId}`);
      return response.data;
    } catch (error) {
      console.warn('eBay OAuth status endpoint not available:', error.message);
      throw error;
    }
  }

  async refreshEbayToken(userId = 'testuser') {
    try {
      const response = await this.client.post(`/api/v1/ebay/tokens/refresh/${userId}`);
      return response.data;
    } catch (error) {
      console.warn('eBay token refresh endpoint not available:', error.message);
      throw error;
    }
  }

  async getEbayTokenHealth() {
    try {
      const response = await this.client.get('/api/v1/ebay/tokens/health');
      return response.data;
    } catch (error) {
      // This endpoint might not exist, provide fallback
      console.warn('eBay token health endpoint not available, using dashboard data');
      try {
        const dashboard = await this.getEbayTokenDashboard();
        return {
          success: true,
          data: {
            system_status: dashboard.data?.system_status || 'unknown',
            total_tokens: dashboard.data?.summary?.total_active_tokens || 0,
            health_summary: dashboard.data?.summary?.health_distribution || {}
          }
        };
      } catch (fallbackError) {
        throw error; // Throw original error if fallback fails
      }
    }
  }

  async initializeEbayOAuth(options = {}) {
    try {
      const response = await this.client.post('/api/v1/ebay/oauth/authorize', {
        user_id: options.user_id || 'testuser',
        scopes: options.scopes || [
          'https://api.ebay.com/oauth/api_scope/sell.inventory',
          'https://api.ebay.com/oauth/api_scope/sell.account',
          'https://api.ebay.com/oauth/api_scope/sell.fulfillment',
          'https://api.ebay.com/oauth/api_scope/sell.marketing'
        ]
      });
      return response.data;
    } catch (error) {
      console.warn('eBay OAuth V2 endpoint not available:', error.message);
      throw error;
    }
  }

  async getEbayListings() {
    try {
      // Use the correct eBay listings endpoint
      const response = await this.client.get('/api/v1/ebay/listings');
      return response.data;
    } catch (error) {
      console.warn('eBay listings endpoint not available');
      return { listings: [], error: 'Endpoint not implemented' };
    }
  }

  async createEbayListing(listingData) {
    try {
      const response = await this.client.post('/api/v1/ebay/create-listing', listingData);
      return response.data;
    } catch (error) {
      console.warn('eBay create listing endpoint not available');
      return { success: false, error: 'Endpoint not implemented' };
    }
  }

  // Real eBay API Testing Methods
  async getEbayAccount() {
    try {
      // Use the eBay status endpoint since account endpoint doesn't exist
      const response = await this.client.get('/api/v1/ebay/status');
      return response.data;
    } catch (error) {
      console.warn('eBay status endpoint not available:', error.message);
      throw error;
    }
  }

  async getEbayInventory() {
    try {
      // Use the correct marketplace endpoint path
      const response = await this.client.get('/api/v1/marketplace/ebay/inventory');
      return response.data;
    } catch (error) {
      console.warn('eBay inventory endpoint not available:', error.message);
      throw error;
    }
  }

  async getEbaySellerListings() {
    try {
      const response = await this.client.get('/api/v1/ebay/seller/listings');
      return response.data;
    } catch (error) {
      console.warn('eBay seller listings endpoint not available:', error.message);
      throw error;
    }
  }

  async testEbayTradingAPI() {
    try {
      const response = await this.client.get('/api/v1/ebay/trading/test');
      return response.data;
    } catch (error) {
      console.warn('eBay Trading API test endpoint not available:', error.message);
      throw error;
    }
  }

  // Authentication (Optional for testing)
  async login(credentials) {
    try {
      const response = await this.client.post('/api/v1/auth/login', credentials);
      if (response.data.access_token) {
        localStorage.setItem('flipsync_token', response.data.access_token);
      }
      return response.data;
    } catch (error) {
      console.warn('Login endpoint not available:', error.message);
      return { success: false, error: 'Authentication not implemented' };
    }
  }

  async register(userData) {
    try {
      const response = await this.client.post('/api/v1/auth/register', userData);
      if (response.data.access_token) {
        localStorage.setItem('flipsync_token', response.data.access_token);
      }
      return response.data;
    } catch (error) {
      console.warn('Register endpoint not available:', error.message);
      return { success: false, error: 'Authentication not implemented' };
    }
  }

  async validateToken() {
    try {
      const response = await this.client.get('/api/v1/auth/validate-token');
      return response.data;
    } catch (error) {
      console.warn('Token validation endpoint not available:', error.message);
      return { valid: false, error: 'Authentication not implemented' };
    }
  }

  // 4+1 Architecture System Status
  async getSystemStatus() {
    try {
      const [health, agents, decisions, chatStatus] = await Promise.allSettled([
        this.getHealth(),
        this.get4Plus1Agents(),
        this.get4Plus1Decisions(),
        this.getChatAgentStatus(),
      ]);

      return {
        health: health.status === 'fulfilled' ? health.value : { status: 'error', error: health.reason?.message },
        agents: agents.status === 'fulfilled' ? agents.value : { status: 'error', error: agents.reason?.message },
        decisions: decisions.status === 'fulfilled' ? decisions.value : { status: 'error', error: decisions.reason?.message },
        chat: chatStatus.status === 'fulfilled' ? chatStatus.value : { status: 'error', error: chatStatus.reason?.message },
        timestamp: new Date().toISOString(),
      };
    } catch (error) {
      throw new Error(`Failed to get system status: ${error.message}`);
    }
  }

  // Agent Testing (4+1 Architecture)
  async triggerAgent(agentType, payload = {}) {
    try {
      const response = await this.client.post(`/api/v1/agents/${agentType}/trigger`, payload);
      return response.data;
    } catch (error) {
      console.warn(`Agent trigger endpoint not available for ${agentType}`);
      return { success: false, error: 'Agent trigger not implemented' };
    }
  }

  // Product Creation Pipeline
  async analyzeProduct(productData) {
    const response = await this.client.post('/api/v1/ai/analyze-product', productData);
    return response.data;
  }

  async generateListing(productData) {
    const response = await this.client.post('/api/v1/ai/generate-listing', productData);
    return response.data;
  }

  // Monitoring
  async getSystemMetrics() {
    const response = await this.client.get('/api/v1/monitoring/status');
    return response.data;
  }
}

const flipSyncAPI = new FlipSyncAPI();
export default flipSyncAPI;
