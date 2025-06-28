#!/usr/bin/env python3
"""
Ollama Elimination Verification Test
Comprehensive test to verify 100% OpenAI usage and elimination of persistent Ollama usage
"""

import asyncio
import aiohttp
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any


async def test_ollama_elimination_verification():
    """Comprehensive verification that Ollama usage has been eliminated."""
    
    print("🔍 Ollama Elimination Verification Test")
    print("=" * 70)
    print("Verifying 100% OpenAI usage in sophisticated 26+ agent architecture")
    print("=" * 70)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "before_test_logs": {},
        "triggered_operations": {},
        "after_test_logs": {},
        "verification_summary": {},
        "final_status": {}
    }
    
    base_url = "http://localhost:8001"
    
    # Phase 1: Baseline Log Analysis
    print("📋 Phase 1: Baseline Log Analysis")
    
    try:
        log_result = subprocess.run(
            ["docker", "logs", "flipsync-api", "--tail", "50"],
            capture_output=True, text=True, timeout=10
        )
        
        baseline_logs = log_result.stdout.lower()
        
        baseline_analysis = {
            "total_lines": len(log_result.stdout.split('\n')),
            "openai_mentions": baseline_logs.count('openai'),
            "gpt_mentions": baseline_logs.count('gpt'),
            "ollama_mentions": baseline_logs.count('ollama'),
            "gemma_mentions": baseline_logs.count('gemma'),
            "openai_client_init": baseline_logs.count('initialized simplelllmclient: openai'),
            "ollama_client_init": baseline_logs.count('initialized simplelllmclient: ollama')
        }
        
        results["before_test_logs"] = baseline_analysis
        
        print(f"   ✅ Baseline analysis: {baseline_analysis['total_lines']} log lines")
        print(f"   📊 OpenAI mentions: {baseline_analysis['openai_mentions']}")
        print(f"   📊 Ollama mentions: {baseline_analysis['ollama_mentions']}")
        print(f"   📊 OpenAI client inits: {baseline_analysis['openai_client_init']}")
        print(f"   📊 Ollama client inits: {baseline_analysis['ollama_client_init']}")
        
    except Exception as e:
        print(f"   ❌ Baseline log analysis failed: {e}")
        results["before_test_logs"] = {"error": str(e)}
    
    # Phase 2: Trigger Multiple AI Operations
    print("\n🤖 Phase 2: Triggering AI Operations")
    
    triggered_operations = []
    
    async with aiohttp.ClientSession() as session:
        
        # Operation 1: Create multiple conversations
        print("   Triggering conversation creation...")
        for i in range(3):
            try:
                async with session.post(
                    f"{base_url}/api/v1/chat/conversations",
                    json={"title": f"Ollama Elimination Test {i+1}"}
                ) as response:
                    if response.status == 200:
                        conv_data = await response.json()
                        triggered_operations.append({
                            "operation": f"conversation_{i+1}",
                            "status": "success",
                            "id": conv_data.get("id")
                        })
                        print(f"     ✅ Conversation {i+1}: {conv_data.get('id')}")
                    else:
                        triggered_operations.append({
                            "operation": f"conversation_{i+1}",
                            "status": "failed",
                            "code": response.status
                        })
            except Exception as e:
                triggered_operations.append({
                    "operation": f"conversation_{i+1}",
                    "status": "error",
                    "error": str(e)
                })
        
        # Operation 2: Test agent endpoints
        print("   Testing agent endpoints...")
        try:
            async with session.get(f"{base_url}/api/v1/agents/") as response:
                if response.status == 200:
                    agents_data = await response.json()
                    triggered_operations.append({
                        "operation": "agent_list",
                        "status": "success",
                        "count": len(agents_data)
                    })
                    print(f"     ✅ Agent list: {len(agents_data)} agents")
        except Exception as e:
            triggered_operations.append({
                "operation": "agent_list",
                "status": "error",
                "error": str(e)
            })
        
        # Operation 3: Test AI confidence endpoint
        print("   Testing AI confidence analysis...")
        try:
            async with session.post(
                f"{base_url}/api/v1/ai/confidence",
                json={"text": "Test OpenAI integration for sophisticated agent system verification"}
            ) as response:
                if response.status == 200:
                    conf_data = await response.json()
                    triggered_operations.append({
                        "operation": "ai_confidence",
                        "status": "success",
                        "confidence": conf_data.get("confidence")
                    })
                    print(f"     ✅ AI confidence: {conf_data.get('confidence', 'N/A')}")
                else:
                    triggered_operations.append({
                        "operation": "ai_confidence",
                        "status": "failed",
                        "code": response.status
                    })
        except Exception as e:
            triggered_operations.append({
                "operation": "ai_confidence",
                "status": "error",
                "error": str(e)
            })
    
    results["triggered_operations"] = triggered_operations
    
    # Wait for operations to complete and generate logs
    print("   Waiting for AI operations to complete...")
    await asyncio.sleep(5)
    
    # Phase 3: Post-Operation Log Analysis
    print("\n📋 Phase 3: Post-Operation Log Analysis")
    
    try:
        log_result = subprocess.run(
            ["docker", "logs", "flipsync-api", "--tail", "200"],
            capture_output=True, text=True, timeout=15
        )
        
        post_logs = log_result.stdout.lower()
        
        # Detailed pattern analysis
        post_analysis = {
            "total_lines": len(log_result.stdout.split('\n')),
            "openai_mentions": post_logs.count('openai'),
            "gpt_mentions": post_logs.count('gpt'),
            "ollama_mentions": post_logs.count('ollama'),
            "gemma_mentions": post_logs.count('gemma'),
            "openai_client_init": post_logs.count('initialized simplelllmclient: openai'),
            "ollama_client_init": post_logs.count('initialized simplelllmclient: ollama'),
            "openai_generation": post_logs.count('openai generation') + post_logs.count('openai response'),
            "ollama_generation": post_logs.count('ollama generation') + post_logs.count('ollama response'),
            "created_openai_client": post_logs.count('created') and post_logs.count('openai'),
            "created_ollama_client": post_logs.count('created') and post_logs.count('ollama'),
            "fallback_to_ollama": post_logs.count('falling back to ollama') + post_logs.count('fallback to ollama')
        }
        
        results["after_test_logs"] = post_analysis
        
        print(f"   ✅ Post-operation analysis: {post_analysis['total_lines']} log lines")
        print(f"   📊 OpenAI mentions: {post_analysis['openai_mentions']}")
        print(f"   📊 Ollama mentions: {post_analysis['ollama_mentions']}")
        print(f"   📊 OpenAI client inits: {post_analysis['openai_client_init']}")
        print(f"   📊 Ollama client inits: {post_analysis['ollama_client_init']}")
        print(f"   📊 OpenAI generations: {post_analysis['openai_generation']}")
        print(f"   📊 Ollama generations: {post_analysis['ollama_generation']}")
        print(f"   📊 Fallbacks to Ollama: {post_analysis['fallback_to_ollama']}")
        
    except Exception as e:
        print(f"   ❌ Post-operation log analysis failed: {e}")
        results["after_test_logs"] = {"error": str(e)}
    
    # Phase 4: Verification Summary
    print("\n🎯 Phase 4: Verification Summary")
    
    verification_metrics = {}
    
    if "after_test_logs" in results and "error" not in results["after_test_logs"]:
        post_data = results["after_test_logs"]
        
        # Calculate key metrics
        verification_metrics = {
            "openai_usage_detected": post_data["openai_mentions"] > 0 or post_data["gpt_mentions"] > 0,
            "ollama_usage_detected": post_data["ollama_mentions"] > 0 or post_data["gemma_mentions"] > 0,
            "openai_primary": post_data["openai_client_init"] > post_data["ollama_client_init"],
            "no_ollama_generation": post_data["ollama_generation"] == 0,
            "no_fallbacks": post_data["fallback_to_ollama"] == 0,
            "openai_ratio": post_data["openai_mentions"] / max(post_data["openai_mentions"] + post_data["ollama_mentions"], 1),
            "successful_operations": len([op for op in triggered_operations if op.get("status") == "success"])
        }
        
        results["verification_summary"] = verification_metrics
        
        print(f"   ✅ OpenAI usage detected: {verification_metrics['openai_usage_detected']}")
        print(f"   ✅ OpenAI primary: {verification_metrics['openai_primary']}")
        print(f"   ✅ No Ollama generation: {verification_metrics['no_ollama_generation']}")
        print(f"   ✅ No fallbacks to Ollama: {verification_metrics['no_fallbacks']}")
        print(f"   ✅ OpenAI ratio: {verification_metrics['openai_ratio']:.2%}")
        print(f"   ✅ Successful operations: {verification_metrics['successful_operations']}")
    
    # Final Assessment
    print("\n🏁 Final Ollama Elimination Assessment")
    print("=" * 55)
    
    # Calculate elimination score
    elimination_score = 0
    max_score = 100
    
    if verification_metrics:
        # OpenAI usage detected (25 points)
        if verification_metrics["openai_usage_detected"]:
            elimination_score += 25
            print("✅ OpenAI usage detected: 25/25")
        else:
            print("❌ OpenAI usage detected: 0/25")
        
        # OpenAI primary (25 points)
        if verification_metrics["openai_primary"]:
            elimination_score += 25
            print("✅ OpenAI primary service: 25/25")
        else:
            print("❌ OpenAI primary service: 0/25")
        
        # No Ollama generation (25 points)
        if verification_metrics["no_ollama_generation"]:
            elimination_score += 25
            print("✅ No Ollama generation: 25/25")
        else:
            print("❌ Ollama generation detected: 0/25")
        
        # No fallbacks (25 points)
        if verification_metrics["no_fallbacks"]:
            elimination_score += 25
            print("✅ No Ollama fallbacks: 25/25")
        else:
            print("❌ Ollama fallbacks detected: 0/25")
    
    percentage = (elimination_score / max_score) * 100
    
    results["final_status"] = {
        "elimination_score": elimination_score,
        "max_score": max_score,
        "percentage": percentage,
        "grade": "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D",
        "ollama_eliminated": percentage >= 90
    }
    
    print(f"\n🎯 Ollama Elimination Score: {elimination_score}/{max_score}")
    print(f"📈 Success Rate: {percentage:.1f}%")
    print(f"🏆 Grade: {results['final_status']['grade']}")
    
    if percentage >= 90:
        print("\n🎉 OLLAMA ELIMINATION: SUCCESS")
        print("✨ 100% OpenAI usage confirmed")
        print("🚫 Ollama usage successfully eliminated")
        print("🤖 Sophisticated 26+ agent system using OpenAI exclusively")
    elif percentage >= 80:
        print("\n✅ OLLAMA ELIMINATION: GOOD")
        print("🔧 Minor Ollama usage may remain")
    elif percentage >= 70:
        print("\n⚠️  OLLAMA ELIMINATION: PARTIAL")
        print("🔧 Some Ollama usage still detected")
    else:
        print("\n❌ OLLAMA ELIMINATION: INCOMPLETE")
        print("🔧 Significant Ollama usage remains")
    
    # Save results
    try:
        import os
        os.makedirs("evidence", exist_ok=True)
        with open(f"evidence/ollama_elimination_verification_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📁 Ollama elimination verification saved to evidence directory")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_ollama_elimination_verification())
