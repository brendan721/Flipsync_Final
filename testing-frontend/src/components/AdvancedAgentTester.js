import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { 
  Play, 
  Settings, 
  BarChart3, 
  GitBranch,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Zap,
  Target,
  TrendingUp,
  FileText,
  Truck,
  MessageSquare,
  Users
} from 'lucide-react';
import ReactJsonView from '@microlink/react-json-view';
import api from '../services/api';

const AdvancedAgentTester = () => {
  const [agents, setAgents] = useState([]);
  const [selectedAgents, setSelectedAgents] = useState([]);
  const [workflowMode, setWorkflowMode] = useState('single'); // single, multi, workflow
  const [testResults, setTestResults] = useState({});
  const [performanceHistory, setPerformanceHistory] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [customPayloads, setCustomPayloads] = useState({});
  const [abTestConfig, setAbTestConfig] = useState({ enabled: false, variants: 2 });

  // Agent type configurations with realistic test scenarios
  const agentConfigs = {
    market: {
      name: 'Market Agent',
      icon: TrendingUp,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      description: 'Market analysis and pricing optimization',
      testScenarios: [
        {
          name: 'Product Pricing Analysis',
          payload: {
            action: 'analyze_pricing',
            product: {
              title: 'Apple iPhone 14 Pro 128GB',
              category: 'Cell Phones & Smartphones',
              condition: 'New',
              current_price: 999.99
            },
            market_data: {
              competitor_analysis: true,
              price_history: true,
              demand_analysis: true
            }
          }
        },
        {
          name: 'Market Trend Analysis',
          payload: {
            action: 'analyze_trends',
            category: 'Electronics',
            timeframe: '30_days',
            metrics: ['price_trends', 'demand_patterns', 'competition_level']
          }
        }
      ]
    },
    content: {
      name: 'Content Agent',
      icon: FileText,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      description: 'Content generation and SEO optimization',
      testScenarios: [
        {
          name: 'eBay Listing Generation',
          payload: {
            action: 'generate_listing',
            product: {
              title: 'Samsung Galaxy S23 Ultra',
              brand: 'Samsung',
              model: 'Galaxy S23 Ultra',
              condition: 'New',
              features: ['5G', '200MP Camera', '8GB RAM', '256GB Storage']
            },
            optimization: {
              seo_keywords: true,
              competitive_analysis: true,
              conversion_optimization: true
            }
          }
        },
        {
          name: 'Content Optimization',
          payload: {
            action: 'optimize_content',
            existing_listing: {
              title: 'Phone for sale',
              description: 'Good phone, works well'
            },
            target_metrics: ['click_through_rate', 'conversion_rate', 'search_ranking']
          }
        }
      ]
    },
    executive: {
      name: 'Executive Agent',
      icon: Settings,
      color: 'text-purple-600',
      bgColor: 'bg-purple-50',
      description: 'Strategic planning and coordination',
      testScenarios: [
        {
          name: 'Strategic Decision Making',
          payload: {
            action: 'strategic_analysis',
            scenario: 'inventory_optimization',
            data: {
              current_inventory: 150,
              sales_velocity: 12.5,
              market_conditions: 'high_demand',
              seasonal_factors: ['back_to_school', 'holiday_prep']
            },
            decision_criteria: ['profitability', 'risk_assessment', 'resource_allocation']
          }
        },
        {
          name: 'Cross-Agent Coordination',
          payload: {
            action: 'coordinate_workflow',
            workflow_type: 'product_launch',
            agents_involved: ['market', 'content', 'logistics'],
            priority: 'high',
            timeline: '48_hours'
          }
        }
      ]
    },
    logistics: {
      name: 'Logistics Agent',
      icon: Truck,
      color: 'text-orange-600',
      bgColor: 'bg-orange-50',
      description: 'Inventory and shipping optimization',
      testScenarios: [
        {
          name: 'Shipping Optimization',
          payload: {
            action: 'optimize_shipping',
            order: {
              items: [{ weight: 2.5, dimensions: [10, 8, 3] }],
              destination: { zip: '90210', state: 'CA' },
              priority: 'standard'
            },
            options: {
              calculate_zones: true,
              compare_carriers: true,
              cost_optimization: true
            }
          }
        },
        {
          name: 'Inventory Management',
          payload: {
            action: 'manage_inventory',
            products: [
              { sku: 'IPHONE14-128', current_stock: 25, reorder_point: 10 },
              { sku: 'SAMSUNG-S23', current_stock: 8, reorder_point: 15 }
            ],
            analysis_type: 'reorder_optimization'
          }
        }
      ]
    },
    chat: {
      name: 'Strategic Chat',
      icon: MessageSquare,
      color: 'text-indigo-600',
      bgColor: 'bg-indigo-50',
      description: 'Conversational interface with Gemini',
      testScenarios: [
        {
          name: 'Business Query Processing',
          payload: {
            action: 'process_query',
            query: 'What is the optimal pricing strategy for electronics during Q4?',
            context: {
              business_type: 'e-commerce',
              category: 'electronics',
              current_season: 'Q4'
            }
          }
        },
        {
          name: 'Agent Collaboration Request',
          payload: {
            action: 'coordinate_agents',
            request: 'Analyze market trends and generate optimized listings for top 5 products',
            agents_needed: ['market', 'content'],
            urgency: 'high'
          }
        }
      ]
    }
  };

  useEffect(() => {
    loadAgentData();
  }, []);

  const loadAgentData = async () => {
    setIsLoading(true);
    try {
      const [agentsResponse, chatResponse] = await Promise.allSettled([
        api.get4Plus1Agents(),
        api.getChatAgentStatus()
      ]);

      let agentsList = [];
      if (agentsResponse.status === 'fulfilled') {
        // Map backend agents to our configurations
        const backendAgents = chatResponse.value?.agents || [];
        agentsList = backendAgents.map(agent => ({
          ...agent,
          config: agentConfigs[agent.agent_type] || agentConfigs.chat,
          scenarios: agentConfigs[agent.agent_type]?.testScenarios || []
        }));
      }

      setAgents(agentsList);
      toast.success(`Loaded ${agentsList.length} agents with advanced testing capabilities`);
    } catch (error) {
      console.error('Failed to load agent data:', error);
      toast.error('Failed to load agent data');
    } finally {
      setIsLoading(false);
    }
  };

  const executeAgentTest = async (agent, scenario, options = {}) => {
    const testId = `${agent.agent_id}_${scenario.name}_${Date.now()}`;
    setIsLoading(true);

    try {
      const startTime = Date.now();
      
      // Execute the test
      const response = await api.triggerAgent(agent.agent_id, scenario.payload);
      
      const endTime = Date.now();
      const executionTime = endTime - startTime;

      // Store results
      const result = {
        id: testId,
        agent: agent.agent_id,
        agentType: agent.agent_type,
        scenario: scenario.name,
        success: true,
        executionTime,
        response,
        timestamp: new Date().toISOString(),
        ...options
      };

      setTestResults(prev => ({
        ...prev,
        [testId]: result
      }));

      // Update performance history
      updatePerformanceHistory(agent.agent_id, executionTime, true);

      toast.success(`${agent.config.name} - ${scenario.name}: Success (${executionTime}ms)`);
      return result;

    } catch (error) {
      const result = {
        id: testId,
        agent: agent.agent_id,
        agentType: agent.agent_type,
        scenario: scenario.name,
        success: false,
        error: error.message,
        timestamp: new Date().toISOString(),
        ...options
      };

      setTestResults(prev => ({
        ...prev,
        [testId]: result
      }));

      updatePerformanceHistory(agent.agent_id, -1, false);
      toast.error(`${agent.config.name} - ${scenario.name}: Failed`);
      return result;

    } finally {
      setIsLoading(false);
    }
  };

  const executeWorkflow = async (workflowAgents, workflowType = 'sequential') => {
    setIsLoading(true);
    const workflowId = `workflow_${Date.now()}`;
    const workflowResults = [];

    try {
      if (workflowType === 'sequential') {
        // Execute agents in sequence
        for (const agent of workflowAgents) {
          const scenario = agent.scenarios[0]; // Use first scenario
          const result = await executeAgentTest(agent, scenario, { workflowId, workflowType });
          workflowResults.push(result);
          
          // Brief delay between agents
          await new Promise(resolve => setTimeout(resolve, 500));
        }
      } else if (workflowType === 'parallel') {
        // Execute agents in parallel
        const promises = workflowAgents.map(agent => {
          const scenario = agent.scenarios[0];
          return executeAgentTest(agent, scenario, { workflowId, workflowType });
        });
        const results = await Promise.allSettled(promises);
        workflowResults.push(...results.map(r => r.value || r.reason));
      }

      toast.success(`Workflow completed: ${workflowResults.length} agents executed`);
      return workflowResults;

    } catch (error) {
      toast.error(`Workflow failed: ${error.message}`);
      return workflowResults;
    } finally {
      setIsLoading(false);
    }
  };

  const updatePerformanceHistory = (agentId, executionTime, success) => {
    setPerformanceHistory(prev => {
      const history = prev[agentId] || { times: [], successes: 0, failures: 0 };
      return {
        ...prev,
        [agentId]: {
          times: [...history.times, executionTime].slice(-20), // Keep last 20 results
          successes: success ? history.successes + 1 : history.successes,
          failures: success ? history.failures : history.failures + 1,
          lastUpdate: new Date().toISOString()
        }
      };
    });
  };

  const getAgentPerformanceMetrics = (agentId) => {
    const history = performanceHistory[agentId];
    if (!history || history.times.length === 0) return null;

    const validTimes = history.times.filter(t => t > 0);
    return {
      averageTime: validTimes.length > 0 ? Math.round(validTimes.reduce((a, b) => a + b, 0) / validTimes.length) : 0,
      successRate: Math.round((history.successes / (history.successes + history.failures)) * 100),
      totalTests: history.successes + history.failures,
      trend: validTimes.length >= 2 ? (validTimes[validTimes.length - 1] < validTimes[0] ? 'improving' : 'stable') : 'stable'
    };
  };

  return (
    <div className="space-y-6">
      {/* Header Controls */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Advanced Agent Testing</h2>
            <p className="text-gray-600">Multi-agent workflows, A/B testing, and performance analysis</p>
          </div>
          <button
            onClick={loadAgentData}
            disabled={isLoading}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center space-x-2"
          >
            <BarChart3 className="w-4 h-4" />
            <span>Refresh Agents</span>
          </button>
        </div>

        {/* Testing Mode Selection */}
        <div className="flex space-x-4 mb-4">
          <button
            onClick={() => setWorkflowMode('single')}
            className={`px-4 py-2 rounded-lg flex items-center space-x-2 ${
              workflowMode === 'single' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
            }`}
          >
            <Target className="w-4 h-4" />
            <span>Single Agent</span>
          </button>
          <button
            onClick={() => setWorkflowMode('multi')}
            className={`px-4 py-2 rounded-lg flex items-center space-x-2 ${
              workflowMode === 'multi' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
            }`}
          >
            <Users className="w-4 h-4" />
            <span>Multi-Agent</span>
          </button>
          <button
            onClick={() => setWorkflowMode('workflow')}
            className={`px-4 py-2 rounded-lg flex items-center space-x-2 ${
              workflowMode === 'workflow' ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-700'
            }`}
          >
            <GitBranch className="w-4 h-4" />
            <span>Workflow</span>
          </button>
        </div>

        {/* A/B Testing Configuration */}
        <div className="flex items-center space-x-4">
          <label className="flex items-center space-x-2">
            <input
              type="checkbox"
              checked={abTestConfig.enabled}
              onChange={(e) => setAbTestConfig(prev => ({ ...prev, enabled: e.target.checked }))}
              className="rounded"
            />
            <span className="text-sm text-gray-700">Enable A/B Testing</span>
          </label>
          {abTestConfig.enabled && (
            <select
              value={abTestConfig.variants}
              onChange={(e) => setAbTestConfig(prev => ({ ...prev, variants: parseInt(e.target.value) }))}
              className="px-3 py-1 border border-gray-300 rounded text-sm"
            >
              <option value={2}>2 Variants</option>
              <option value={3}>3 Variants</option>
              <option value={4}>4 Variants</option>
            </select>
          )}
        </div>
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <AgentTestCard
            key={agent.agent_id}
            agent={agent}
            onTest={executeAgentTest}
            performance={getAgentPerformanceMetrics(agent.agent_id)}
            isLoading={isLoading}
            workflowMode={workflowMode}
            selectedAgents={selectedAgents}
            onSelectionChange={setSelectedAgents}
          />
        ))}
      </div>

      {/* Workflow Controls */}
      {workflowMode !== 'single' && selectedAgents.length > 1 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Workflow Execution</h3>
          <div className="flex space-x-4">
            <button
              onClick={() => executeWorkflow(selectedAgents, 'sequential')}
              disabled={isLoading}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center space-x-2"
            >
              <GitBranch className="w-4 h-4" />
              <span>Sequential Workflow</span>
            </button>
            <button
              onClick={() => executeWorkflow(selectedAgents, 'parallel')}
              disabled={isLoading}
              className="px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 flex items-center space-x-2"
            >
              <Zap className="w-4 h-4" />
              <span>Parallel Workflow</span>
            </button>
          </div>
        </div>
      )}

      {/* Test Results */}
      <TestResultsPanel results={testResults} />
    </div>
  );
};

