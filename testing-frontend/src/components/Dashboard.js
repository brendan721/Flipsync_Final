import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import {
  Activity,
  Settings,
  LogOut,
  Wifi,
  WifiOff,
  RefreshCw,
  CheckCircle,
  AlertCircle,
  Clock,
  Zap,
  GitBranch,
  BarChart3,
  Shield
} from 'lucide-react';

import SystemStatus from './SystemStatus';
import EbayOAuthTester from './EbayOAuthTester';
import AgentTester from './AgentTester';
import WebSocketTester from './WebSocketTester';
import ProductPipelineTester from './ProductPipelineTester';
import AdvancedAgentTester from './AdvancedAgentTester';
import WorkflowSimulator from './WorkflowSimulator';
import AnalyticsDashboard from './AnalyticsDashboard';
import ProductionTester from './ProductionTester';

import api from '../services/api';
import websocket from '../services/websocket';

const Dashboard = ({ user, onLogout }) => {
  const [activeTab, setActiveTab] = useState('system');
  const [systemHealth, setSystemHealth] = useState(null);
  const [wsConnected, setWsConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  useEffect(() => {
    loadSystemHealth();
    setupWebSocketListeners();
    
    // Refresh system health every 30 seconds
    const interval = setInterval(loadSystemHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadSystemHealth = async () => {
    try {
      const health = await api.getHealth();
      setSystemHealth(health);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to load system health:', error);
      toast.error('Failed to load system health');
    }
  };

  const setupWebSocketListeners = () => {
    websocket.on('connected', () => {
      setWsConnected(true);
      toast.success('WebSocket connected');
    });

    websocket.on('disconnected', () => {
      setWsConnected(false);
      toast.warning('WebSocket disconnected');
    });

    websocket.on('error', () => {
      setWsConnected(false);
    });
  };

  const tabs = [
    { id: 'system', label: 'System Status', icon: Activity },
    { id: 'agents', label: 'Agent Testing', icon: RefreshCw },
    { id: 'advanced-agents', label: 'Advanced Testing', icon: Zap },
    { id: 'workflows', label: 'Workflow Simulator', icon: GitBranch },
    { id: 'analytics', label: 'Analytics', icon: BarChart3 },
    { id: 'production', label: 'Production Testing', icon: Shield },
    { id: 'websocket', label: 'WebSocket', icon: Wifi },
    { id: 'ebay', label: 'eBay OAuth', icon: Settings },
    { id: 'pipeline', label: 'Product Pipeline', icon: CheckCircle }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'system':
        return <SystemStatus />;
      case 'agents':
        return <AgentTester />;
      case 'advanced-agents':
        return <AdvancedAgentTester />;
      case 'workflows':
        return <WorkflowSimulator />;
      case 'analytics':
        return <AnalyticsDashboard />;
      case 'production':
        return <ProductionTester />;
      case 'websocket':
        return <WebSocketTester />;
      case 'ebay':
        return <EbayOAuthTester />;
      case 'pipeline':
        return <ProductPipelineTester />;
      default:
        return <SystemStatus />;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <h1 className="text-2xl font-bold text-flipsync-900">FlipSync</h1>
              <span className="ml-2 text-sm text-gray-500">Testing Dashboard</span>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* WebSocket Status */}
              <div className="flex items-center space-x-2">
                {wsConnected ? (
                  <Wifi className="w-4 h-4 text-green-500" />
                ) : (
                  <WifiOff className="w-4 h-4 text-red-500" />
                )}
                <span className="text-sm text-gray-600">
                  {wsConnected ? 'Connected' : 'Disconnected'}
                </span>
              </div>

              {/* System Health */}
              <div className="flex items-center space-x-2">
                {systemHealth?.status === 'ok' ? (
                  <CheckCircle className="w-4 h-4 text-green-500" />
                ) : (
                  <AlertCircle className="w-4 h-4 text-red-500" />
                )}
                <span className="text-sm text-gray-600">
                  {systemHealth?.status || 'Unknown'}
                </span>
              </div>

              {/* Last Update */}
              <div className="flex items-center space-x-2 text-sm text-gray-500">
                <Clock className="w-4 h-4" />
                <span>{lastUpdate.toLocaleTimeString()}</span>
              </div>

              {/* User Menu */}
              <div className="flex items-center space-x-3">
                <span className="text-sm text-gray-700">
                  {user?.username || user?.email}
                </span>
                <button
                  onClick={onLogout}
                  className="flex items-center space-x-1 text-sm text-gray-600 hover:text-gray-900"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-flipsync-500 text-flipsync-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        {renderTabContent()}
      </main>
    </div>
  );
};

export default Dashboard;
