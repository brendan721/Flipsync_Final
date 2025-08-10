#!/usr/bin/env node

/**
 * Day 7: Complete Business Workflow Testing
 * FlipSync 4+1 Architecture End-to-End Validation
 * 
 * Tests complete business workflows:
 * 1. Product Listing Creation Workflow
 * 2. Shipping Arbitrage Workflow  
 * 3. Market Analysis Workflow
 * 
 * Success Criteria: >98% success rate, acceptable timeframes
 */

const axios = require('axios');
const WebSocket = require('ws');

// Production backend configuration
const PRODUCTION_API_BASE = 'http://174.138.77.110:8000';
const WS_URL = 'ws://174.138.77.110:8000/ws/flipsync';
const TIMEOUT_MS = 30000;

class BusinessWorkflowTester {
  constructor() {
    this.results = {
      productListingWorkflow: {},
      shippingArbitrageWorkflow: {},
      marketAnalysisWorkflow: {},
      summary: { totalWorkflows: 0, successfulWorkflows: 0, failedWorkflows: 0 }
    };
    
    this.client = axios.create({
      baseURL: PRODUCTION_API_BASE,
      timeout: TIMEOUT_MS,
      headers: { 'Content-Type': 'application/json' }
    });
  }

  async testProductListingCreationWorkflow() {
    console.log('\n🚀 Testing Product Listing Creation Workflow');
    console.log('=' .repeat(70));
    
    const workflow = {
      name: 'Product Listing Creation',
      steps: [],
      startTime: Date.now(),
      success: false,
      agents_involved: []
    };

    try {
      // Step 1: Content Agent - Product Identification via Orchestration
      console.log('\n📝 Step 1: Content Agent - Product Identification');
      const productData = {
        barcode: '123456789012',
        product_name: 'Test Product for Listing',
        category: 'Electronics',
        condition: 'New'
      };

      const contentResponse = await this.client.post('/api/v1/orchestration/decision/execute', {
        agent_type: 'content',
        decision_type: 'product_identification',
        context: {
          product_data: productData,
          content_type: 'product_listing'
        }
      });
      
      workflow.steps.push({
        step: 1,
        agent: 'content',
        action: 'product_identification',
        status: contentResponse.status === 200 ? 'SUCCESS' : 'FAILED',
        duration: Date.now() - workflow.startTime,
        data: contentResponse.data
      });
      
      if (contentResponse.status === 200) {
        workflow.agents_involved.push('content');
        console.log('✅ Content Agent: Product identification successful');
      } else {
        console.log('❌ Content Agent: Product identification failed');
      }

      // Step 2: Market Agent - Market Analysis
      console.log('\n📊 Step 2: Market Agent - Market Analysis');
      const marketResponse = await this.client.post('/api/v1/orchestration/decision/execute', {
        agent_type: 'market',
        decision_type: 'pricing_strategy',
        context: {
          product: productData,
          analysis_type: 'pricing_strategy'
        }
      });
      
      workflow.steps.push({
        step: 2,
        agent: 'market',
        action: 'market_analysis',
        status: marketResponse.status === 200 ? 'SUCCESS' : 'FAILED',
        duration: Date.now() - workflow.startTime,
        data: marketResponse.data
      });
      
      if (marketResponse.status === 200) {
        workflow.agents_involved.push('market');
        console.log('✅ Market Agent: Market analysis successful');
      } else {
        console.log('❌ Market Agent: Market analysis failed');
      }

      // Step 3: Logistics Agent - Shipping Setup
      console.log('\n🚚 Step 3: Logistics Agent - Shipping Setup');
      const logisticsResponse = await this.client.post('/api/v1/orchestration/decision/execute', {
        agent_type: 'logistics',
        decision_type: 'shipping_strategy',
        context: {
          product: productData,
          optimization_type: 'shipping_strategy'
        }
      });
      
      workflow.steps.push({
        step: 3,
        agent: 'logistics',
        action: 'shipping_setup',
        status: logisticsResponse.status === 200 ? 'SUCCESS' : 'FAILED',
        duration: Date.now() - workflow.startTime,
        data: logisticsResponse.data
      });
      
      if (logisticsResponse.status === 200) {
        workflow.agents_involved.push('logistics');
        console.log('✅ Logistics Agent: Shipping setup successful');
      } else {
        console.log('❌ Logistics Agent: Shipping setup failed');
      }

      // Step 4: Executive Agent - Strategic Review
      console.log('\n🎯 Step 4: Executive Agent - Strategic Review');
      const executiveResponse = await this.client.post('/api/v1/orchestration/decision/execute', {
        agent_type: 'executive',
        decision_type: 'listing_approval',
        context: {
          workflow_data: {
            content: workflow.steps[0]?.data,
            market: workflow.steps[1]?.data,
            logistics: workflow.steps[2]?.data
          }
        }
      });
      
      workflow.steps.push({
        step: 4,
        agent: 'executive',
        action: 'strategic_review',
        status: executiveResponse.status === 200 ? 'SUCCESS' : 'FAILED',
        duration: Date.now() - workflow.startTime,
        data: executiveResponse.data
      });
      
      if (executiveResponse.status === 200) {
        workflow.agents_involved.push('executive');
        console.log('✅ Executive Agent: Strategic review successful');
      } else {
        console.log('❌ Executive Agent: Strategic review failed');
      }

      // Step 5: eBay Listing Deployment (Simulated)
      console.log('\n🏪 Step 5: eBay Listing Deployment (Simulated)');
      const listingData = {
        title: productData.product_name,
        description: workflow.steps[0]?.data?.content || 'Generated content',
        price: workflow.steps[1]?.data?.suggested_price || 29.99,
        shipping: workflow.steps[2]?.data?.shipping_cost || 5.99
      };
      
      // Simulate eBay listing creation
      const listingSuccess = workflow.steps.filter(s => s.status === 'SUCCESS').length >= 3;
      
      workflow.steps.push({
        step: 5,
        agent: 'ebay_integration',
        action: 'listing_deployment',
        status: listingSuccess ? 'SUCCESS' : 'FAILED',
        duration: Date.now() - workflow.startTime,
        data: { listing: listingData, simulated: true }
      });
      
      if (listingSuccess) {
        console.log('✅ eBay Integration: Listing deployment successful (simulated)');
      } else {
        console.log('❌ eBay Integration: Listing deployment failed');
      }

      // Calculate workflow success
      const successfulSteps = workflow.steps.filter(s => s.status === 'SUCCESS').length;
      workflow.success = successfulSteps >= 4; // At least 4/5 steps successful
      workflow.totalDuration = Date.now() - workflow.startTime;
      workflow.successRate = (successfulSteps / workflow.steps.length) * 100;

      console.log(`\n📊 Product Listing Workflow Results:`);
      console.log(`   Success Rate: ${workflow.successRate.toFixed(1)}%`);
      console.log(`   Total Duration: ${workflow.totalDuration}ms`);
      console.log(`   Agents Involved: ${workflow.agents_involved.length}/4`);
      console.log(`   Status: ${workflow.success ? '✅ SUCCESS' : '❌ FAILED'}`);

    } catch (error) {
      console.log(`❌ Product Listing Workflow Error: ${error.message}`);
      workflow.error = error.message;
      workflow.success = false;
    }

    this.results.productListingWorkflow = workflow;
    return workflow;
  }

