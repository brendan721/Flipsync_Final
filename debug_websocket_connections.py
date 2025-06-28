#!/usr/bin/env python3
"""
Debug script to check WebSocket connections and manager state.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, '/app')

from fs_agt_clean.core.websocket.manager import websocket_manager

async def debug_websocket_connections():
    """Debug WebSocket connections and manager state."""
    print("🔍 WebSocket Connection Debug")
    print("=" * 50)
    
    try:
        # Check active connections
        active_connections = websocket_manager.active_connections
        print(f"📊 Active connections count: {len(active_connections)}")
        
        if active_connections:
            print("📋 Active connection details:")
            for client_id, connection_info in active_connections.items():
                print(f"   - Client ID: {client_id}")
                print(f"     Connection type: {type(connection_info)}")
                print(f"     Connection state: {getattr(connection_info, 'state', 'unknown')}")
        else:
            print("❌ No active connections found in websocket_manager")
        
        # Check if manager is properly initialized
        print(f"\n🔧 WebSocket Manager State:")
        print(f"   - Manager type: {type(websocket_manager)}")
        print(f"   - Has active_connections attr: {hasattr(websocket_manager, 'active_connections')}")
        print(f"   - Has broadcast method: {hasattr(websocket_manager, 'broadcast')}")
        print(f"   - Has broadcast_workflow_update method: {hasattr(websocket_manager, 'broadcast_workflow_update')}")
        
        # Test a simple broadcast
        print(f"\n🔄 Testing simple broadcast...")
        test_message = {
            "type": "test_message",
            "data": {"message": "Hello from debug script"},
            "timestamp": "2025-06-16T23:05:00.000Z"
        }
        
        sent_count = await websocket_manager.broadcast(test_message)
        print(f"✅ Simple broadcast sent to {sent_count} clients")
        
        return len(active_connections), sent_count
        
    except Exception as e:
        print(f"❌ Error debugging WebSocket connections: {e}")
        import traceback
        traceback.print_exc()
        return 0, 0

async def main():
    """Main debug function."""
    connection_count, broadcast_count = await debug_websocket_connections()
    
    print("\n" + "=" * 50)
    print("📋 DEBUG SUMMARY")
    print("=" * 50)
    print(f"🔗 Connections in manager: {connection_count}")
    print(f"📡 Broadcast recipients: {broadcast_count}")
    
    if connection_count > 0 and broadcast_count > 0:
        print("\n✅ WebSocket system appears to be working correctly!")
    elif connection_count > 0 and broadcast_count == 0:
        print("\n⚠️ Connections exist but broadcasts aren't reaching them!")
        print("   This suggests an issue with the broadcast mechanism.")
    elif connection_count == 0:
        print("\n❌ No connections found in the WebSocket manager!")
        print("   The Flutter app may not be properly connecting.")
    else:
        print("\n❓ Unexpected state - investigate further.")

if __name__ == "__main__":
    asyncio.run(main())
