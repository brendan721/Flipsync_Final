#!/usr/bin/env python3
"""
Test script to manually trigger WebSocket workflow notifications.
This will help us verify if the WebSocket workflow broadcast system is working.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, '/app')

from fs_agt_clean.core.websocket.manager import websocket_manager

async def test_workflow_notification():
    """Test sending a workflow notification via WebSocket."""
    print("🔄 Testing WebSocket workflow notification...")
    
    try:
        # Test workflow data
        workflow_id = "test-workflow-123"
        workflow_type = "test_analysis"
        status = "in_progress"
        progress = 0.75
        participating_agents = ["executive", "content"]
        current_agent = "executive"
        
        print(f"📊 Sending workflow notification:")
        print(f"   - Workflow ID: {workflow_id}")
        print(f"   - Type: {workflow_type}")
        print(f"   - Status: {status}")
        print(f"   - Progress: {progress * 100}%")
        print(f"   - Agents: {participating_agents}")
        print(f"   - Current Agent: {current_agent}")
        
        # Send the workflow notification
        sent_count = await websocket_manager.broadcast_workflow_update(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            status=status,
            progress=progress,
            participating_agents=participating_agents,
            current_agent=current_agent,
            error_message=None,
            conversation_id=None
        )
        
        print(f"✅ Workflow notification sent to {sent_count} clients")
        
        if sent_count > 0:
            print("🎉 WebSocket workflow notification system is working!")
            print("   The Flutter app should receive this update in real-time.")
        else:
            print("⚠️ No clients received the notification.")
            print("   This could mean no WebSocket clients are connected.")
        
        return sent_count > 0
        
    except Exception as e:
        print(f"❌ Error sending workflow notification: {e}")
        return False

async def test_agent_coordination_notification():
    """Test sending an agent coordination notification via WebSocket."""
    print("\n🔄 Testing WebSocket agent coordination notification...")
    
    try:
        # Test coordination data
        coordination_id = "test-coordination-456"
        coordinating_agents = ["executive", "content", "market"]
        task = "Analyze product pricing and optimize listing"
        progress = 0.60
        current_phase = "market_analysis"
        agent_statuses = {
            "executive": "coordinating",
            "content": "waiting",
            "market": "analyzing"
        }
        
        print(f"📊 Sending agent coordination notification:")
        print(f"   - Coordination ID: {coordination_id}")
        print(f"   - Task: {task}")
        print(f"   - Progress: {progress * 100}%")
        print(f"   - Current Phase: {current_phase}")
        print(f"   - Agent Statuses: {agent_statuses}")
        
        # Send the coordination notification
        sent_count = await websocket_manager.broadcast_agent_coordination(
            coordination_id=coordination_id,
            coordinating_agents=coordinating_agents,
            task=task,
            progress=progress,
            current_phase=current_phase,
            agent_statuses=agent_statuses,
            conversation_id=None
        )
        
        print(f"✅ Agent coordination notification sent to {sent_count} clients")
        
        if sent_count > 0:
            print("🎉 WebSocket agent coordination system is working!")
            print("   The Flutter app should receive this update in real-time.")
        else:
            print("⚠️ No clients received the notification.")
        
        return sent_count > 0
        
    except Exception as e:
        print(f"❌ Error sending agent coordination notification: {e}")
        return False

async def main():
    """Main test function."""
    print("🎯 WebSocket Workflow Notification Test")
    print("=" * 50)
    
    # Test workflow notifications
    workflow_success = await test_workflow_notification()
    
    # Test agent coordination notifications
    coordination_success = await test_agent_coordination_notification()
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 WEBSOCKET NOTIFICATION TEST SUMMARY")
    print("=" * 50)
    print(f"✅ Workflow notifications: {'WORKING' if workflow_success else 'NO CLIENTS'}")
    print(f"✅ Agent coordination notifications: {'WORKING' if coordination_success else 'NO CLIENTS'}")
    
    if workflow_success and coordination_success:
        print("\n🎉 WEBSOCKET SYSTEM: FULLY FUNCTIONAL!")
        print("   The Flutter app should receive real-time workflow updates.")
        print("   Check the browser console for incoming WebSocket messages.")
    elif workflow_success or coordination_success:
        print("\n⚠️ WEBSOCKET SYSTEM: PARTIALLY WORKING")
        print("   Some notifications are working, but check for issues.")
    else:
        print("\n❌ WEBSOCKET SYSTEM: NO ACTIVE CLIENTS")
        print("   Either no clients are connected or there's a connection issue.")
        print("   Make sure the Flutter app is open and connected.")

if __name__ == "__main__":
    asyncio.run(main())
