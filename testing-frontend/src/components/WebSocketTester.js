import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import {
  Wifi,
  WifiOff,
  Send,
  Trash2,
  RefreshCw,
  MessageCircle,
  Activity,
  XCircle
} from 'lucide-react';
import ReactJsonView from '@microlink/react-json-view';
import websocket from '../services/websocket';

const WebSocketTester = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState([]);
  const [testMessage, setTestMessage] = useState('');
  const [connectionInfo, setConnectionInfo] = useState(null);
  const [stats, setStats] = useState({
    messagesSent: 0,
    messagesReceived: 0,
    connectionTime: null,
    lastPing: null
  });

  useEffect(() => {
    setupWebSocketListeners();
    checkConnection();

    // Ping every 30 seconds to test connection
    const pingInterval = setInterval(sendPing, 30000);

    return () => {
      clearInterval(pingInterval);
    };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const setupWebSocketListeners = () => {
    websocket.on('connected', (data) => {
      setIsConnected(true);
      setConnectionInfo(data);
      setStats(prev => ({ ...prev, connectionTime: new Date() }));
      addMessage('system', 'WebSocket connected', data);
      toast.success('WebSocket connected');
    });

    websocket.on('disconnected', (data) => {
      setIsConnected(false);
      setConnectionInfo(null);
      addMessage('system', 'WebSocket disconnected', data);
      toast.warning('WebSocket disconnected');
    });

    websocket.on('error', (error) => {
      addMessage('error', 'WebSocket error', error);
      toast.error('WebSocket error');
    });

    websocket.on('message', (data) => {
      setStats(prev => ({ ...prev, messagesReceived: prev.messagesReceived + 1 }));
      addMessage('received', 'Message received', data);
    });

    websocket.on('connection_established', (data) => {
      setConnectionInfo(data);
      addMessage('system', 'Connection established', data);
    });

    websocket.on('ping_pong', (data) => {
      setStats(prev => ({ ...prev, lastPing: new Date() }));
      addMessage('ping', 'Ping response', data);
    });
  };

  const checkConnection = () => {
    setIsConnected(websocket.isConnected());
  };

  const addMessage = (type, title, data) => {
    const message = {
      id: Date.now() + Math.random(),
      timestamp: new Date(),
      type,
      title,
      data
    };
    setMessages(prev => [message, ...prev].slice(0, 100)); // Keep last 100 messages
  };

  const connect = () => {
    websocket.connect();
    toast.info('Connecting to WebSocket...');
  };

  const disconnect = () => {
    websocket.disconnect();
    setIsConnected(false);
    setConnectionInfo(null);
    toast.info('Disconnected from WebSocket');
  };

  const sendTestMessage = () => {
    if (!testMessage.trim()) {
      toast.warning('Please enter a test message');
      return;
    }

    try {
      const messageData = {
        type: 'test_message',
        message: testMessage,
        timestamp: new Date().toISOString()
      };

      websocket.send(messageData);
      setStats(prev => ({ ...prev, messagesSent: prev.messagesSent + 1 }));
      addMessage('sent', 'Test message sent', messageData);
      setTestMessage('');
      toast.success('Test message sent');
    } catch (error) {
      toast.error('Failed to send message');
    }
  };

  const sendPing = () => {
    if (isConnected) {
      const pingData = {
        type: 'ping',
        timestamp: new Date().toISOString()
      };
      websocket.send(pingData);
      addMessage('ping', 'Ping sent', pingData);
    }
  };

  const clearMessages = () => {
    setMessages([]);
    setStats({
      messagesSent: 0,
      messagesReceived: 0,
      connectionTime: stats.connectionTime,
      lastPing: null
    });
  };

  const getMessageIcon = (type) => {
    switch (type) {
      case 'sent':
        return <Send className="w-4 h-4 text-blue-500" />;
      case 'received':
        return <MessageCircle className="w-4 h-4 text-green-500" />;
      case 'system':
        return <Activity className="w-4 h-4 text-purple-500" />;
      case 'ping':
        return <RefreshCw className="w-4 h-4 text-orange-500" />;
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <MessageCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">WebSocket Testing</h2>
          <p className="text-gray-600 mt-1">
            Test real-time communication with FlipSync backend
          </p>
        </div>
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-2">
            {isConnected ? (
              <Wifi className="w-5 h-5 text-green-500" />
            ) : (
              <WifiOff className="w-5 h-5 text-red-500" />
            )}
            <span className={`text-sm font-medium ${
              isConnected ? 'text-green-600' : 'text-red-600'
            }`}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>
          {isConnected ? (
            <button onClick={disconnect} className="btn-secondary">
              Disconnect
            </button>
          ) : (
            <button onClick={connect} className="btn-primary">
              Connect
            </button>
          )}
        </div>
      </div>

      {/* Connection Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card text-center">
          <div className="text-2xl font-bold text-blue-600">{stats.messagesSent}</div>
          <div className="text-sm text-gray-600">Messages Sent</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-green-600">{stats.messagesReceived}</div>
          <div className="text-sm text-gray-600">Messages Received</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-purple-600">
            {stats.connectionTime ? 
              Math.floor((new Date() - stats.connectionTime) / 1000) + 's' : 
              'N/A'
            }
          </div>
          <div className="text-sm text-gray-600">Connected Time</div>
        </div>
        <div className="card text-center">
          <div className="text-2xl font-bold text-orange-600">
            {stats.lastPing ? 
              Math.floor((new Date() - stats.lastPing) / 1000) + 's ago' : 
              'N/A'
            }
          </div>
          <div className="text-sm text-gray-600">Last Ping</div>
        </div>
      </div>

      {/* Connection Info */}
      {connectionInfo && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Connection Information</h3>
          <ReactJsonView
            src={connectionInfo}
            theme="rjv-default"
            collapsed={false}
            displayDataTypes={false}
            displayObjectSize={false}
            enableClipboard={true}
            name="connection_info"
          />
        </div>
      )}

      {/* Message Testing */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Send Test Message</h3>
        <div className="flex space-x-3">
          <input
            type="text"
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && sendTestMessage()}
            placeholder="Enter test message..."
            className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-flipsync-500"
            disabled={!isConnected}
          />
          <button
            onClick={sendTestMessage}
            disabled={!isConnected || !testMessage.trim()}
            className="btn-primary disabled:opacity-50"
          >
            <Send className="w-4 h-4 mr-2" />
            Send
          </button>
          <button
            onClick={sendPing}
            disabled={!isConnected}
            className="btn-secondary disabled:opacity-50"
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Ping
          </button>
        </div>
      </div>

      {/* Message Log */}
      <div className="card">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Message Log</h3>
          <button
            onClick={clearMessages}
            className="btn-secondary"
          >
            <Trash2 className="w-4 h-4 mr-2" />
            Clear
          </button>
        </div>
        
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {messages.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              No messages yet. Connect and send a test message to get started.
            </div>
          ) : (
            messages.map((message) => (
              <div key={message.id} className="bg-gray-50 rounded-lg p-3">
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    {getMessageIcon(message.type)}
                    <span className="font-medium text-gray-900">{message.title}</span>
                  </div>
                  <span className="text-xs text-gray-500">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>
                {message.data && (
                  <ReactJsonView
                    src={message.data}
                    theme="rjv-default"
                    collapsed={1}
                    displayDataTypes={false}
                    displayObjectSize={false}
                    enableClipboard={false}
                    name={false}
                  />
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default WebSocketTester;