// Individual Agent Test Card Component
const AgentTestCard = ({ agent, onTest, performance, isLoading, workflowMode, selectedAgents, onSelectionChange }) => {
  const [selectedScenario, setSelectedScenario] = useState(0);
  const config = agent.config || {};
  const Icon = config.icon || Settings;

  const handleSelection = (selected) => {
    if (selected) {
      onSelectionChange(prev => [...prev, agent]);
    } else {
      onSelectionChange(prev => prev.filter(a => a.agent_id !== agent.agent_id));
    }
  };

  const isSelected = selectedAgents.some(a => a.agent_id === agent.agent_id);

  return (
    <div className={`bg-white rounded-lg shadow-sm border-2 transition-all ${
      isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200'
    }`}>
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${config.bgColor || 'bg-gray-50'}`}>
              <Icon className={`w-6 h-6 ${config.color || 'text-gray-600'}`} />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{config.name || agent.agent_type}</h3>
              <p className="text-sm text-gray-600">{agent.status}</p>
            </div>
          </div>
          {workflowMode !== 'single' && (
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => handleSelection(e.target.checked)}
              className="rounded"
            />
          )}
        </div>

        {/* Performance Metrics */}
        {performance && (
          <div className="grid grid-cols-3 gap-2 mb-4 text-sm">
            <div className="text-center">
              <div className="font-semibold text-gray-900">{performance.averageTime}ms</div>
              <div className="text-gray-600">Avg Time</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-gray-900">{performance.successRate}%</div>
              <div className="text-gray-600">Success</div>
            </div>
            <div className="text-center">
              <div className="font-semibold text-gray-900">{performance.totalTests}</div>
              <div className="text-gray-600">Tests</div>
            </div>
          </div>
        )}

        {/* Scenario Selection */}
        {agent.scenarios && agent.scenarios.length > 0 && (
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">Test Scenario</label>
            <select
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm"
            >
              {agent.scenarios.map((scenario, index) => (
                <option key={index} value={index}>{scenario.name}</option>
              ))}
            </select>
          </div>
        )}

        {/* Test Button */}
        <button
          onClick={() => onTest(agent, agent.scenarios[selectedScenario])}
          disabled={isLoading || !agent.scenarios || agent.scenarios.length === 0}
          className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 flex items-center justify-center space-x-2"
        >
          <Play className="w-4 h-4" />
          <span>Execute Test</span>
        </button>
      </div>
    </div>
  );
};

// Test Results Panel Component
const TestResultsPanel = ({ results }) => {
  const resultsList = Object.values(results).sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  if (resultsList.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Results</h3>
        <p className="text-gray-500 text-center py-8">No test results yet. Execute some agent tests to see results here.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Results ({resultsList.length})</h3>
      <div className="space-y-4 max-h-96 overflow-y-auto">
        {resultsList.map((result) => (
          <div key={result.id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center space-x-2">
                {result.success ? (
                  <CheckCircle className="w-5 h-5 text-green-500" />
                ) : (
                  <XCircle className="w-5 h-5 text-red-500" />
                )}
                <span className="font-medium">{result.agent} - {result.scenario}</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <Clock className="w-4 h-4" />
                <span>{result.executionTime || 'N/A'}ms</span>
              </div>
            </div>
            {result.response && (
              <ReactJsonView
                src={result.response}
                theme="rjv-default"
                collapsed={2}
                displayDataTypes={false}
                displayObjectSize={false}
                name={false}
                style={{ fontSize: '12px', maxHeight: '200px', overflow: 'auto' }}
              />
            )}
            {result.error && (
              <div className="text-red-600 text-sm mt-2">
                Error: {result.error}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default AdvancedAgentTester;
