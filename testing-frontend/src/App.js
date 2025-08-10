import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

import Dashboard from './components/Dashboard';
import Login from './components/Login';
import EbayOAuthCallback from './components/EbayOAuthCallback';
import ConfigurationValidator from './components/ConfigurationValidator';
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
        if (response.valid !== false) {
          setIsAuthenticated(true);
          setUser(response.user || { name: 'Test User' });
        } else {
          // Token invalid, clear it and require login
          localStorage.removeItem('flipsync_token');
          setIsAuthenticated(false);
          setUser(null);
        }
      } catch (error) {
        console.warn('Token validation failed:', error.message);
        // For testing, try to auto-login with test credentials
        try {
          const loginResponse = await api.login({
            email: 'test@example.com',
            password: 'SecurePassword!'
          });
          if (loginResponse.access_token) {
            setIsAuthenticated(true);
            setUser(loginResponse.user || { name: 'Test User', email: 'test@example.com' });
          } else {
            setIsAuthenticated(false);
            setUser(null);
          }
        } catch (loginError) {
          console.warn('Auto-login failed:', loginError.message);
          setIsAuthenticated(false);
          setUser(null);
        }
      }
    } else {
      // No token, try auto-login for testing
      try {
        const loginResponse = await api.login({
          email: 'test@example.com',
          password: 'SecurePassword!'
        });
        if (loginResponse.access_token) {
          setIsAuthenticated(true);
          setUser(loginResponse.user || { name: 'Test User', email: 'test@example.com' });
        } else {
          setIsAuthenticated(false);
          setUser(null);
        }
      } catch (error) {
        console.warn('Auto-login failed:', error.message);
        setIsAuthenticated(false);
        setUser(null);
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
    <Router basename="/testing-frontend" future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
      <div className="App">
        {/* Configuration Validator - Always visible for debugging */}
        <div className="fixed top-4 right-4 z-50 max-w-md">
          <ConfigurationValidator />
        </div>

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
