import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { 
  Play, 
  RefreshCw, 
  TrendingUp, 
  FileText, 
  Settings, 
  Truck,
  MessageSquare,
  CheckCircle,
  XCircle,
  Clock
} from 'lucide-react';
import ReactJsonView from '@microlink/react-json-view';
import api from '../services/api';
import websocket from '../services/websocket';

const AgentTester = () => {
  const [agents, setAgents] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [testResults, setTestResults] = useState({});
  const [agentLogs, setAgentLogs] = useState([]);

  const agentConfigs = [
    {
      id: 'market_autonomous_agent',
      name: 'Market Agent',
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      description: 'Market analysis and pricing optimization',
      testPayload: {
        action: 'analyze_market',
        product_category: 'electronics',
        competitor_data: true
      }
    },
    {
      id: 'content_autonomous_agent',
      name: 'Content Agent',
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      description: 'Content generation and SEO optimization',
      testPayload: {
        action: 'optimize_content',
        product_title: 'Test Product',
        generate_seo: true
      }
    },
    {
      id: 'executive_autonomous_agent',
      name: 'Executive Agent',
      icon: Settings,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      description: 'Strategic planning and coordination',
      testPayload: {
        action: 'strategic_analysis',
        coordination_required: true
      }
    },
    {
      id: 'logistics_autonomous_agent',
      name: 'Logistics Agent',
      icon: Truck,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      description: 'Inventory and shipping optimization',
      testPayload: {
        action: 'optimize_shipping',
        calculate_zones: true
      }
    },
    {
      id: 'strategic_chat_service',
      name: 'Strategic Chat',
      icon: MessageSquare,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      description: 'Conversational interface with Gemini',
      testPayload: {
        action: 'chat_response',
        message: 'Test collaboration workflow'
      }
    }
  ];

  useEffect(() => {
    loadAgentStatus();
    setupWebSocketListeners();
  }, []);

  const setupWebSocketListeners = () => {
    websocket.on('agent_status_update', (data) => {
      console.log('Agent status update:', data);
      setAgentLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        type: 'status_update',
        data: data
      }]);
    });

    websocket.on('agent_decision', (data) => {
      console.log('Agent decision:', data);
      setAgentLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        type: 'decision',
        data: data
      }]);
    });
  };

  const loadAgentStatus = async () => {
    setIsLoading(true);
    try {
      const response = await api.getAgentStatus();
      setAgents(response.agents || []);
      toast.success('Agent status loaded');
    } catch (error) {
      console.error('Failed to load agent status:', error);
      toast.error('Failed to load agent status');
    } finally {
      setIsLoading(false);
    }
  };

  const triggerAgent = async (agentConfig) => {
    setIsLoading(true);
    try {
      const startTime = Date.now();
      
      // Try to trigger the agent
      const response = await api.triggerAgent(agentConfig.id, agentConfig.testPayload);
      
      const endTime = Date.now();
      const responseTime = endTime - startTime;

      setTestResults(prev => ({
        ...prev,
        [agentConfig.id]: {
          success: true,
          response: response,
          responseTime: responseTime,
          timestamp: new Date().toISOString()
        }
      }));

      toast.success(`${agentConfig.name} triggered successfully (${responseTime}ms)`);
      
      // Add to logs
      setAgentLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        type: 'trigger',
        agent: agentConfig.name,
        responseTime: responseTime,
        success: true
      }]);

    } catch (error) {
      console.error(`Failed to trigger ${agentConfig.name}:`, error);
      
      setTestResults(prev => ({
        ...prev,
        [agentConfig.id]: {
          success: false,
          error: error.message,
          timestamp: new Date().toISOString()
        }
      }));

      // For 404 errors, this might be expected as the trigger endpoints may not be implemented yet
      if (error.response?.status === 404) {
        toast.warning(`${agentConfig.name} trigger endpoint not implemented yet`);
      } else {
        toast.error(`Failed to trigger ${agentConfig.name}`);
      }

      // Add to logs
      setAgentLogs(prev => [...prev, {
        timestamp: new Date().toISOString(),
        type: 'trigger',
        agent: agentConfig.name,
        success: false,
        error: error.message
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const triggerAllAgents = async () => {
    for (const agentConfig of agentConfigs) {
      await triggerAgent(agentConfig);
      // Small delay between triggers
      await new Promise(resolve => setTimeout(resolve, 500));
    }
  };

  const clearLogs = () => {
    setAgentLogs([]);
    setTestResults({});
  };

  const getAgentStatus = (agentId) => {
    const agent = agents.find(a => a.id === agentId || a.agent_id === agentId);
    return agent?.status || 'unknown';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'running':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'stopped':
      case 'error':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Agent Testing</h2>
          <p className="text-gray-600 mt-1">
            Test individual agents and monitor real-time coordination
          </p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={clearLogs}
            className="btn-secondary"
          >
            Clear Logs
          </button>
          <button
            onClick={loadAgentStatus}
            disabled={isLoading}
            className="btn-secondary disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
          <button
            onClick={triggerAllAgents}
            disabled={isLoading}
            className="btn-primary disabled:opacity-50"
          >
            <Play className="w-4 h-4 mr-2" />
            Test All Agents
          </button>
        </div>
      </div>

      {/* Agent Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {agentConfigs.map((agentConfig) => {
          const Icon = agentConfig.icon;
          const status = getAgentStatus(agentConfig.id);
          const testResult = testResults[agentConfig.id];
          
          return (
            <div key={agentConfig.id} className="card">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center">
                  <div className={`p-2 rounded-lg ${agentConfig.bgColor} mr-3`}>
                    <Icon className={`w-5 h-5 ${agentConfig.color}`} />
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{agentConfig.name}</h3>
                    <p className="text-sm text-gray-600">{agentConfig.description}</p>
                  </div>
                </div>
                {getStatusIcon(status)}
              </div>

              <div className="space-y-3">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-600">Status:</span>
                  <span className={`font-medium ${
                    status === 'running' ? 'text-green-600' : 
                    status === 'error' ? 'text-red-600' : 'text-yellow-600'
                  }`}>
                    {status}
                  </span>
                </div>

                {testResult && (
                  <div className="text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Last Test:</span>
                      <span className={`font-medium ${
                        testResult.success ? 'text-green-600' : 'text-red-600'
                      }`}>
                        {testResult.success ? 'Success' : 'Failed'}
                      </span>
                    </div>
                    {testResult.responseTime && (
                      <div className="flex justify-between">
                        <span className="text-gray-600">Response Time:</span>
                        <span className="font-medium text-blue-600">
                          {testResult.responseTime}ms
                        </span>
                      </div>
                    )}
                  </div>
                )}

                <button
                  onClick={() => triggerAgent(agentConfig)}
                  disabled={isLoading}
                  className="w-full btn-primary disabled:opacity-50"
                >
                  <Play className="w-4 h-4 mr-2" />
                  Test Agent
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* Test Results */}
      {Object.keys(testResults).length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Results</h3>
          <ReactJsonView
            src={testResults}
            theme="rjv-default"
            collapsed={1}
            displayDataTypes={false}
            displayObjectSize={false}
            enableClipboard={true}
            name="agent_test_results"
          />
        </div>
      )}

      {/* Real-time Logs */}
      {agentLogs.length > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Real-time Agent Logs</h3>
          <div className="space-y-2 max-h-96 overflow-y-auto">
            {agentLogs.slice(-20).reverse().map((log, index) => (
              <div key={index} className="bg-gray-50 rounded-lg p-3 text-sm">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <span className="font-medium text-gray-900">
                      {log.type === 'trigger' ? `Triggered ${log.agent}` : 
                       log.type === 'status_update' ? 'Status Update' : 
                       log.type === 'decision' ? 'Agent Decision' : log.type}
                    </span>
                    {log.responseTime && (
                      <span className="ml-2 text-blue-600">({log.responseTime}ms)</span>
                    )}
                    {log.error && (
                      <span className="ml-2 text-red-600">Error: {log.error}</span>
                    )}
                  </div>
                  <span className="text-gray-500 text-xs">
                    {new Date(log.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AgentTester;
