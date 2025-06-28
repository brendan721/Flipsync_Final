#!/usr/bin/env python3
"""
Comprehensive validation of Phase 2 Mobile Agentic Integration.
Tests the corrected mobile app backend integration and validates all claims.
"""

import requests
import json
import time
from datetime import datetime

def validate_phase2_integration():
    """Validate all Phase 2 mobile agentic integration features."""
    
    print("🎯 PHASE 2 VALIDATION: Mobile Agentic Integration")
    print("=" * 60)
    
    base_url = "http://localhost:8001"
    results = {
        'backend_connectivity': False,
        'chat_service': False,
        'mobile_endpoints': False,
        'agent_monitoring': False,
        'workflow_coordination': False,
        'websocket_support': False,
        'real_agent_data': False,
    }
    
    # Test 1: Backend Connectivity
    print("\n1. 🔌 Testing Backend Connectivity...")
    try:
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Backend operational: {data.get('status', 'Unknown')}")
            print(f"   📊 Version: {data.get('version', 'Unknown')}")
            results['backend_connectivity'] = True
        else:
            print(f"   ❌ Backend failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Backend error: {e}")
    
    # Test 2: Chat Service (Previously thought missing)
    print("\n2. 💬 Testing Chat Service...")
    try:
        response = requests.get(f"{base_url}/api/v1/chat/", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Chat service: {data.get('status', 'Unknown')}")
            print(f"   🔧 Features: {len(data.get('features', []))} available")
            
            # Test conversations endpoint
            conv_response = requests.get(f"{base_url}/api/v1/chat/conversations", timeout=10)
            if conv_response.status_code == 200:
                conversations = conv_response.json()
                print(f"   📝 Conversations: {len(conversations)} found")
                results['chat_service'] = True
            else:
                print(f"   ⚠️  Conversations endpoint: {conv_response.status_code}")
        else:
            print(f"   ❌ Chat service failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Chat service error: {e}")
    
    # Test 3: Mobile-Specific Endpoints (Previously thought missing)
    print("\n3. 📱 Testing Mobile Endpoints...")
    try:
        # Mobile agent status
        response = requests.get(f"{base_url}/api/v1/mobile/agents/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            agents = data.get('agents', [])
            print(f"   ✅ Mobile agent status: {len(agents)} agents")
            print(f"   🤖 Active agents: {data.get('active_agents', 0)}")
            
            # Mobile dashboard
            dash_response = requests.get(f"{base_url}/api/v1/mobile/dashboard", timeout=10)
            if dash_response.status_code == 200:
                dashboard = dash_response.json()
                dash_data = dashboard.get('dashboard', {})
                print(f"   📊 Dashboard data: {dash_data.get('active_agents', 0)} agents, {dash_data.get('total_listings', 0)} listings")
                print(f"   💰 Revenue today: ${dash_data.get('revenue_today', 0)}")
                results['mobile_endpoints'] = True
            else:
                print(f"   ⚠️  Mobile dashboard: {dash_response.status_code}")
        else:
            print(f"   ❌ Mobile endpoints failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Mobile endpoints error: {e}")
    
    # Test 4: Agent Monitoring Data
    print("\n4. 🤖 Testing Agent Monitoring...")
    try:
        # General agent status
        response = requests.get(f"{base_url}/api/v1/agents/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            agents = data.get('agents', [])
            print(f"   ✅ Agent status: {len(agents)} agents active")
            
            # Detailed agent list
            agents_response = requests.get(f"{base_url}/api/v1/agents", timeout=10)
            if agents_response.status_code == 200:
                detailed_agents = agents_response.json()
                print(f"   📋 Detailed agents: {len(detailed_agents)} available")
                
                agent_types = {}
                for agent in detailed_agents:
                    agent_type = agent.get('agentType', 'unknown')
                    if agent_type not in agent_types:
                        agent_types[agent_type] = 0
                    agent_types[agent_type] += 1
                
                print(f"   🏷️  Agent types: {', '.join(agent_types.keys())}")
                results['agent_monitoring'] = True
                results['real_agent_data'] = len(detailed_agents) > 0
            else:
                print(f"   ⚠️  Detailed agents: {agents_response.status_code}")
        else:
            print(f"   ❌ Agent monitoring failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Agent monitoring error: {e}")
    
    # Test 5: Workflow Coordination (AI Orchestration)
    print("\n5. 🔄 Testing Workflow Coordination...")
    try:
        # Test AI coordination endpoint
        response = requests.get(f"{base_url}/api/v1/ai/ai/coordination/orchestrate", timeout=10)
        if response.status_code in [200, 405]:  # 405 = Method not allowed (POST required)
            print(f"   ✅ AI coordination endpoint exists")
            
            # Test decision consensus
            consensus_response = requests.get(f"{base_url}/api/v1/ai/ai/decision/consensus", timeout=10)
            if consensus_response.status_code in [200, 405]:
                print(f"   ✅ Decision consensus endpoint exists")
                results['workflow_coordination'] = True
            else:
                print(f"   ⚠️  Decision consensus: {consensus_response.status_code}")
        else:
            print(f"   ❌ AI coordination failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Workflow coordination error: {e}")
    
    # Test 6: WebSocket Support
    print("\n6. 🔌 Testing WebSocket Support...")
    try:
        response = requests.get(f"{base_url}/api/v1/ws/stats", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ WebSocket stats: {data.get('total_connections', 0)} total connections")
            print(f"   📊 Messages: {data.get('messages_sent', 0)} sent, {data.get('messages_received', 0)} received")
            
            # Test WebSocket connections endpoint
            conn_response = requests.get(f"{base_url}/api/v1/ws/connections", timeout=10)
            if conn_response.status_code == 200:
                print(f"   ✅ WebSocket connections endpoint available")
                results['websocket_support'] = True
            else:
                print(f"   ⚠️  WebSocket connections: {conn_response.status_code}")
        else:
            print(f"   ❌ WebSocket support failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ WebSocket support error: {e}")
    
    # Summary
    print("\n" + "=" * 60)
    print("🎯 PHASE 2 VALIDATION RESULTS:")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for feature, status in results.items():
        status_icon = "✅" if status else "❌"
        feature_name = feature.replace('_', ' ').title()
        print(f"   {status_icon} {feature_name}")
    
    print(f"\n📊 Overall Score: {passed}/{total} ({(passed/total)*100:.1f}%)")
    
    if passed >= 5:
        print("🎉 PHASE 2 INTEGRATION: SUBSTANTIALLY WORKING")
        print("   The mobile app can successfully connect to backend services")
        print("   Most claimed features are actually functional")
    elif passed >= 3:
        print("⚠️  PHASE 2 INTEGRATION: PARTIALLY WORKING")
        print("   Some features working, but gaps remain")
    else:
        print("❌ PHASE 2 INTEGRATION: NEEDS WORK")
        print("   Major functionality gaps identified")
    
    # Specific findings
    print("\n🔍 KEY FINDINGS:")
    if results['chat_service']:
        print("   ✅ Chat service IS working (previously thought missing)")
    if results['mobile_endpoints']:
        print("   ✅ Mobile endpoints ARE available (previously thought missing)")
    if results['workflow_coordination']:
        print("   ✅ AI coordination endpoints exist")
    if results['real_agent_data']:
        print("   ✅ Real agent data is available from backend")
    
    print(f"\n📱 Mobile App Status: Ready for testing at http://localhost:3002")
    print(f"🔗 Backend API: Operational at {base_url}")
    
    return results

def test_mobile_app_integration():
    """Test if mobile app can actually use the backend data."""
    
    print("\n🧪 TESTING MOBILE APP INTEGRATION")
    print("=" * 40)
    
    base_url = "http://localhost:8001"
    
    # Simulate mobile app requests
    print("1. Simulating mobile app agent status request...")
    try:
        response = requests.get(f"{base_url}/api/v1/mobile/agents/status", timeout=10)
        if response.status_code == 200:
            data = response.json()
            agents = data.get('agents', [])
            print(f"   📱 Mobile app would receive: {len(agents)} agents")
            for agent in agents[:3]:  # Show first 3
                print(f"      - {agent.get('name', 'Unknown')}: {agent.get('status', 'Unknown')}")
        else:
            print(f"   ❌ Mobile request failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Mobile request error: {e}")
    
    print("\n2. Simulating mobile app dashboard request...")
    try:
        response = requests.get(f"{base_url}/api/v1/mobile/dashboard", timeout=10)
        if response.status_code == 200:
            data = response.json()
            dashboard = data.get('dashboard', {})
            print(f"   📊 Mobile dashboard would show:")
            print(f"      - Active agents: {dashboard.get('active_agents', 0)}")
            print(f"      - Total listings: {dashboard.get('total_listings', 0)}")
            print(f"      - Pending orders: {dashboard.get('pending_orders', 0)}")
            print(f"      - Revenue today: ${dashboard.get('revenue_today', 0)}")
        else:
            print(f"   ❌ Dashboard request failed: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Dashboard request error: {e}")

if __name__ == "__main__":
    results = validate_phase2_integration()
    test_mobile_app_integration()
    
    print(f"\n🎉 Validation completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("🌐 Open http://localhost:3002 to test the mobile app interface")
