// WebSocket service for FlipSync real-time communication

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
      // Use WebSocket directly for FlipSync backend
      // Use relative URL in development, absolute in production
      const wsUrl = process.env.NODE_ENV === 'development'
        ? 'ws://localhost:3000/ws/flipsync'
        : 'ws://174.138.77.110:8000/ws/flipsync';
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
