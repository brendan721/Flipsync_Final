import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Dashboard from './components/Dashboard';
import Login from './components/Login';
import EbayOAuthCallback from './components/EbayOAuthCallback';
import api from './services/api';
import websocket from './services/websocket';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [user, setUser] = useState(null);

  useEffect(() => {
    checkAuthentication();
    initializeWebSocket();
  }, []);

  const checkAuthentication = async () => {
    const token = localStorage.getItem('flipsync_token');
    if (token) {
      try {
        const response = await api.validateToken();
        setIsAuthenticated(true);
        setUser(response.user);
      } catch (error) {
        console.error('Token validation failed:', error);
        localStorage.removeItem('flipsync_token');
        setIsAuthenticated(false);
      }
    }
    setIsLoading(false);
  };

  const initializeWebSocket = () => {
    websocket.connect();
    
    websocket.on('connected', () => {
      console.log('WebSocket connected successfully');
    });

    websocket.on('error', (error) => {
      console.error('WebSocket connection error:', error);
    });
  };

  const handleLogin = (userData) => {
    setIsAuthenticated(true);
    setUser(userData.user);
  };

  const handleLogout = () => {
    localStorage.removeItem('flipsync_token');
    setIsAuthenticated(false);
    setUser(null);
    websocket.disconnect();
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-flipsync-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading FlipSync Testing Dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <Router future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="App">
        <Routes>
          <Route 
            path="/login" 
            element={
              isAuthenticated ? 
              <Navigate to="/" replace /> : 
              <Login onLogin={handleLogin} />
            } 
          />
          <Route 
            path="/ebay-oauth-callback" 
            element={<EbayOAuthCallback />} 
          />
          <Route 
            path="/" 
            element={
              isAuthenticated ? 
              <Dashboard user={user} onLogout={handleLogout} /> : 
              <Navigate to="/login" replace />
            } 
          />
        </Routes>
        
        <ToastContainer
          position="top-right"
          autoClose={5000}
          hideProgressBar={false}
          newestOnTop={false}
          closeOnClick
          rtl={false}
          pauseOnFocusLoss
          draggable
          pauseOnHover
          theme="light"
        />
      </div>
    </Router>
  );
}

export default App;
