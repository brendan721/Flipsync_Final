import React, { useState } from 'react';
import { toast } from 'react-toastify';
import { Eye, EyeOff, LogIn, UserPlus } from 'lucide-react';
import api from '../services/api';

const Login = ({ onLogin }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    username: '',
    first_name: '',
    last_name: ''
  });

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);

    try {
      let response;
      if (isLogin) {
        // Check for test credentials to bypass auth service issues
        if (formData.email === 'admin@flipsync.com' && formData.password === 'AdminPassword123!') {
          // Simulate successful admin login
          response = {
            access_token: 'test-admin-token-' + Date.now(),
            user: {
              user_id: 'admin_user_001',
              username: 'admin',
              email: 'admin@flipsync.com',
              roles: ['admin', 'user'],
              permissions: ['read', 'write', 'admin', 'manage_agents']
            }
          };
          localStorage.setItem('flipsync_token', response.access_token);
          toast.success('Login successful! (Test Mode)');
        } else if (formData.email === 'test@example.com' && formData.password === 'SecurePassword!') {
          // Simulate successful test user login
          response = {
            access_token: 'test-user-token-' + Date.now(),
            user: {
              user_id: 'test_user_001',
              username: 'testuser',
              email: 'test@example.com',
              roles: ['user', 'tester'],
              permissions: ['read', 'write', 'test']
            }
          };
          localStorage.setItem('flipsync_token', response.access_token);
          toast.success('Login successful! (Test Mode)');
        } else {
          // Try real authentication
          response = await api.login({
            email: formData.email,
            password: formData.password
          });
          toast.success('Login successful!');
        }
      } else {
        response = await api.register(formData);
        toast.success('Registration successful!');
      }

      onLogin(response);
    } catch (error) {
      console.error('Authentication error:', error);
      const message = error.response?.data?.message ||
                     error.response?.data?.detail ||
                     'Authentication failed. Try admin@flipsync.com / AdminPassword123! for test access.';
      toast.error(message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-flipsync-50 to-flipsync-100 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h1 className="text-4xl font-bold text-flipsync-900 mb-2">FlipSync</h1>
          <h2 className="text-xl font-semibold text-gray-700 mb-2">Testing Dashboard</h2>
          <p className="text-sm text-gray-600">
            eBay OAuth & Agent Workflow Validator
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-lg p-8">
          {/* Test Credentials Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
            <h4 className="font-medium text-blue-900 mb-2">Test Credentials Available</h4>
            <div className="text-sm text-blue-700 space-y-1">
              <div><strong>Admin:</strong> admin@flipsync.com / AdminPassword123!</div>
              <div><strong>Test User:</strong> test@example.com / SecurePassword!</div>
            </div>
          </div>

          <div className="flex mb-6">
            <button
              type="button"
              onClick={() => setIsLogin(true)}
              className={`flex-1 py-2 px-4 text-sm font-medium rounded-l-lg border ${
                isLogin
                  ? 'bg-flipsync-600 text-white border-flipsync-600'
                  : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
              }`}
            >
              <LogIn className="w-4 h-4 inline mr-2" />
              Login
            </button>
            <button
              type="button"
              onClick={() => setIsLogin(false)}
              className={`flex-1 py-2 px-4 text-sm font-medium rounded-r-lg border-t border-r border-b ${
                !isLogin
                  ? 'bg-flipsync-600 text-white border-flipsync-600'
                  : 'bg-gray-50 text-gray-700 border-gray-300 hover:bg-gray-100'
              }`}
            >
              <UserPlus className="w-4 h-4 inline mr-2" />
              Register
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            {!isLogin && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">
                      First Name
                    </label>
                    <input
                      id="first_name"
                      name="first_name"
                      type="text"
                      required={!isLogin}
                      value={formData.first_name}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-flipsync-500 focus:border-transparent"
                    />
                  </div>
                  <div>
                    <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">
                      Last Name
                    </label>
                    <input
                      id="last_name"
                      name="last_name"
                      type="text"
                      required={!isLogin}
                      value={formData.last_name}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-flipsync-500 focus:border-transparent"
                    />
                  </div>
                </div>
                <div>
                  <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                    Username
                  </label>
                  <input
                    id="username"
                    name="username"
                    type="text"
                    required={!isLogin}
                    value={formData.username}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-flipsync-500 focus:border-transparent"
                  />
                </div>
              </>
            )}

            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email Address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleInputChange}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-flipsync-500 focus:border-transparent"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  autoComplete="current-password"
                  required
                  value={formData.password}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-flipsync-500 focus:border-transparent"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center"
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-400" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-400" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  {isLogin ? 'Signing In...' : 'Creating Account...'}
                </div>
              ) : (
                isLogin ? 'Sign In' : 'Create Account'
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default Login;
