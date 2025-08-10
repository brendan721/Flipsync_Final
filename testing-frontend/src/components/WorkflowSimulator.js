import React, { useState, useEffect } from 'react';
import { toast } from 'react-toastify';
import { 
  Play, 
  Pause, 
  Square, 
  SkipForward,
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  ArrowRight,
  Package,
  DollarSign,
  FileText,
  Truck,
  BarChart3,
  Zap,
  RefreshCw
} from 'lucide-react';
import api from '../services/api';

const WorkflowSimulator = () => {
  const [activeWorkflow, setActiveWorkflow] = useState(null);
  const [workflowState, setWorkflowState] = useState('idle'); // idle, running, paused, completed, failed
  const [currentStep, setCurrentStep] = useState(0);
  const [stepResults, setStepResults] = useState({});
  const [workflowMetrics, setWorkflowMetrics] = useState({});
  const [simulationSpeed, setSimulationSpeed] = useState(1); // 1x, 2x, 5x speed

  // Predefined realistic workflows based on actual business operations
  const workflows = {
    product_listing: {
      name: 'End-to-End Product Listing Creation',
      description: 'Complete workflow from barcode scan to live eBay listing',
      estimatedTime: '2-3 minutes',
      steps: [
        {
          id: 'product_scan',
          name: 'Product Identification',
          description: 'Scan barcode and identify product details',
          agent: 'content',
          duration: 5000,
          payload: {
            action: 'identify_product',
            barcode: '885909950805',
            source: 'barcode_scan'
          },
          expectedOutput: ['product_title', 'brand', 'model', 'category']
        },
        {
          id: 'market_analysis',
          name: 'Market Research & Pricing',
          description: 'Analyze market conditions and determine optimal pricing',
          agent: 'market',
          duration: 8000,
          payload: {
            action: 'analyze_pricing',
            product_data: '${product_scan.output}',
            market_research: true,
            competitor_analysis: true
          },
          expectedOutput: ['suggested_price', 'market_demand', 'competition_level']
        },
        {
          id: 'content_generation',
          name: 'Listing Content Creation',
          description: 'Generate optimized title, description, and keywords',
          agent: 'content',
          duration: 12000,
          payload: {
            action: 'generate_listing',
            product_data: '${product_scan.output}',
            pricing_data: '${market_analysis.output}',
            optimization_level: 'high'
          },
          expectedOutput: ['optimized_title', 'description', 'keywords', 'category']
        },
        {
          id: 'shipping_calculation',
          name: 'Shipping & Logistics Setup',
          description: 'Calculate shipping costs and setup logistics',
          agent: 'logistics',
          duration: 6000,
          payload: {
            action: 'setup_shipping',
            product_data: '${product_scan.output}',
            shipping_zones: 'all_us',
            calculate_dimensional: true
          },
          expectedOutput: ['shipping_cost', 'handling_time', 'shipping_options']
        },
        {
          id: 'executive_review',
          name: 'Strategic Review & Approval',
          description: 'Executive agent reviews and approves listing strategy',
          agent: 'executive',
          duration: 4000,
          payload: {
            action: 'review_listing_strategy',
            listing_data: '${content_generation.output}',
            pricing_data: '${market_analysis.output}',
            logistics_data: '${shipping_calculation.output}'
          },
          expectedOutput: ['approval_status', 'recommendations', 'risk_assessment']
        },
        {
          id: 'listing_creation',
          name: 'eBay Listing Creation',
          description: 'Create live eBay listing with all optimized data',
          agent: 'marketplace',
          duration: 10000,
          payload: {
            action: 'create_ebay_listing',
            listing_data: '${content_generation.output}',
            pricing: '${market_analysis.output.suggested_price}',
            shipping: '${shipping_calculation.output}',
            approved: '${executive_review.output.approval_status}'
          },
          expectedOutput: ['listing_id', 'listing_url', 'status', 'fees']
        }
      ]
    },
    market_optimization: {
      name: 'Market Analysis & Pricing Optimization',
      description: 'Comprehensive market analysis for inventory optimization',
      estimatedTime: '1-2 minutes',
      steps: [
        {
          id: 'inventory_analysis',
          name: 'Current Inventory Assessment',
          description: 'Analyze current inventory levels and performance',
          agent: 'logistics',
          duration: 6000,
          payload: {
            action: 'analyze_inventory',
            include_performance_metrics: true,
            timeframe: '30_days'
          },
          expectedOutput: ['inventory_levels', 'turnover_rates', 'slow_movers']
        },
        {
          id: 'market_trends',
          name: 'Market Trend Analysis',
          description: 'Analyze current market trends and demand patterns',
          agent: 'market',
          duration: 10000,
          payload: {
            action: 'analyze_market_trends',
            categories: ['electronics', 'home_garden', 'fashion'],
            trend_period: '90_days',
            include_seasonal: true
          },
          expectedOutput: ['trending_categories', 'demand_forecast', 'seasonal_patterns']
        },
        {
          id: 'pricing_optimization',
          name: 'Dynamic Pricing Strategy',
          description: 'Optimize pricing based on market conditions',
          agent: 'market',
          duration: 8000,
          payload: {
            action: 'optimize_pricing',
            inventory_data: '${inventory_analysis.output}',
            market_data: '${market_trends.output}',
            strategy: 'profit_maximization'
          },
          expectedOutput: ['price_adjustments', 'expected_impact', 'implementation_plan']
        },
        {
          id: 'content_updates',
          name: 'Listing Content Optimization',
          description: 'Update listing content based on market insights',
          agent: 'content',
          duration: 7000,
          payload: {
            action: 'optimize_listings',
            market_insights: '${market_trends.output}',
            pricing_strategy: '${pricing_optimization.output}',
            update_type: 'bulk_optimization'
          },
          expectedOutput: ['updated_listings', 'seo_improvements', 'conversion_optimizations']
        },
        {
          id: 'strategic_planning',
          name: 'Strategic Implementation Plan',
          description: 'Create comprehensive implementation strategy',
          agent: 'executive',
          duration: 5000,
          payload: {
            action: 'create_implementation_plan',
            pricing_strategy: '${pricing_optimization.output}',
            content_updates: '${content_updates.output}',
            timeline: 'immediate'
          },
          expectedOutput: ['implementation_timeline', 'resource_requirements', 'success_metrics']
        }
      ]
    },
    inventory_management: {
      name: 'Intelligent Inventory Management',
      description: 'AI-driven inventory optimization and reorder management',
      estimatedTime: '1-2 minutes',
      steps: [
        {
          id: 'demand_forecasting',
          name: 'Demand Forecasting Analysis',
          description: 'Predict future demand using historical data and trends',
          agent: 'market',
          duration: 9000,
          payload: {
            action: 'forecast_demand',
            historical_period: '12_months',
            include_seasonality: true,
            external_factors: ['economic_indicators', 'market_trends']
          },
          expectedOutput: ['demand_forecast', 'confidence_intervals', 'risk_factors']
        },
        {
          id: 'inventory_optimization',
          name: 'Inventory Level Optimization',
          description: 'Optimize inventory levels based on demand forecast',
          agent: 'logistics',
          duration: 7000,
          payload: {
            action: 'optimize_inventory_levels',
            demand_forecast: '${demand_forecasting.output}',
            current_inventory: 'fetch_current',
            optimization_goal: 'minimize_carrying_cost'
          },
          expectedOutput: ['optimal_levels', 'reorder_points', 'safety_stock']
        },
        {
          id: 'supplier_analysis',
          name: 'Supplier Performance Analysis',
          description: 'Analyze supplier performance and lead times',
          agent: 'logistics',
          duration: 6000,
          payload: {
            action: 'analyze_suppliers',
            include_lead_times: true,
            performance_metrics: ['delivery_time', 'quality', 'cost'],
            evaluation_period: '6_months'
          },
          expectedOutput: ['supplier_rankings', 'lead_time_analysis', 'cost_comparison']
        },
        {
          id: 'reorder_strategy',
          name: 'Automated Reorder Strategy',
          description: 'Create intelligent reorder strategy and automation rules',
          agent: 'executive',
          duration: 5000,
          payload: {
            action: 'create_reorder_strategy',
            inventory_optimization: '${inventory_optimization.output}',
            supplier_analysis: '${supplier_analysis.output}',
            automation_level: 'high'
          },
          expectedOutput: ['reorder_rules', 'automation_triggers', 'approval_workflows']
        }
      ]
    },
    peak_load_simulation: {
      name: 'Peak Load Stress Testing',
      description: 'Simulate Black Friday / holiday peak load conditions',
      estimatedTime: '3-5 minutes',
      steps: [
        {
          id: 'load_preparation',
          name: 'System Load Preparation',
          description: 'Prepare system for high-volume operations',
          agent: 'executive',
          duration: 3000,
          payload: {
            action: 'prepare_peak_load',
            expected_volume: '10x_normal',
            duration: '24_hours',
            priority_products: 'top_100'
          },
          expectedOutput: ['system_status', 'resource_allocation', 'monitoring_setup']
        },
        {
          id: 'bulk_market_analysis',
          name: 'Bulk Market Analysis',
          description: 'Analyze market conditions for high-volume products',
          agent: 'market',
          duration: 15000,
          payload: {
            action: 'bulk_market_analysis',
            product_count: 100,
            analysis_depth: 'comprehensive',
            real_time_updates: true
          },
          expectedOutput: ['market_analysis_results', 'pricing_recommendations', 'demand_predictions']
        },
        {
          id: 'content_bulk_generation',
          name: 'Bulk Content Generation',
          description: 'Generate optimized content for multiple products simultaneously',
          agent: 'content',
          duration: 20000,
          payload: {
            action: 'bulk_content_generation',
            market_data: '${bulk_market_analysis.output}',
            product_count: 100,
            optimization_level: 'high',
            parallel_processing: true
          },
          expectedOutput: ['generated_content', 'seo_optimizations', 'processing_metrics']
        },
        {
          id: 'logistics_scaling',
          name: 'Logistics Scaling Operations',
          description: 'Scale logistics operations for peak demand',
          agent: 'logistics',
          duration: 12000,
          payload: {
            action: 'scale_logistics',
            expected_volume: '10x_normal',
            shipping_optimization: 'peak_efficiency',
            carrier_diversification: true
          },
          expectedOutput: ['scaling_plan', 'shipping_optimizations', 'capacity_analysis']
        },
        {
          id: 'performance_monitoring',
          name: 'Real-time Performance Monitoring',
          description: 'Monitor system performance under peak load',
          agent: 'executive',
          duration: 8000,
          payload: {
            action: 'monitor_peak_performance',
            metrics: ['response_times', 'error_rates', 'throughput'],
            alert_thresholds: 'peak_load_config'
          },
          expectedOutput: ['performance_metrics', 'bottleneck_analysis', 'optimization_recommendations']
        }
      ]
    }
  };

  const startWorkflow = async (workflowKey) => {
    const workflow = workflows[workflowKey];
    if (!workflow) return;

    setActiveWorkflow({ key: workflowKey, ...workflow });
    setWorkflowState('running');
    setCurrentStep(0);
    setStepResults({});
    setWorkflowMetrics({
      startTime: Date.now(),
      totalSteps: workflow.steps.length,
      completedSteps: 0,
      failedSteps: 0
    });

    toast.info(`Starting workflow: ${workflow.name}`);
    await executeWorkflowSteps(workflow.steps);
  };

  const executeWorkflowSteps = async (steps) => {
    for (let i = 0; i < steps.length; i++) {
      if (workflowState === 'paused') {
        // Wait for resume
        await new Promise(resolve => {
          const checkResume = () => {
            if (workflowState === 'running') {
              resolve();
            } else {
              setTimeout(checkResume, 100);
            }
          };
          checkResume();
        });
      }

      if (workflowState === 'idle') break; // Workflow stopped

      setCurrentStep(i);
      const step = steps[i];
      
      try {
        const result = await executeWorkflowStep(step, i);
        setStepResults(prev => ({
          ...prev,
          [step.id]: result
        }));

        setWorkflowMetrics(prev => ({
          ...prev,
          completedSteps: prev.completedSteps + 1
        }));

        // Simulate processing time based on step duration and speed
        const delay = (step.duration || 5000) / simulationSpeed;
        await new Promise(resolve => setTimeout(resolve, delay));

      } catch (error) {
        console.error(`Step ${step.id} failed:`, error);
        setStepResults(prev => ({
          ...prev,
          [step.id]: { success: false, error: error.message }
        }));

        setWorkflowMetrics(prev => ({
          ...prev,
          failedSteps: prev.failedSteps + 1
        }));

        // Continue with next step (resilient workflow)
      }
    }

    // Workflow completed
    setWorkflowState('completed');
    setWorkflowMetrics(prev => ({
      ...prev,
      endTime: Date.now(),
      totalDuration: Date.now() - prev.startTime
    }));

    toast.success(`Workflow completed: ${activeWorkflow.name}`);
  };

  const executeWorkflowStep = async (step, stepIndex) => {
    const startTime = Date.now();
    
    try {
      // Simulate realistic API call based on step configuration
      let payload = step.payload;
      
      // Replace template variables with previous step results
      if (typeof payload === 'object') {
        payload = JSON.parse(JSON.stringify(payload).replace(
          /\$\{(\w+)\.output\}/g,
          (match, stepId) => {
            const stepResult = stepResults[stepId];
            return stepResult ? JSON.stringify(stepResult.output || {}) : '{}';
          }
        ));
      }

      // Execute the step (simulate with realistic data)
      const response = await simulateAgentResponse(step.agent, payload, step.expectedOutput);
      
      const endTime = Date.now();
      const executionTime = endTime - startTime;

      return {
        success: true,
        executionTime,
        output: response,
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      const endTime = Date.now();
      const executionTime = endTime - startTime;

      return {
        success: false,
        executionTime,
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  };

  const simulateAgentResponse = async (agentType, payload, expectedOutput) => {
    // Simulate realistic agent responses based on the agent type and expected output
    const responses = {
      market: {
        suggested_price: 299.99,
        market_demand: 'high',
        competition_level: 'moderate',
        demand_forecast: { next_30_days: 'increasing', confidence: 0.85 },
        trending_categories: ['electronics', 'home_improvement'],
        price_adjustments: [{ product_id: 'ABC123', old_price: 199.99, new_price: 219.99 }]
      },
      content: {
        product_title: 'Apple iPhone 14 Pro 128GB - Unlocked',
        optimized_title: 'Apple iPhone 14 Pro 128GB Unlocked Smartphone - Deep Purple - NEW',
        description: 'Brand new Apple iPhone 14 Pro with advanced camera system...',
        keywords: ['iPhone', 'Apple', 'smartphone', 'unlocked', '5G'],
        category: 'Cell Phones & Smartphones',
        updated_listings: 25,
        seo_improvements: 'Title optimization, keyword density improvement'
      },
      logistics: {
        shipping_cost: 12.99,
        handling_time: '1 business day',
        shipping_options: ['Standard', 'Expedited', 'Overnight'],
        inventory_levels: { total_items: 1250, categories: 15 },
        optimal_levels: { reorder_point: 50, max_stock: 200 },
        supplier_rankings: [{ name: 'Supplier A', score: 9.2 }, { name: 'Supplier B', score: 8.7 }]
      },
      executive: {
        approval_status: 'approved',
        recommendations: ['Increase marketing budget', 'Monitor competitor pricing'],
        risk_assessment: 'low',
        implementation_timeline: '2-3 business days',
        resource_requirements: 'Standard allocation sufficient',
        success_metrics: ['Revenue increase: 15%', 'Conversion rate: +2.3%']
      },
      marketplace: {
        listing_id: 'eBay-' + Math.random().toString(36).substr(2, 9),
        listing_url: 'https://ebay.com/itm/123456789',
        status: 'active',
        fees: { insertion_fee: 0.35, final_value_fee: '12.9%' }
      }
    };

    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, Math.random() * 1000 + 500));

    // Return realistic response based on expected output
    const agentResponses = responses[agentType] || {};
    const response = {};
    
    expectedOutput.forEach(field => {
      if (agentResponses[field]) {
        response[field] = agentResponses[field];
      } else {
        response[field] = `Simulated ${field} data`;
      }
    });

    return response;
  };

  const pauseWorkflow = () => {
    setWorkflowState('paused');
    toast.info('Workflow paused');
  };

  const resumeWorkflow = () => {
    setWorkflowState('running');
    toast.info('Workflow resumed');
  };

  const stopWorkflow = () => {
    setWorkflowState('idle');
    setActiveWorkflow(null);
    setCurrentStep(0);
    setStepResults({});
    toast.info('Workflow stopped');
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Workflow Simulator</h2>
            <p className="text-gray-600">Realistic business workflow testing and validation</p>
          </div>
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2">
              <span className="text-sm text-gray-700">Speed:</span>
              <select
                value={simulationSpeed}
                onChange={(e) => setSimulationSpeed(parseFloat(e.target.value))}
                className="px-3 py-1 border border-gray-300 rounded text-sm"
              >
                <option value={0.5}>0.5x</option>
                <option value={1}>1x</option>
                <option value={2}>2x</option>
                <option value={5}>5x</option>
              </select>
            </label>
          </div>
        </div>

        {/* Workflow Controls */}
        {activeWorkflow && (
          <div className="flex items-center space-x-4 mb-4">
            {workflowState === 'running' ? (
              <button
                onClick={pauseWorkflow}
                className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 flex items-center space-x-2"
              >
                <Pause className="w-4 h-4" />
                <span>Pause</span>
              </button>
            ) : workflowState === 'paused' ? (
              <button
                onClick={resumeWorkflow}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center space-x-2"
              >
                <Play className="w-4 h-4" />
                <span>Resume</span>
              </button>
            ) : null}
            
            <button
              onClick={stopWorkflow}
              className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 flex items-center space-x-2"
            >
              <Square className="w-4 h-4" />
              <span>Stop</span>
            </button>

            <div className="text-sm text-gray-600">
              Step {currentStep + 1} of {activeWorkflow.steps.length}
            </div>
          </div>
        )}
      </div>

      {/* Workflow Selection */}
      {!activeWorkflow && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {Object.entries(workflows).map(([key, workflow]) => (
            <WorkflowCard
              key={key}
              workflowKey={key}
              workflow={workflow}
              onStart={startWorkflow}
            />
          ))}
        </div>
      )}

      {/* Active Workflow Display */}
      {activeWorkflow && (
        <div className="space-y-6">
          {/* Progress Overview */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{activeWorkflow.name}</h3>
            
            {/* Progress Bar */}
            <div className="mb-4">
              <div className="flex justify-between text-sm text-gray-600 mb-2">
                <span>Progress</span>
                <span>{Math.round((currentStep / activeWorkflow.steps.length) * 100)}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${(currentStep / activeWorkflow.steps.length) * 100}%` }}
                ></div>
              </div>
            </div>

            {/* Metrics */}
            {workflowMetrics.startTime && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="text-gray-600">Completed</div>
                  <div className="font-semibold">{workflowMetrics.completedSteps}/{workflowMetrics.totalSteps}</div>
                </div>
                <div>
                  <div className="text-gray-600">Failed</div>
                  <div className="font-semibold text-red-600">{workflowMetrics.failedSteps}</div>
                </div>
                <div>
                  <div className="text-gray-600">Duration</div>
                  <div className="font-semibold">
                    {workflowMetrics.endTime 
                      ? `${Math.round((workflowMetrics.endTime - workflowMetrics.startTime) / 1000)}s`
                      : `${Math.round((Date.now() - workflowMetrics.startTime) / 1000)}s`
                    }
                  </div>
                </div>
                <div>
                  <div className="text-gray-600">Status</div>
                  <div className={`font-semibold capitalize ${
                    workflowState === 'completed' ? 'text-green-600' :
                    workflowState === 'running' ? 'text-blue-600' :
                    workflowState === 'paused' ? 'text-yellow-600' :
                    'text-gray-600'
                  }`}>
                    {workflowState}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Step Details */}
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Workflow Steps</h3>
            <div className="space-y-4">
              {activeWorkflow.steps.map((step, index) => (
                <WorkflowStep
                  key={step.id}
                  step={step}
                  index={index}
                  isActive={index === currentStep}
                  isCompleted={index < currentStep}
                  result={stepResults[step.id]}
                />
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

// Workflow Card Component
const WorkflowCard = ({ workflowKey, workflow, onStart }) => {
  const getWorkflowIcon = (key) => {
    switch (key) {
      case 'product_listing': return Package;
      case 'market_optimization': return BarChart3;
      case 'inventory_management': return Truck;
      case 'peak_load_simulation': return Zap;
      default: return FileText;
    }
  };

  const Icon = getWorkflowIcon(workflowKey);

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow">
      <div className="flex items-center space-x-3 mb-4">
        <div className="p-2 bg-blue-50 rounded-lg">
          <Icon className="w-6 h-6 text-blue-600" />
        </div>
        <div>
          <h3 className="font-semibold text-gray-900">{workflow.name}</h3>
          <p className="text-sm text-gray-600">{workflow.estimatedTime}</p>
        </div>
      </div>
      
      <p className="text-gray-700 mb-4">{workflow.description}</p>
      
      <div className="flex items-center justify-between">
        <span className="text-sm text-gray-600">{workflow.steps.length} steps</span>
        <button
          onClick={() => onStart(workflowKey)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 flex items-center space-x-2"
        >
          <Play className="w-4 h-4" />
          <span>Start Workflow</span>
        </button>
      </div>
    </div>
  );
};

// Workflow Step Component
const WorkflowStep = ({ step, index, isActive, isCompleted, result }) => {
  const getStepIcon = () => {
    if (result) {
      return result.success ? (
        <CheckCircle className="w-5 h-5 text-green-500" />
      ) : (
        <XCircle className="w-5 h-5 text-red-500" />
      );
    }
    if (isActive) {
      return <RefreshCw className="w-5 h-5 text-blue-500 animate-spin" />;
    }
    if (isCompleted) {
      return <CheckCircle className="w-5 h-5 text-green-500" />;
    }
    return <div className="w-5 h-5 rounded-full border-2 border-gray-300"></div>;
  };

  return (
    <div className={`flex items-start space-x-4 p-4 rounded-lg ${
      isActive ? 'bg-blue-50 border border-blue-200' :
      isCompleted ? 'bg-green-50 border border-green-200' :
      'bg-gray-50 border border-gray-200'
    }`}>
      <div className="flex-shrink-0 mt-1">
        {getStepIcon()}
      </div>
      
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-medium text-gray-900">{step.name}</h4>
          <div className="flex items-center space-x-2 text-sm text-gray-600">
            <span className="capitalize">{step.agent} agent</span>
            {result && (
              <>
                <Clock className="w-4 h-4" />
                <span>{result.executionTime}ms</span>
              </>
            )}
          </div>
        </div>
        
        <p className="text-sm text-gray-600 mb-2">{step.description}</p>
        
        {result && result.error && (
          <div className="text-sm text-red-600 bg-red-50 p-2 rounded">
            Error: {result.error}
          </div>
        )}
        
        {result && result.success && result.output && (
          <div className="text-sm text-gray-700 bg-white p-2 rounded border">
            <strong>Output:</strong> {Object.keys(result.output).join(', ')}
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowSimulator;