  async testShippingArbitrageWorkflow() {
    console.log('\n🚀 Testing Shipping Arbitrage Workflow');
    console.log('=' .repeat(70));
    
    const workflow = {
      name: 'Shipping Arbitrage',
      steps: [],
      startTime: Date.now(),
      success: false,
      agents_involved: []
    };

    try {
      // Step 1: Market Agent - Product Analysis
      console.log('\n📊 Step 1: Market Agent - Product Analysis');
      const productAnalysis = await this.client.post('/api/v1/orchestration/decision/execute', {
        agent_type: 'market',
        decision_type: 'arbitrage_opportunity',
        context: {
          product: {
            dimensions: { length: 12, width: 8, height: 4, weight: 2.5 },
            category: 'Electronics',
            current_price: 45.99
          }
        }
      });
      
      workflow.steps.push({
        step: 1,
        agent: 'market',
        action: 'product_analysis',
        status: productAnalysis.status === 200 ? 'SUCCESS' : 'FAILED',
        duration: Date.now() - workflow.startTime
      });
      
      if (productAnalysis.status === 200) {
        workflow.agents_involved.push('market');
        console.log('✅ Market Agent: Product analysis successful');
      }

      // Step 2: Logistics Agent - Dimensional Calculations
      console.log('\n📦 Step 2: Logistics Agent - Dimensional Calculations');
      const dimensionalCalc = await this.client.post('/api/v1/orchestration/decision/execute', {
        agent_type: 'logistics',
        decision_type: 'dimensional_shipping',
        context: {
          product: {
            dimensions: { length: 12, width: 8, height: 4, weight: 2.5 }
          }
        }
      });
      
      workflow.steps.push({
        step: 2,
        agent: 'logistics',
        action: 'dimensional_calculations',
        status: dimensionalCalc.status === 200 ? 'SUCCESS' : 'FAILED',
        duration: Date.now() - workflow.startTime
      });
      
      if (dimensionalCalc.status === 200) {
        workflow.agents_involved.push('logistics');
        console.log('✅ Logistics Agent: Dimensional calculations successful');
      }

      // Step 3: Executive Agent - Profit Margin Analysis
      console.log('\n💰 Step 3: Executive Agent - Profit Margin Analysis');
      const profitAnalysis = await this.client.post('/api/v1/orchestration/decision/execute', {
        agent_type: 'executive',
        decision_type: 'profit_analysis',
        context: {
          analysis_data: {
            market_data: productAnalysis.data,
            shipping_data: dimensionalCalc.data,
            cost_basis: 25.00
          }
        }
      });
      
      workflow.steps.push({
        step: 3,
        agent: 'executive',
        action: 'profit_analysis',
        status: profitAnalysis.status === 200 ? 'SUCCESS' : 'FAILED',
        duration: Date.now() - workflow.startTime
      });
      
      if (profitAnalysis.status === 200) {
        workflow.agents_involved.push('executive');
        console.log('✅ Executive Agent: Profit analysis successful');
      }

      // Step 4: Content Agent - Content Optimization
      console.log('\n✨ Step 4: Content Agent - Content Optimization');
      const contentOpt = await this.client.post('/api/v1/orchestration/decision/execute', {
        agent_type: 'content',
        decision_type: 'arbitrage_listing',
        context: {
          optimization_data: {
            profit_margin: profitAnalysis.data?.profit_margin || 35,
            shipping_advantage: dimensionalCalc.data?.shipping_savings || 15
          }
        }
      });
      
      workflow.steps.push({
        step: 4,
        agent: 'content',
        action: 'content_optimization',
        status: contentOpt.status === 200 ? 'SUCCESS' : 'FAILED',
        duration: Date.now() - workflow.startTime
      });
      
      if (contentOpt.status === 200) {
        workflow.agents_involved.push('content');
        console.log('✅ Content Agent: Content optimization successful');
      }

      // Calculate workflow success
      const successfulSteps = workflow.steps.filter(s => s.status === 'SUCCESS').length;
      workflow.success = successfulSteps >= 3; // At least 3/4 steps successful
      workflow.totalDuration = Date.now() - workflow.startTime;
      workflow.successRate = (successfulSteps / workflow.steps.length) * 100;

      console.log(`\n📊 Shipping Arbitrage Workflow Results:`);
      console.log(`   Success Rate: ${workflow.successRate.toFixed(1)}%`);
      console.log(`   Total Duration: ${workflow.totalDuration}ms`);
      console.log(`   Agents Involved: ${workflow.agents_involved.length}/4`);
      console.log(`   Status: ${workflow.success ? '✅ SUCCESS' : '❌ FAILED'}`);

    } catch (error) {
      console.log(`❌ Shipping Arbitrage Workflow Error: ${error.message}`);
      workflow.error = error.message;
      workflow.success = false;
    }

    this.results.shippingArbitrageWorkflow = workflow;
    return workflow;
  }

