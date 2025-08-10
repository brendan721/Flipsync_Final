import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { 
  Activity, 
  Database, 
  Cpu, 
  Globe, 
  RefreshCw,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock
} from 'lucide-react';
import ReactJsonView from '@microlink/react-json-view';
import api from '../services/api';

const SystemStatus = () => {
  const [systemData, setSystemData] = useState({
    health: null,
    agents: null,
    aiStatus: null,
    ebayStatus: null
  });
  const [isLoading, setIsLoading] = useState(false);
  const [lastUpdate, setLastUpdate] = useState(null);

  useEffect(() => {
    loadSystemData();
    
    // Auto-refresh every 30 seconds
    const interval = setInterval(loadSystemData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadSystemData = async () => {
    setIsLoading(true);
    try {
      // Use the new 4+1 architecture system status method
      const systemStatus = await api.getSystemStatus();

      setSystemData({
        health: systemStatus.health,
        agents: systemStatus.agents,
        decisions: systemStatus.decisions,
        chat: systemStatus.chat,
        // Keep legacy fields for compatibility
        aiStatus: systemStatus.chat || { status: 'not_available' },
        ebayStatus: { status: 'not_available', message: 'eBay integration testing' }
      });

      setLastUpdate(new Date());
      toast.success('4+1 Architecture status updated');
    } catch (error) {
      console.error('Failed to load system data:', error);
      toast.error('Failed to load system status');

      // Set error state
      setSystemData({
        health: { error: error.message },
        agents: { error: 'Failed to fetch' },
        decisions: { error: 'Failed to fetch' },
        chat: { error: 'Failed to fetch' },
        aiStatus: { error: 'Failed to fetch' },
        ebayStatus: { error: 'Failed to fetch' }
      });
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusIcon = (status, hasError = false) => {
    if (hasError) return <XCircle className="w-5 h-5 text-red-500" />;
    if (status === 'ok' || status === 'running' || status === 'operational') {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    }
    return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
  };

  const StatusCard = ({ title, icon: Icon, data, status, error }) => (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center">
          <Icon className="w-6 h-6 text-flipsync-600 mr-3" />
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        {getStatusIcon(status, !!error)}
      </div>
      
      {error ? (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800 text-sm">Error: {error}</p>
        </div>
      ) : data ? (
        <ReactJsonView
          src={data}
          theme="rjv-default"
          collapsed={2}
          displayDataTypes={false}
          displayObjectSize={false}
          enableClipboard={true}
          name={title.toLowerCase().replace(' ', '_')}
        />
      ) : (
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">System Status</h2>
          <p className="text-gray-600 mt-1">
            Real-time monitoring of FlipSync backend services
          </p>
        </div>
        <div className="flex items-center space-x-4">
          {lastUpdate && (
            <div className="flex items-center text-sm text-gray-500">
              <Clock className="w-4 h-4 mr-1" />
              Last updated: {lastUpdate.toLocaleTimeString()}
            </div>
          )}
          <button
            onClick={loadSystemData}
            disabled={isLoading}
            className="btn-secondary disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* System Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <Activity className="w-8 h-8 text-green-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">System Health</p>
              <p className="text-lg font-semibold text-gray-900">
                {systemData.health?.status || 'Loading...'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <Cpu className="w-8 h-8 text-blue-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">4+1 Agents</p>
              <p className="text-lg font-semibold text-gray-900">
                {systemData.agents?.total_agents || '0'} Total
              </p>
              <p className="text-xs text-gray-500">
                {systemData.agents?.autonomous_agents || '0'} Autonomous + {systemData.agents?.conversational_interfaces || '0'} Chat
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <Database className="w-8 h-8 text-purple-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Decisions</p>
              <p className="text-lg font-semibold text-gray-900">
                {systemData.decisions?.total_decisions || '0'} Total
              </p>
              <p className="text-xs text-gray-500">
                {systemData.decisions?.compliance_metrics?.compliant_decisions || '0'} Compliant
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <div className="flex items-center">
            <Globe className="w-8 h-8 text-orange-500 mr-3" />
            <div>
              <p className="text-sm font-medium text-gray-600">Chat Interface</p>
              <p className="text-lg font-semibold text-gray-900">
                {systemData.chat?.success ? 'Active' : 'Inactive'}
              </p>
              <p className="text-xs text-gray-500">
                {systemData.chat?.summary?.active_agents || '0'} Active Agents
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Detailed Status Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <StatusCard
          title="System Health"
          icon={Activity}
          data={systemData.health}
          status={systemData.health?.status}
          error={systemData.health?.error}
        />

        <StatusCard
          title="4+1 Agents"
          icon={Cpu}
          data={systemData.agents}
          status={systemData.agents?.status}
          error={systemData.agents?.error}
        />

        <StatusCard
          title="Agent Decisions"
          icon={Database}
          data={systemData.decisions}
          status={systemData.decisions?.status || 'operational'}
          error={systemData.decisions?.error}
        />

        <StatusCard
          title="Chat Interface"
          icon={Globe}
          data={systemData.chat}
          status={systemData.chat?.success ? 'operational' : 'error'}
          error={systemData.ebayStatus?.error}
        />
      </div>
    </div>
  );
};

export default SystemStatus;
