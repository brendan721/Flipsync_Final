#!/usr/bin/env python3
import sys
import asyncio
import os
sys.path.append('/app')

async def test_cost_controls_simple():
    try:
        from fs_agt_clean.core.ai.openai_client import create_openai_client, OpenAIModel
        from fs_agt_clean.core.monitoring.cost_tracker import get_cost_tracker, record_ai_cost
        
        print('💰 OpenAI Cost Control Validation Results')
        print('=' * 50)
        
        # 1. Configuration Check
        print('📋 Configuration Validation:')
        daily_budget = os.getenv('OPENAI_DAILY_BUDGET', 'Not set')
        max_cost = os.getenv('OPENAI_MAX_COST_PER_REQUEST', 'Not set')
        provider = os.getenv('LLM_PROVIDER', 'Not set')
        
        print(f'  Daily Budget: ${daily_budget}')
        print(f'  Max Cost Per Request: ${max_cost}')
        print(f'  LLM Provider: {provider}')
        print(f'  Budget Configured: {daily_budget == "2.00"}')
        print(f'  Provider Configured: {provider == "openai"}')
        print()
        
        # 2. Cost Tracker Test
        print('📊 Cost Tracking System:')
        cost_tracker = get_cost_tracker()
        print(f'  Cost Tracker Available: {cost_tracker is not None}')
        print(f'  Cost Tracker Type: {type(cost_tracker).__name__}')
        print()
        
        # 3. Client Initialization
        print('🔧 OpenAI Client Test:')
        client = create_openai_client()
        print(f'  Client Created: {client is not None}')
        print(f'  Client Type: {type(client).__name__}')
        print()
        
        # 4. Cost Estimation Test
        print('🧮 Cost Estimation Test:')
        estimated_cost = client.estimate_cost(OpenAIModel.GPT_4O_MINI, 10, 5)
        print(f'  Estimated cost (10 input, 5 output tokens): ${estimated_cost:.6f}')
        print(f'  Cost under max limit: {estimated_cost < float(max_cost)}')
        print()
        
        # 5. Real API Call with Cost Tracking
        print('🔍 Real API Call Test:')
        response = await client.generate_text(
            prompt='Test cost tracking',
            system_prompt='Respond briefly'
        )
        print(f'  API Call Success: {response.success}')
        print(f'  Response: {response.content}')
        print(f'  Actual Cost: ${response.cost_estimate:.6f}')
        print(f'  Model Used: {response.model}')
        print(f'  Cost Under Limit: {response.cost_estimate < float(max_cost)}')
        print()
        
        # 6. Cost Recording Test
        print('💾 Cost Recording Test:')
        await record_ai_cost(
            category='validation',
            model='gpt-4o-mini',
            operation='cost_control_test',
            cost=response.cost_estimate,
            agent_id='validation_agent',
            tokens_used=10
        )
        print('  Cost Recording: ✅ Successful')
        print()
        
        # 7. Summary
        print('📊 Cost Control Summary:')
        budget_ok = daily_budget == '2.00'
        provider_ok = provider == 'openai'
        cost_tracking_ok = cost_tracker is not None
        api_working = response.success
        cost_under_limit = response.cost_estimate < float(max_cost)
        
        print(f'  Daily Budget ($2.00): {"✅" if budget_ok else "❌"} {daily_budget}')
        print(f'  Max Cost Per Request: {"⚠️" if max_cost == "0.10" else "✅"} ${max_cost} (should be $0.05)')
        print(f'  OpenAI Provider: {"✅" if provider_ok else "❌"} {provider}')
        print(f'  Cost Tracking: {"✅" if cost_tracking_ok else "❌"} Working')
        print(f'  API Functionality: {"✅" if api_working else "❌"} Working')
        print(f'  Cost Under Limit: {"✅" if cost_under_limit else "❌"} ${response.cost_estimate:.6f} < ${max_cost}')
        
        overall_pass = budget_ok and provider_ok and cost_tracking_ok and api_working and cost_under_limit
        print(f'  Overall Status: {"✅ PASS" if overall_pass else "❌ FAIL"}')
        
        return overall_pass
        
    except Exception as e:
        print(f'❌ Cost control validation failed: {e}')
        import traceback
        traceback.print_exc()
        return False

async def main():
    result = await test_cost_controls_simple()
    print(f'\nFinal Result: {"SUCCESS" if result else "FAILURE"}')
    return result

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