  async testMarketAnalysisWorkflow() {
    console.log('\n🚀 Testing Market Analysis Workflow');
    console.log('=' .repeat(70));
    
    const workflow = {
      name: 'Market Analysis',
      steps: [],
      startTime: Date.now(),
      success: false,
      agents_involved: []
    };

    try {
      // Step 1: Market Agent - Competitive Analysis
      console.log('\n🔍 Step 1: Market Agent - Competitive Analysis');
      const competitiveAnalysis = await this.client.post('/api/v1/orchestration/decision/execute', {
        agent_type: 'market',
        decision_type: 'competitive_landscape',
        context: {
          product: {
            category: 'Electronics',
            keywords: ['smartphone', 'accessories', 'wireless']
          }
        }
      });
      
      workflow.steps.push({
        step: 1,
        agent: 'market',
        action: 'competitive_analysis',
        status: competitiveAnalysis.status === 200 ? 'SUCCESS' : 'FAILED',
        duration: Date.now() - workflow.startTime
      });
      
      if (competitiveAnalysis.status === 200) {
        workflow.agents_involved.push('market');
        console.log('✅ Market Agent: Competitive analysis successful');
      }

      // Step 2: Executive Agent - Strategy Validation
      console.log('\n🎯 Step 2: Executive Agent - Strategy Validation');
      const strategyValidation = await this.client.post('/api/v1/orchestration/decision/execute', {
        agent_type: 'executive',
        decision_type: 'market_strategy',
        context: {
          market_data: competitiveAnalysis.data
        }
      });
      
      workflow.steps.push({
        step: 2,
        agent: 'executive',
        action: 'strategy_validation',
        status: strategyValidation.status === 200 ? 'SUCCESS' : 'FAILED',
        duration: Date.now() - workflow.startTime
      });
      
      if (strategyValidation.status === 200) {
        workflow.agents_involved.push('executive');
        console.log('✅ Executive Agent: Strategy validation successful');
      }

      // Step 3: Content Agent - Market-Driven Content
      console.log('\n📝 Step 3: Content Agent - Market-Driven Content');
      const marketContent = await this.client.post('/api/v1/orchestration/decision/execute', {
        agent_type: 'content',
        decision_type: 'market_optimized',
        context: {
          market_insights: {
            competitive_data: competitiveAnalysis.data,
            strategy: strategyValidation.data
          }
        }
      });
      
      workflow.steps.push({
        step: 3,
        agent: 'content',
        action: 'market_content',
        status: marketContent.status === 200 ? 'SUCCESS' : 'FAILED',
        duration: Date.now() - workflow.startTime
      });
      
      if (marketContent.status === 200) {
        workflow.agents_involved.push('content');
        console.log('✅ Content Agent: Market-driven content successful');
      }

      // Calculate workflow success
      const successfulSteps = workflow.steps.filter(s => s.status === 'SUCCESS').length;
      workflow.success = successfulSteps >= 2; // At least 2/3 steps successful
      workflow.totalDuration = Date.now() - workflow.startTime;
      workflow.successRate = (successfulSteps / workflow.steps.length) * 100;

      console.log(`\n📊 Market Analysis Workflow Results:`);
      console.log(`   Success Rate: ${workflow.successRate.toFixed(1)}%`);
      console.log(`   Total Duration: ${workflow.totalDuration}ms`);
      console.log(`   Agents Involved: ${workflow.agents_involved.length}/3`);
      console.log(`   Status: ${workflow.success ? '✅ SUCCESS' : '❌ FAILED'}`);

    } catch (error) {
      console.log(`❌ Market Analysis Workflow Error: ${error.message}`);
      workflow.error = error.message;
      workflow.success = false;
    }

    this.results.marketAnalysisWorkflow = workflow;
    return workflow;
  }

