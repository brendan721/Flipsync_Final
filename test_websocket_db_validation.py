#!/usr/bin/env python3
import sys
import asyncio
import json
import time
sys.path.append('/app')

async def test_websocket_connection():
    """Test WebSocket connectivity for agent coordination."""
    try:
        print('🔌 Testing WebSocket Connection...')
        
        # Import websockets inside the container
        import websockets
        
        # Test basic WebSocket endpoint
        uri = "ws://localhost:8000/api/v1/ws?client_id=test_client_validation"
        
        async with websockets.connect(uri) as websocket:
            print('✅ WebSocket connection established successfully')
            
            # Send test message
            test_message = {
                "type": "test",
                "message": "WebSocket validation test",
                "timestamp": time.time()
            }
            
            await websocket.send(json.dumps(test_message))
            print('📤 Test message sent')
            
            # Wait for response
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            response_data = json.loads(response)
            
            print('📥 Response received:')
            print('  Type:', response_data.get('type'))
            print('  Status:', response_data.get('status'))
            print('  Client ID:', response_data.get('client_id'))
            
            return True
            
    except Exception as e:
        print('❌ WebSocket connection failed:', str(e))
        import traceback
        traceback.print_exc()
        return False

async def test_database_connections():
    """Test database connectivity from container."""
    try:
        print('🗄️ Testing Database Connections...')
        
        # Test PostgreSQL
        try:
            import asyncpg
            conn = await asyncpg.connect(
                host='flipsync-infrastructure-postgres',
                port=5432,
                user='postgres',
                password='postgres',
                database='postgres'
            )
            await conn.close()
            print('✅ PostgreSQL connection successful')
            postgres_ok = True
        except Exception as e:
            print('❌ PostgreSQL connection failed:', str(e))
            postgres_ok = False
        
        # Test Redis
        try:
            import redis.asyncio as redis
            r = redis.Redis(host='flipsync-infrastructure-redis', port=6379, db=0)
            await r.ping()
            await r.close()
            print('✅ Redis connection successful')
            redis_ok = True
        except Exception as e:
            print('❌ Redis connection failed:', str(e))
            redis_ok = False
        
        # Test Qdrant
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get('http://flipsync-infrastructure-qdrant:6333/') as resp:
                    if resp.status == 200:
                        print('✅ Qdrant connection successful')
                        qdrant_ok = True
                    else:
                        print('❌ Qdrant connection failed: HTTP', resp.status)
                        qdrant_ok = False
        except Exception as e:
            print('❌ Qdrant connection failed:', str(e))
            qdrant_ok = False
        
        return postgres_ok and redis_ok and qdrant_ok
        
    except Exception as e:
        print('❌ Database connection test failed:', str(e))
        return False

async def main():
    print('🧪 Container Connectivity Validation Suite')
    print('=' * 50)
    
    # Test WebSocket
    websocket_result = await test_websocket_connection()
    print()
    
    # Test Databases
    database_result = await test_database_connections()
    print()
    
    overall_success = websocket_result and database_result
    print('📊 Overall Results:')
    print(f'  WebSocket: {"✅ PASS" if websocket_result else "❌ FAIL"}')
    print(f'  Databases: {"✅ PASS" if database_result else "❌ FAIL"}')
    print(f'  Overall: {"✅ PASS" if overall_success else "❌ FAIL"}')
    
    return overall_success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
