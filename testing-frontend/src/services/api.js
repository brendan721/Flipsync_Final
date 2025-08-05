import axios from 'axios';

// FlipSync API Configuration
// Use relative URLs in development to leverage proxy, absolute in production
const API_BASE_URL = process.env.NODE_ENV === 'development' ? '' : 'http://174.138.77.110:8000';

class FlipSyncAPI {
  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
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

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          localStorage.removeItem('flipsync_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Health & Status
  async getHealth() {
    const response = await this.client.get('/api/v1/health');
    return response.data;
  }

  async getAgentStatus() {
    const response = await this.client.get('/api/v1/agents/status');
    return response.data;
  }

  async getAIStatus() {
    const response = await this.client.get('/api/v1/ai/status');
    return response.data;
  }

  // eBay Integration
  async getEbayStatus() {
    const response = await this.client.get('/api/v1/ebay/status');
    return response.data;
  }

  async initializeEbayOAuth() {
    const response = await this.client.post('/api/v1/marketplace/ebay/oauth/authorize');
    return response.data;
  }

  async getEbayListings() {
    const response = await this.client.get('/api/v1/ebay/listings');
    return response.data;
  }

  async createEbayListing(listingData) {
    const response = await this.client.post('/api/v1/ebay/create-listing', listingData);
    return response.data;
  }

  // Authentication
  async login(credentials) {
    const response = await this.client.post('/api/v1/auth/login', credentials);
    if (response.data.access_token) {
      localStorage.setItem('flipsync_token', response.data.access_token);
    }
    return response.data;
  }

  async register(userData) {
    const response = await this.client.post('/api/v1/auth/register', userData);
    if (response.data.access_token) {
      localStorage.setItem('flipsync_token', response.data.access_token);
    }
    return response.data;
  }

  async validateToken() {
    const response = await this.client.get('/api/v1/auth/validate-token');
    return response.data;
  }

  // Agent Testing
  async triggerAgent(agentType, payload = {}) {
    const response = await this.client.post(`/api/v1/agents/${agentType}/trigger`, payload);
    return response.data;
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
