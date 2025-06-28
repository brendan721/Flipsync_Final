import asyncio
import json
from datetime import datetime
import time
import redis

async def test_realtime_business_intelligence():
    results = {
        'timestamp': datetime.now().isoformat(),
        'test_name': 'Phase5_Test4_RealTime_Business_Intelligence_Testing',
        'business_intelligence_tests': {}
    }
    
    print('🔄 Phase 5 Test 4: Real-Time Business Intelligence Testing')
    print('Testing: Redis Cache + Market Data Processing + OpenAI Analytics + Real-Time Capabilities')
    
    try:
        # Step 1: Redis Cache Infrastructure Test
        print('\n🗄️ Step 1: Redis Cache Infrastructure...')
        step1_start = time.time()
        
        # Connect to Redis
        try:
            r = redis.Redis(host='flipsync-infrastructure-redis', port=6379, db=0, decode_responses=True)
            
            # Test Redis connectivity
            redis_ping = r.ping()
            redis_info = r.info()
            
            # Test basic cache operations
            test_key = f"test_cache_{int(time.time())}"
            test_value = {"test": "data", "timestamp": datetime.now().isoformat()}
            
            # Set with expiration
            r.setex(test_key, 300, json.dumps(test_value))
            
            # Retrieve and verify
            cached_value = r.get(test_key)
            cache_retrieval_success = cached_value is not None
            
            # Clean up
            r.delete(test_key)
            
            redis_functional = True
            redis_error = None
            
        except Exception as e:
            redis_functional = False
            redis_error = str(e)
            redis_ping = False
            cache_retrieval_success = False
        
        step1_time = time.time() - step1_start
        
        results['business_intelligence_tests']['redis_infrastructure'] = {
            'execution_time': step1_time,
            'redis_connectivity': redis_functional,
            'redis_ping_successful': redis_ping,
            'cache_operations_working': cache_retrieval_success,
            'redis_host': 'flipsync-infrastructure-redis',
            'redis_port': 6379,
            'error': redis_error,
            'status': 'SUCCESS' if redis_functional else 'FAIL'
        }
        
        # Step 2: Market Data Collection and Caching
        print('\n📊 Step 2: Market Data Collection and Caching...')
        step2_start = time.time()
        
        from fs_agt_clean.agents.market.ebay_client import eBayClient
        from fs_agt_clean.core.ai.openai_client import create_openai_client
        
        # Collect market data
        market_data_collection = {}
        
        async with eBayClient(environment='sandbox') as ebay_client:
            # Search for multiple product categories
            camera_data = await ebay_client.search_products('camera', limit=5)
            electronics_data = await ebay_client.search_products('laptop', limit=5)
            
            market_data_collection = {
                'cameras': {
                    'products_found': len(camera_data),
                    'sample_products': [
                        {
                            'title': product.title,
                            'price': float(product.current_price.amount),
                            'condition': str(product.condition),
                            'seller_rating': product.seller_rating
                        } for product in camera_data[:3]
                    ] if camera_data else [],
                    'price_range': [
                        min(float(p.current_price.amount) for p in camera_data),
                        max(float(p.current_price.amount) for p in camera_data)
                    ] if camera_data else [0, 0],
                    'avg_price': sum(float(p.current_price.amount) for p in camera_data) / len(camera_data) if camera_data else 0
                },
                'electronics': {
                    'products_found': len(electronics_data),
                    'sample_products': [
                        {
                            'title': product.title,
                            'price': float(product.current_price.amount),
                            'condition': str(product.condition),
                            'seller_rating': product.seller_rating
                        } for product in electronics_data[:3]
                    ] if electronics_data else [],
                    'price_range': [
                        min(float(p.current_price.amount) for p in electronics_data),
                        max(float(p.current_price.amount) for p in electronics_data)
                    ] if electronics_data else [0, 0],
                    'avg_price': sum(float(p.current_price.amount) for p in electronics_data) / len(electronics_data) if electronics_data else 0
                },
                'collection_timestamp': datetime.now().isoformat(),
                'total_products_analyzed': len(camera_data) + len(electronics_data)
            }
        
        # Cache market data in Redis
        if redis_functional:
            try:
                market_data_key = f"market_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                r.setex(market_data_key, 3600, json.dumps(market_data_collection))  # 1 hour expiration
                
                # Verify caching
                cached_market_data = r.get(market_data_key)
                market_data_cached = cached_market_data is not None
                
                # Store key for later retrieval
                market_data_cache_key = market_data_key
                
            except Exception as e:
                market_data_cached = False
                market_data_cache_key = None
        else:
            market_data_cached = False
            market_data_cache_key = None
        
        step2_time = time.time() - step2_start
        
        results['business_intelligence_tests']['market_data_collection'] = {
            'execution_time': step2_time,
            'data_collection_successful': len(camera_data) + len(electronics_data) > 0,
            'cameras_found': len(camera_data),
            'electronics_found': len(electronics_data),
            'total_products_analyzed': len(camera_data) + len(electronics_data),
            'market_data_cached': market_data_cached,
            'cache_key': market_data_cache_key,
            'data_freshness': 'real_time',
            'status': 'SUCCESS' if len(camera_data) + len(electronics_data) > 0 else 'PARTIAL'
        }
        
        # Step 3: OpenAI-Powered Business Intelligence Analysis
        print('\n🧠 Step 3: OpenAI Business Intelligence Analysis...')
        step3_start = time.time()
        
        # Create AI client
        ai_client = create_openai_client(daily_budget=2.00)
        
        # Generate comprehensive business intelligence analysis
        analysis_prompt = f"""
        Analyze this real-time market data and provide strategic business intelligence insights:
        
        Market Data Summary:
        - Total Products Analyzed: {market_data_collection['total_products_analyzed']}
        - Camera Market: {market_data_collection['cameras']['products_found']} products, avg price ${market_data_collection['cameras']['avg_price']:.2f}
        - Electronics Market: {market_data_collection['electronics']['products_found']} products, avg price ${market_data_collection['electronics']['avg_price']:.2f}
        
        Camera Market Details:
        {json.dumps(market_data_collection['cameras'], indent=2)}
        
        Electronics Market Details:
        {json.dumps(market_data_collection['electronics'], indent=2)}
        
        Provide:
        1. Market opportunity analysis
        2. Pricing strategy recommendations
        3. Inventory optimization suggestions
        4. Competitive positioning insights
        5. Risk assessment and mitigation strategies
        """
        
        business_intelligence_response = await ai_client.generate_text(
            prompt=analysis_prompt,
            system_prompt='You are an advanced business intelligence analyst specializing in e-commerce market analysis. Provide data-driven insights, strategic recommendations, and actionable business intelligence based on real-time market data.'
        )
        
        step3_time = time.time() - step3_start
        
        # Cache AI analysis results
        if redis_functional and business_intelligence_response.success:
            try:
                analysis_key = f"business_intelligence_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                analysis_data = {
                    'analysis': business_intelligence_response.content,
                    'model_used': business_intelligence_response.model,
                    'cost': business_intelligence_response.cost_estimate,
                    'timestamp': datetime.now().isoformat(),
                    'market_data_key': market_data_cache_key
                }
                r.setex(analysis_key, 1800, json.dumps(analysis_data))  # 30 minutes expiration
                
                analysis_cached = True
                analysis_cache_key = analysis_key
                
            except Exception as e:
                analysis_cached = False
                analysis_cache_key = None
        else:
            analysis_cached = False
            analysis_cache_key = None
        
        results['business_intelligence_tests']['ai_analysis'] = {
            'execution_time': step3_time,
            'analysis_successful': business_intelligence_response.success,
            'ai_model_used': business_intelligence_response.model,
            'analysis_cost': business_intelligence_response.cost_estimate,
            'response_time': business_intelligence_response.response_time,
            'analysis_length': len(business_intelligence_response.content) if business_intelligence_response.content else 0,
            'analysis_preview': business_intelligence_response.content[:300] + '...' if business_intelligence_response.content else None,
            'analysis_cached': analysis_cached,
            'cache_key': analysis_cache_key,
            'status': 'SUCCESS' if business_intelligence_response.success else 'FAIL'
        }
        
        # Step 4: Real-Time Capability Validation
        print('\n⚡ Step 4: Real-Time Capability Validation...')
        step4_start = time.time()
        
        # Test real-time data retrieval and processing speed
        realtime_tests = {
            'cache_retrieval_speed': 0,
            'data_processing_speed': 0,
            'analysis_generation_speed': 0,
            'end_to_end_speed': 0
        }
        
        if redis_functional and market_data_cache_key:
            # Test cache retrieval speed
            cache_start = time.time()
            cached_data = r.get(market_data_cache_key)
            realtime_tests['cache_retrieval_speed'] = time.time() - cache_start
            
            # Test data processing speed
            process_start = time.time()
            if cached_data:
                parsed_data = json.loads(cached_data)
                # Simulate data processing
                processed_insights = {
                    'total_products': parsed_data.get('total_products_analyzed', 0),
                    'market_segments': len([k for k in parsed_data.keys() if k not in ['collection_timestamp', 'total_products_analyzed']]),
                    'processing_timestamp': datetime.now().isoformat()
                }
            realtime_tests['data_processing_speed'] = time.time() - process_start
        
        # Test quick analysis generation
        quick_analysis_start = time.time()
        quick_analysis = await ai_client.generate_text(
            'Provide a 2-sentence market summary for camera and electronics products.',
            'You are a business analyst. Be concise and actionable.'
        )
        realtime_tests['analysis_generation_speed'] = time.time() - quick_analysis_start
        
        # Calculate end-to-end speed
        realtime_tests['end_to_end_speed'] = (
            realtime_tests['cache_retrieval_speed'] + 
            realtime_tests['data_processing_speed'] + 
            realtime_tests['analysis_generation_speed']
        )
        
        # Determine real-time capability
        realtime_capable = realtime_tests['end_to_end_speed'] < 15.0  # Under 15 seconds
        
        step4_time = time.time() - step4_start
        
        results['business_intelligence_tests']['realtime_capabilities'] = {
            'execution_time': step4_time,
            'performance_metrics': realtime_tests,
            'realtime_capable': realtime_capable,
            'cache_retrieval_under_1s': realtime_tests['cache_retrieval_speed'] < 1.0,
            'analysis_under_10s': realtime_tests['analysis_generation_speed'] < 10.0,
            'end_to_end_under_15s': realtime_tests['end_to_end_speed'] < 15.0,
            'quick_analysis_successful': quick_analysis.success,
            'status': 'SUCCESS' if realtime_capable else 'PARTIAL'
        }
        
        # Step 5: Business Intelligence Test Summary
        print('\n📈 Step 5: Business Intelligence Test Summary...')
        
        total_test_time = step1_time + step2_time + step3_time + step4_time
        total_ai_cost = business_intelligence_response.cost_estimate + quick_analysis.cost_estimate
        
        # Calculate overall success metrics
        test_statuses = [
            results['business_intelligence_tests']['redis_infrastructure']['status'],
            results['business_intelligence_tests']['market_data_collection']['status'],
            results['business_intelligence_tests']['ai_analysis']['status'],
            results['business_intelligence_tests']['realtime_capabilities']['status']
        ]
        
        successful_tests = sum(1 for status in test_statuses if status == 'SUCCESS')
        partial_tests = sum(1 for status in test_statuses if status == 'PARTIAL')
        
        overall_success_rate = (successful_tests + (partial_tests * 0.5)) / len(test_statuses) * 100
        
        results['intelligence_summary'] = {
            'total_execution_time': total_test_time,
            'total_ai_cost': total_ai_cost,
            'tests_completed': 4,
            'successful_tests': successful_tests,
            'partial_tests': partial_tests,
            'overall_success_rate_percent': overall_success_rate,
            'test_status': 'SUCCESS' if overall_success_rate >= 80 else 'PARTIAL',
            'production_ready': overall_success_rate >= 80,
            'redis_infrastructure_working': redis_functional,
            'market_data_processing_functional': len(camera_data) + len(electronics_data) > 0,
            'ai_analysis_working': business_intelligence_response.success,
            'realtime_capabilities_validated': realtime_capable,
            'cache_optimization_working': market_data_cached and analysis_cached
        }
        
        print(f'\n✅ Business Intelligence Test Complete: {overall_success_rate:.1f}% success rate')
        print(f'🗄️ Redis Infrastructure: {results["business_intelligence_tests"]["redis_infrastructure"]["status"]}')
        print(f'📊 Market Data Collection: {results["business_intelligence_tests"]["market_data_collection"]["status"]}')
        print(f'🧠 AI Analysis: {results["business_intelligence_tests"]["ai_analysis"]["status"]}')
        print(f'⚡ Real-Time Capabilities: {results["business_intelligence_tests"]["realtime_capabilities"]["status"]}')
        print(f'💰 Total Cost: ${total_ai_cost:.6f}')
        print(f'⏱️ Total Time: {total_test_time:.2f}s')
        
    except Exception as e:
        results['intelligence_summary'] = {
            'test_status': 'FAIL',
            'error': str(e),
            'production_ready': False
        }
        print(f'❌ Business Intelligence Test Failed: {str(e)}')
    
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    asyncio.run(test_realtime_business_intelligence())