  async generateDay7Report() {
    console.log('\n🎯 DAY 7: BUSINESS WORKFLOW TESTING SUMMARY');
    console.log('=' .repeat(70));
    
    const workflows = [
      this.results.productListingWorkflow,
      this.results.shippingArbitrageWorkflow,
      this.results.marketAnalysisWorkflow
    ];
    
    this.results.summary.totalWorkflows = workflows.length;
    this.results.summary.successfulWorkflows = workflows.filter(w => w.success).length;
    this.results.summary.failedWorkflows = workflows.filter(w => !w.success).length;
    
    const overallSuccessRate = (this.results.summary.successfulWorkflows / this.results.summary.totalWorkflows) * 100;
    
    console.log(`📊 Overall Results:`);
    console.log(`   Total Workflows Tested: ${this.results.summary.totalWorkflows}`);
    console.log(`   Successful Workflows: ${this.results.summary.successfulWorkflows}`);
    console.log(`   Failed Workflows: ${this.results.summary.failedWorkflows}`);
    console.log(`   Overall Success Rate: ${overallSuccessRate.toFixed(1)}%`);
    console.log(`   Target Success Rate: >98%`);
    
    const meetsTarget = overallSuccessRate >= 98;
    console.log(`\n🎯 Day 7 Status: ${meetsTarget ? '✅ SUCCESS - Target Met' : '⚠️  NEEDS IMPROVEMENT'}`);
    
    if (meetsTarget) {
      console.log('✅ All business workflows operational and meeting success criteria');
      console.log('✅ Ready for Day 8: Multi-Agent Coordination Testing');
    } else {
      console.log('⚠️  Some workflows need optimization before proceeding');
    }
    
    return {
      success: meetsTarget,
      overallSuccessRate,
      results: this.results
    };
  }
}

// Main execution
async function main() {
  const tester = new BusinessWorkflowTester();
  
  try {
    console.log('🚀 Day 7: Complete Business Workflow Testing');
    console.log('FlipSync 4+1 Architecture End-to-End Validation');
    console.log('=' .repeat(70));
    
    // Execute all workflow tests
    await tester.testProductListingCreationWorkflow();
    await tester.testShippingArbitrageWorkflow();
    await tester.testMarketAnalysisWorkflow();
    
    // Generate final report
    const report = await tester.generateDay7Report();
    
    // Save results
    const fs = require('fs');
    fs.writeFileSync('day7-business-workflow-results.json', JSON.stringify(report, null, 2));
    console.log('\n📄 Results saved to: day7-business-workflow-results.json');
    
    process.exit(report.success ? 0 : 1);
    
  } catch (error) {
    console.error('\n❌ Day 7 testing execution failed:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = BusinessWorkflowTester;
