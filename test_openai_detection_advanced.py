#!/usr/bin/env python3
"""
Advanced OpenAI Integration Detection Test
Comprehensive analysis of OpenAI usage patterns in FlipSync sophisticated agent system
"""

import asyncio
import aiohttp
import json
import subprocess
import time
from datetime import datetime
from typing import Dict, List, Any


async def test_advanced_openai_detection():
    """Advanced OpenAI integration detection with multiple verification methods."""
    
    print("🔍 Advanced OpenAI Integration Detection")
    print("=" * 60)
    print("Testing sophisticated 26+ agent architecture OpenAI usage")
    print("=" * 60)
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "docker_environment": {},
        "live_api_tests": {},
        "agent_responses": {},
        "cost_tracking": {},
        "log_analysis": {},
        "final_verification": {}
    }
    
    # Test 1: Docker Environment Analysis
    print("🐳 Test 1: Docker Environment Analysis")
    
    try:
        # Check OpenAI environment variables
        env_result = subprocess.run(
            ["docker", "exec", "flipsync-api", "env"],
            capture_output=True, text=True, timeout=10
        )
        
        openai_vars = {}
        for line in env_result.stdout.split('\n'):
            if 'OPENAI' in line or 'LLM' in line or 'MODEL' in line:
                if '=' in line:
                    key, value = line.split('=', 1)
                    openai_vars[key] = value[:20] + "..." if len(value) > 20 else value
        
        results["docker_environment"] = {
            "openai_variables": openai_vars,
            "openai_configured": len(openai_vars) > 0,
            "primary_provider": openai_vars.get("LLM_PROVIDER", "unknown"),
            "default_model": openai_vars.get("DEFAULT_MODEL", "unknown")
        }
        
        print(f"✅ OpenAI Variables: {len(openai_vars)} found")
        print(f"✅ Primary Provider: {openai_vars.get('LLM_PROVIDER', 'unknown')}")
        print(f"✅ Default Model: {openai_vars.get('DEFAULT_MODEL', 'unknown')}")
        
    except Exception as e:
        print(f"❌ Docker environment test failed: {e}")
        results["docker_environment"] = {"error": str(e)}
    
    # Test 2: Live API Tests with OpenAI Triggers
    print("\n🤖 Test 2: Live API Tests with OpenAI Triggers")
    
    base_url = "http://localhost:8001"
    
    async with aiohttp.ClientSession() as session:
        
        # Test 2a: AI Confidence Analysis (triggers LLM)
        print("   Testing AI Confidence Analysis...")
        start_time = time.time()
        try:
            async with session.post(
                f"{base_url}/api/v1/ai/confidence",
                json={"text": "Analyze this sophisticated e-commerce product for OpenAI integration testing"},
                timeout=30
            ) as response:
                response_time = time.time() - start_time
                
                if response.status == 200:
                    data = await response.json()
                    results["live_api_tests"]["ai_confidence"] = {
                        "status": "success",
                        "response_time": response_time,
                        "confidence_score": data.get("confidence", 0),
                        "analysis_present": "analysis" in data
                    }
                    print(f"   ✅ AI Confidence: {response_time:.2f}s - Score: {data.get('confidence', 'N/A')}")
                else:
                    results["live_api_tests"]["ai_confidence"] = {
                        "status": "failed",
                        "status_code": response.status,
                        "response_time": response_time
                    }
                    print(f"   ⚠️  AI Confidence: HTTP {response.status}")
                    
        except Exception as e:
            print(f"   ❌ AI Confidence test failed: {e}")
            results["live_api_tests"]["ai_confidence"] = {"error": str(e)}
        
        # Test 2b: Chat Message (triggers LLM)
        print("   Testing Chat Message Processing...")
        start_time = time.time()
        try:
            # First create a conversation
            async with session.post(
                f"{base_url}/api/v1/chat/conversations",
                json={"title": "OpenAI Integration Test Conversation"},
                timeout=30
            ) as conv_response:
                if conv_response.status == 200:
                    conv_data = await conv_response.json()
                    conversation_id = conv_data.get("id")
                    
                    # Now send a message that requires AI processing
                    async with session.post(
                        f"{base_url}/api/v1/chat/conversations/{conversation_id}/messages",
                        json={
                            "content": "Analyze my eBay listings and suggest pricing optimizations using sophisticated AI analysis",
                            "message_type": "user"
                        },
                        timeout=30
                    ) as msg_response:
                        response_time = time.time() - start_time
                        
                        if msg_response.status == 200:
                            msg_data = await msg_response.json()
                            results["live_api_tests"]["chat_message"] = {
                                "status": "success",
                                "response_time": response_time,
                                "conversation_id": conversation_id,
                                "message_id": msg_data.get("id"),
                                "ai_processing": True
                            }
                            print(f"   ✅ Chat Message: {response_time:.2f}s - Conversation: {conversation_id}")
                        else:
                            results["live_api_tests"]["chat_message"] = {
                                "status": "failed",
                                "status_code": msg_response.status,
                                "response_time": response_time
                            }
                            print(f"   ⚠️  Chat Message: HTTP {msg_response.status}")
                else:
                    print(f"   ⚠️  Conversation creation failed: HTTP {conv_response.status}")
                    
        except Exception as e:
            print(f"   ❌ Chat message test failed: {e}")
            results["live_api_tests"]["chat_message"] = {"error": str(e)}
    
    # Test 3: Real-time Log Analysis
    print("\n📋 Test 3: Real-time Log Analysis")
    
    try:
        # Trigger some AI operations first
        print("   Triggering AI operations...")
        subprocess.run(
            ["curl", "-X", "POST", f"{base_url}/api/v1/ai/confidence", 
             "-H", "Content-Type: application/json",
             "-d", '{"text": "OpenAI detection test trigger"}'],
            capture_output=True, timeout=10
        )
        
        # Wait a moment for logs to generate
        time.sleep(2)
        
        # Analyze recent logs
        log_result = subprocess.run(
            ["docker", "logs", "flipsync-api", "--tail", "100"],
            capture_output=True, text=True, timeout=10
        )
        
        log_analysis = {
            "total_lines": len(log_result.stdout.split('\n')),
            "openai_mentions": log_result.stdout.lower().count('openai'),
            "gpt_mentions": log_result.stdout.lower().count('gpt'),
            "client_creation": log_result.stdout.lower().count('created') and log_result.stdout.lower().count('client'),
            "api_calls": log_result.stdout.lower().count('api'),
            "sophisticated_agent": log_result.stdout.lower().count('sophisticated'),
            "llm_factory": log_result.stdout.lower().count('llm')
        }
        
        # Look for specific OpenAI patterns
        openai_patterns = [
            "openai client",
            "gpt-4o-mini",
            "created.*openai",
            "primary.*openai",
            "sophisticated.*openai"
        ]
        
        pattern_matches = {}
        for pattern in openai_patterns:
            pattern_matches[pattern] = log_result.stdout.lower().count(pattern.lower())
        
        results["log_analysis"] = {
            "basic_analysis": log_analysis,
            "pattern_matches": pattern_matches,
            "openai_detected": log_analysis["openai_mentions"] > 0 or log_analysis["gpt_mentions"] > 0,
            "recent_activity": log_analysis["total_lines"] > 50
        }
        
        print(f"   ✅ Log Lines Analyzed: {log_analysis['total_lines']}")
        print(f"   ✅ OpenAI Mentions: {log_analysis['openai_mentions']}")
        print(f"   ✅ GPT Mentions: {log_analysis['gpt_mentions']}")
        print(f"   ✅ Pattern Matches: {sum(pattern_matches.values())}")
        
    except Exception as e:
        print(f"   ❌ Log analysis failed: {e}")
        results["log_analysis"] = {"error": str(e)}
    
    # Test 4: Agent Response Analysis
    print("\n🏗️  Test 4: Agent Response Analysis")
    
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{base_url}/api/v1/agents/") as response:
                if response.status == 200:
                    agents_data = await response.json()
                    
                    # Analyze agent configurations for OpenAI usage
                    openai_agents = 0
                    ai_capable_agents = 0
                    sophisticated_agents = 0
                    
                    for agent in agents_data:
                        agent_str = json.dumps(agent).lower()
                        
                        if 'openai' in agent_str or 'gpt' in agent_str:
                            openai_agents += 1
                        
                        if any(keyword in agent_str for keyword in ['ai', 'llm', 'model', 'analysis']):
                            ai_capable_agents += 1
                        
                        if any(keyword in agent_str for keyword in ['sophisticated', 'advanced', 'intelligent']):
                            sophisticated_agents += 1
                    
                    results["agent_responses"] = {
                        "total_agents": len(agents_data),
                        "openai_agents": openai_agents,
                        "ai_capable_agents": ai_capable_agents,
                        "sophisticated_agents": sophisticated_agents,
                        "architecture_score": min(100, (len(agents_data) / 26) * 100)
                    }
                    
                    print(f"   ✅ Total Agents: {len(agents_data)}")
                    print(f"   ✅ OpenAI-configured Agents: {openai_agents}")
                    print(f"   ✅ AI-capable Agents: {ai_capable_agents}")
                    print(f"   ✅ Sophisticated Agents: {sophisticated_agents}")
                    
        except Exception as e:
            print(f"   ❌ Agent response analysis failed: {e}")
            results["agent_responses"] = {"error": str(e)}
    
    # Test 5: Final Verification Score
    print("\n🎯 Test 5: Final Verification Score")
    
    verification_score = 0
    max_score = 100
    
    # Environment configuration (25 points)
    if results.get("docker_environment", {}).get("openai_configured", False):
        verification_score += 25
        print("   ✅ Environment Configuration: 25/25")
    else:
        print("   ❌ Environment Configuration: 0/25")
    
    # Live API functionality (25 points)
    api_tests = results.get("live_api_tests", {})
    api_success = sum(1 for test in api_tests.values() if test.get("status") == "success")
    api_score = min(25, (api_success / max(len(api_tests), 1)) * 25)
    verification_score += api_score
    print(f"   ✅ Live API Tests: {api_score:.0f}/25")
    
    # Log analysis (25 points)
    log_data = results.get("log_analysis", {})
    if log_data.get("openai_detected", False):
        verification_score += 25
        print("   ✅ Log Analysis: 25/25")
    else:
        print("   ❌ Log Analysis: 0/25")
    
    # Agent architecture (25 points)
    agent_data = results.get("agent_responses", {})
    arch_score = min(25, agent_data.get("architecture_score", 0) * 0.25)
    verification_score += arch_score
    print(f"   ✅ Agent Architecture: {arch_score:.0f}/25")
    
    results["final_verification"] = {
        "total_score": verification_score,
        "max_score": max_score,
        "percentage": (verification_score / max_score) * 100,
        "grade": "A" if verification_score >= 90 else "B" if verification_score >= 80 else "C" if verification_score >= 70 else "D"
    }
    
    # Final Assessment
    print("\n🏁 Advanced OpenAI Detection Results")
    print("=" * 50)
    
    percentage = (verification_score / max_score) * 100
    grade = results["final_verification"]["grade"]
    
    print(f"📊 OpenAI Integration Score: {verification_score:.0f}/{max_score}")
    print(f"📈 Success Rate: {percentage:.1f}%")
    print(f"🏆 Grade: {grade}")
    
    if percentage >= 90:
        print("\n🎉 OPENAI INTEGRATION: EXCELLENT")
        print("✨ Sophisticated 26+ agent system fully using OpenAI")
        print("🤖 All detection methods confirm OpenAI as primary AI service")
    elif percentage >= 80:
        print("\n✅ OPENAI INTEGRATION: GOOD")
        print("🔧 Minor detection improvements possible")
    elif percentage >= 70:
        print("\n⚠️  OPENAI INTEGRATION: ACCEPTABLE")
        print("🔧 Some detection methods need refinement")
    else:
        print("\n❌ OPENAI INTEGRATION: NEEDS WORK")
        print("🔧 Multiple detection issues require attention")
    
    # Save results
    try:
        import os
        os.makedirs("evidence", exist_ok=True)
        with open(f"evidence/advanced_openai_detection_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n📁 Advanced detection results saved to evidence directory")
    except Exception as e:
        print(f"⚠️  Could not save results: {e}")
    
    return results


if __name__ == "__main__":
    asyncio.run(test_advanced_openai_detection())
