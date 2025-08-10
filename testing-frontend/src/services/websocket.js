// WebSocket service for FlipSync real-time communication
import { getWebSocketUrl, logConfiguration } from '../config/environment.js';

class WebSocketService {
  constructor() {
    this.socket = null;
    this.listeners = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
    this.reconnectDelay = 1000;
  }

  connect() {
    try {
      // Use working WebSocket endpoint for agent monitoring
      const wsUrl = getWebSocketUrl('/ws/monitoring');

      // Log configuration in development
      if (process.env.NODE_ENV === 'development') {
        logConfiguration();
      }

      console.log('Connecting to WebSocket:', wsUrl);
      this.socket = new WebSocket(wsUrl);
      
      this.socket.onopen = () => {
        console.log('✅ WebSocket connected to FlipSync');
        this.reconnectAttempts = 0;
        this.emit('connected', { status: 'connected' });
        
        // Send authentication if token exists
        const token = localStorage.getItem('flipsync_token');
        if (token) {
          this.send({
            type: 'auth',
            token: token
          });
        }
      };

      this.socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('📥 WebSocket message received:', data);

          // Handle enhanced token lifecycle events
          this.handleTokenLifecycleEvents(data);

          // Emit to specific listeners
          if (data.type) {
            this.emit(data.type, data);
          }

          // Emit to general message listeners
          this.emit('message', data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      this.socket.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
        this.emit('error', error);
      };

      this.socket.onclose = (event) => {
        console.log('🔌 WebSocket disconnected:', event.code, event.reason);
        this.emit('disconnected', { code: event.code, reason: event.reason });
        this.handleReconnect();
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.handleReconnect();
    }
  }

  handleReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);

      console.log(`🔄 Reconnecting in ${delay}ms... (attempt ${this.reconnectAttempts})`);
      setTimeout(() => this.connect(), delay);
    } else {
      console.error('❌ Max reconnection attempts reached');
      this.emit('max_reconnect_attempts', { attempts: this.reconnectAttempts });
    }
  }

  handleTokenLifecycleEvents(data) {
    // Handle enhanced eBay OAuth V2 and Token Lifecycle Management events
    switch (data.type) {
      case 'token_refresh_success':
        console.log('🔄 Token refreshed successfully:', data.data);
        this.emit('token_status_changed', {
          type: 'refresh_success',
          user_id: data.data?.user_id,
          new_expires_at: data.data?.new_expires_at,
          message: 'Token refreshed successfully'
        });
        break;

      case 'token_cleared':
        console.log('🧹 Token cleared:', data.data);
        this.emit('token_status_changed', {
          type: 'token_cleared',
          user_id: data.data?.user_id,
          reason: data.data?.reason,
          message: 'Token cleared - re-authentication required'
        });
        break;

      case 'reauth_required':
        console.log('🔐 Re-authentication required:', data.data);
        this.emit('token_status_changed', {
          type: 'reauth_required',
          user_id: data.data?.user_id,
          message: data.data?.message || 'Re-authentication required'
        });
        break;

      case 'token_refresh_failed':
        console.log('❌ Token refresh failed:', data.data);
        this.emit('token_status_changed', {
          type: 'refresh_failed',
          user_id: data.data?.user_id,
          error: data.data?.error,
          message: 'Token refresh failed'
        });
        break;

      case 'proactive_refresh':
        console.log('⏰ Proactive token refresh:', data.data);
        this.emit('token_status_changed', {
          type: 'proactive_refresh',
          user_id: data.data?.user_id,
          message: 'Token proactively refreshed'
        });
        break;

      default:
        // Handle other events normally
        break;
    }
  }

  send(data) {
    if (this.socket && this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(data));
      console.log('📤 WebSocket message sent:', data);
    } else {
      console.warn('⚠️ WebSocket not connected, message not sent:', data);
    }
  }

  on(event, callback) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, []);
    }
    this.listeners.get(event).push(callback);
  }

  off(event, callback) {
    if (this.listeners.has(event)) {
      const callbacks = this.listeners.get(event);
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  emit(event, data) {
    if (this.listeners.has(event)) {
      this.listeners.get(event).forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in WebSocket event listener for ${event}:`, error);
        }
      });
    }
  }

  disconnect() {
    if (this.socket) {
      this.socket.close();
      this.socket = null;
    }
    this.listeners.clear();
  }

  isConnected() {
    return this.socket && this.socket.readyState === WebSocket.OPEN;
  }
}

const webSocketService = new WebSocketService();
export default webSocketService;
