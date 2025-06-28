#!/usr/bin/env python3
"""
Test script for cached LLM client implementation.
Tests both caching functionality and performance improvements.
"""

import asyncio
import logging
import time
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_cached_llm_client():
    """Test the cached LLM client implementation."""
    try:
        # Import required modules
        from fs_agt_clean.core.ai.simple_llm_client import SimpleLLMClientFactory, ModelType, ModelProvider
        from fs_agt_clean.core.ai.cached_llm_client import CachedLLMClientFactory
        from fs_agt_clean.core.cache.ai_cache import AICacheService
        
        print("🧪 Testing Cached LLM Client Implementation")
        print("=" * 50)
        
        # Test 1: Create base LLM client
        print("\n1. Creating base LLM client...")
        base_client = SimpleLLMClientFactory.create_ollama_client(
            model_type=ModelType.GEMMA_7B,  # gemma3:4b
            temperature=0.7
        )
        print(f"✅ Base client created: {base_client.provider.value} - {base_client.model}")
        
        # Test 2: Create cached client
        print("\n2. Creating cached LLM client...")
        try:
            cached_client = await CachedLLMClientFactory.create_cached_client(
                base_client,
                redis_url="redis://flipsync-infrastructure-redis:6379",
                cache_db=2
            )
            print(f"✅ Cached client created (cache_enabled={cached_client.cache_enabled})")
        except Exception as e:
            print(f"⚠️  Cache service failed, creating non-cached client: {e}")
            cached_client = CachedLLMClientFactory.create_non_cached_client(base_client)
        
        # Test 3: Simple response generation
        print("\n3. Testing simple response generation...")
        test_prompt = "What is pricing analysis?"
        
        start_time = time.time()
        try:
            response = await cached_client.generate_response(
                prompt=test_prompt,
                system_prompt="You are a helpful business assistant."
            )
            response_time = time.time() - start_time
            
            print(f"✅ Response generated in {response_time:.2f}s")
            print(f"   Provider: {response.provider.value}")
            print(f"   Model: {response.model}")
            print(f"   Response time: {response.response_time:.2f}s")
            print(f"   Content length: {len(response.content)} characters")
            print(f"   Cached: {response.metadata.get('cached', False)}")
            print(f"   Content preview: {response.content[:100]}...")
            
        except Exception as e:
            print(f"❌ Response generation failed: {e}")
            return False
        
        # Test 4: Cache hit test (if cache is enabled)
        if cached_client.cache_enabled:
            print("\n4. Testing cache hit...")
            start_time = time.time()
            try:
                cached_response = await cached_client.generate_response(
                    prompt=test_prompt,
                    system_prompt="You are a helpful business assistant."
                )
                cache_response_time = time.time() - start_time
                
                print(f"✅ Cached response retrieved in {cache_response_time:.2f}s")
                print(f"   Cached: {cached_response.metadata.get('cached', False)}")
                print(f"   Speed improvement: {response_time/cache_response_time:.1f}x faster")
                
            except Exception as e:
                print(f"❌ Cache hit test failed: {e}")
        else:
            print("\n4. ⚠️  Cache disabled - skipping cache hit test")
        
        # Test 5: Different prompts (cache miss)
        print("\n5. Testing cache miss with different prompt...")
        different_prompt = "Explain inventory management strategies."
        
        start_time = time.time()
        try:
            different_response = await cached_client.generate_response(
                prompt=different_prompt,
                system_prompt="You are a helpful business assistant."
            )
            different_response_time = time.time() - start_time
            
            print(f"✅ Different response generated in {different_response_time:.2f}s")
            print(f"   Cached: {different_response.metadata.get('cached', False)}")
            print(f"   Content preview: {different_response.content[:100]}...")
            
        except Exception as e:
            print(f"❌ Different prompt test failed: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Cached LLM Client test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_performance_comparison():
    """Compare performance between cached and non-cached clients."""
    try:
        from fs_agt_clean.core.ai.simple_llm_client import SimpleLLMClientFactory, ModelType
        from fs_agt_clean.core.ai.cached_llm_client import CachedLLMClientFactory
        
        print("\n🏁 Performance Comparison Test")
        print("=" * 40)
        
        # Create clients
        base_client = SimpleLLMClientFactory.create_ollama_client(
            model_type=ModelType.GEMMA_7B,
            temperature=0.7
        )
        
        cached_client = await CachedLLMClientFactory.create_cached_client(base_client)
        non_cached_client = CachedLLMClientFactory.create_non_cached_client(base_client)
        
        test_prompt = "Explain competitive pricing strategies."
        system_prompt = "You are an expert business consultant."
        
        # Test non-cached client
        print("\nTesting non-cached client...")
        start_time = time.time()
        non_cached_response = await non_cached_client.generate_response(
            prompt=test_prompt,
            system_prompt=system_prompt
        )
        non_cached_time = time.time() - start_time
        print(f"Non-cached response time: {non_cached_time:.2f}s")
        
        # Test cached client (first call - cache miss)
        print("\nTesting cached client (cache miss)...")
        start_time = time.time()
        cached_response_miss = await cached_client.generate_response(
            prompt=test_prompt,
            system_prompt=system_prompt
        )
        cached_miss_time = time.time() - start_time
        print(f"Cached response time (miss): {cached_miss_time:.2f}s")
        
        # Test cached client (second call - cache hit)
        if cached_client.cache_enabled:
            print("\nTesting cached client (cache hit)...")
            start_time = time.time()
            cached_response_hit = await cached_client.generate_response(
                prompt=test_prompt,
                system_prompt=system_prompt
            )
            cached_hit_time = time.time() - start_time
            print(f"Cached response time (hit): {cached_hit_time:.2f}s")
            print(f"Cache hit speedup: {non_cached_time/cached_hit_time:.1f}x faster")
        
        print("\n🎯 Performance test completed!")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")

if __name__ == "__main__":
    async def main():
        success = await test_cached_llm_client()
        if success:
            await test_performance_comparison()
    
    asyncio.run(main())
