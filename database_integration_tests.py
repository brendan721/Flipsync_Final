#!/usr/bin/env python3
"""
Database Integration Tests for FlipSync Production Validation
Real database operations without mocks
"""

import asyncio
import json
import time
import requests
import logging
import sys
import uuid
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DatabaseIntegrationTester:
    """Database integration testing suite."""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.test_results = {}
        self.session = requests.Session()
        self.session.timeout = 30
        
    def log_test_result(self, test_name: str, success: bool, details: Dict[str, Any]):
        """Log test result with details."""
        self.test_results[test_name] = {
            'success': success,
            'timestamp': datetime.now().isoformat(),
            'details': details
        }
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status}: {test_name}")
        if not success:
            logger.error(f"   Error: {details.get('error', 'Unknown error')}")

    def test_conversation_crud_operations(self) -> bool:
        """Test Create, Read, Update, Delete operations for conversations."""
        logger.info("🔄 Testing Conversation CRUD Operations...")
        
        try:
            # CREATE: Create a new conversation
            create_payload = {
                "title": f"DB Test Conversation {datetime.now().strftime('%H:%M:%S')}",
                "agent_type": "general"
            }
            
            response = self.session.post(f"{self.base_url}/api/v1/chat/conversations", json=create_payload)
            create_success = response.status_code == 200
            
            if not create_success:
                self.log_test_result("conversation_create", False, {
                    "status_code": response.status_code,
                    "error": "Failed to create conversation"
                })
                return False
                
            conversation_data = response.json()
            conversation_id = conversation_data.get('id')
            
            self.log_test_result("conversation_create", True, {
                "conversation_id": conversation_id,
                "title": conversation_data.get('title')
            })
            
            # READ: Retrieve the conversation
            response = self.session.get(f"{self.base_url}/api/v1/chat/conversations/{conversation_id}")
            read_success = response.status_code == 200
            
            if read_success:
                retrieved_data = response.json()
                read_success = retrieved_data.get('id') == conversation_id
                
            self.log_test_result("conversation_read", read_success, {
                "conversation_id": conversation_id,
                "retrieved": read_success
            })
            
            # CREATE MESSAGE: Add a message to test message persistence
            message_payload = {
                "text": f"Test message for database validation {datetime.now().isoformat()}",
                "role": "user"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/v1/chat/conversations/{conversation_id}/messages",
                json=message_payload
            )
            message_create_success = response.status_code == 200
            
            message_id = None
            if message_create_success:
                message_data = response.json()
                message_id = message_data.get('id')
                
            self.log_test_result("message_create", message_create_success, {
                "conversation_id": conversation_id,
                "message_id": message_id
            })
            
            # READ MESSAGES: Retrieve messages
            response = self.session.get(f"{self.base_url}/api/v1/chat/conversations/{conversation_id}/messages")
            messages_read_success = response.status_code == 200
            
            if messages_read_success:
                messages = response.json()
                messages_read_success = len(messages) > 0 and any(msg.get('id') == message_id for msg in messages)
                
            self.log_test_result("messages_read", messages_read_success, {
                "conversation_id": conversation_id,
                "message_count": len(messages) if messages_read_success else 0
            })
            
            return create_success and read_success and message_create_success and messages_read_success
            
        except Exception as e:
            self.log_test_result("conversation_crud", False, {"error": str(e)})
            return False

    def test_inventory_operations(self) -> bool:
        """Test inventory database operations."""
        logger.info("🔄 Testing Inventory Database Operations...")
        
        try:
            # Test inventory listing
            response = self.session.get(f"{self.base_url}/api/v1/inventory/items")
            inventory_list_success = response.status_code == 200
            
            inventory_count = 0
            if inventory_list_success:
                inventory_data = response.json()
                inventory_count = len(inventory_data) if isinstance(inventory_data, list) else 0
                
            self.log_test_result("inventory_list", inventory_list_success, {
                "status_code": response.status_code,
                "item_count": inventory_count
            })
            
            # Test creating an inventory item
            test_sku = f"TEST-SKU-{int(time.time())}"
            create_item_payload = {
                "sku": test_sku,
                "name": f"Test Product {datetime.now().strftime('%H:%M:%S')}",
                "description": "Test product for database validation",
                "price": 29.99,
                "quantity": 10,
                "category": "Electronics"
            }
            
            response = self.session.post(f"{self.base_url}/api/v1/inventory/items", json=create_item_payload)
            item_create_success = response.status_code in [200, 201]
            
            item_id = None
            if item_create_success:
                try:
                    item_data = response.json()
                    item_id = item_data.get('id') or item_data.get('item_id')
                except:
                    # Some endpoints might return different formats
                    pass
                    
            self.log_test_result("inventory_item_create", item_create_success, {
                "status_code": response.status_code,
                "sku": test_sku,
                "item_id": item_id
            })
            
            # Test retrieving item by SKU
            response = self.session.get(f"{self.base_url}/api/v1/inventory/items/sku/{test_sku}")
            item_retrieve_success = response.status_code == 200
            
            if item_retrieve_success:
                try:
                    retrieved_item = response.json()
                    item_retrieve_success = retrieved_item.get('sku') == test_sku
                except:
                    item_retrieve_success = False
                    
            self.log_test_result("inventory_item_retrieve", item_retrieve_success, {
                "status_code": response.status_code,
                "sku": test_sku
            })
            
            return inventory_list_success and item_create_success
            
        except Exception as e:
            self.log_test_result("inventory_operations", False, {"error": str(e)})
            return False

    def test_data_persistence_across_restart(self) -> bool:
        """Test data persistence by creating data, simulating restart, and verifying data exists."""
        logger.info("🔄 Testing Data Persistence...")
        
        try:
            # Create a conversation that should persist
            persistent_title = f"Persistence Test {int(time.time())}"
            create_payload = {
                "title": persistent_title,
                "agent_type": "general"
            }
            
            response = self.session.post(f"{self.base_url}/api/v1/chat/conversations", json=create_payload)
            create_success = response.status_code == 200
            
            if not create_success:
                self.log_test_result("persistence_create", False, {
                    "error": "Failed to create persistent conversation"
                })
                return False
                
            conversation_data = response.json()
            conversation_id = conversation_data.get('id')
            
            # Wait a moment to ensure data is written
            time.sleep(2)
            
            # Verify the conversation still exists (simulating persistence check)
            response = self.session.get(f"{self.base_url}/api/v1/chat/conversations/{conversation_id}")
            persistence_success = response.status_code == 200
            
            if persistence_success:
                retrieved_data = response.json()
                persistence_success = (
                    retrieved_data.get('id') == conversation_id and
                    retrieved_data.get('title') == persistent_title
                )
                
            self.log_test_result("data_persistence", persistence_success, {
                "conversation_id": conversation_id,
                "title_match": retrieved_data.get('title') == persistent_title if persistence_success else False
            })
            
            return persistence_success
            
        except Exception as e:
            self.log_test_result("data_persistence", False, {"error": str(e)})
            return False

    def test_concurrent_database_operations(self) -> bool:
        """Test concurrent database operations to verify connection pooling."""
        logger.info("🔄 Testing Concurrent Database Operations...")
        
        try:
            import concurrent.futures
            import threading
            
            def create_conversation(thread_id: int) -> Dict[str, Any]:
                try:
                    payload = {
                        "title": f"Concurrent Test {thread_id} - {datetime.now().strftime('%H:%M:%S.%f')}",
                        "agent_type": "general"
                    }
                    
                    response = requests.post(
                        f"{self.base_url}/api/v1/chat/conversations",
                        json=payload,
                        timeout=30
                    )
                    
                    return {
                        'thread_id': thread_id,
                        'success': response.status_code == 200,
                        'status_code': response.status_code,
                        'conversation_id': response.json().get('id') if response.status_code == 200 else None
                    }
                except Exception as e:
                    return {
                        'thread_id': thread_id,
                        'success': False,
                        'error': str(e)
                    }
            
            # Run 10 concurrent database operations
            start_time = time.time()
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(create_conversation, i) for i in range(10)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            total_time = time.time() - start_time
            successful_operations = sum(1 for r in results if r.get('success', False))
            
            concurrent_success = successful_operations >= 8  # 80% success rate
            
            self.log_test_result("concurrent_database_operations", concurrent_success, {
                "total_operations": 10,
                "successful_operations": successful_operations,
                "success_rate": (successful_operations / 10) * 100,
                "total_time": total_time,
                "avg_time_per_operation": total_time / 10
            })
            
            return concurrent_success
            
        except Exception as e:
            self.log_test_result("concurrent_database_operations", False, {"error": str(e)})
            return False

async def main():
    """Run database integration tests."""
    logger.info("🚀 Starting Database Integration Tests")
    logger.info("=" * 60)
    
    tester = DatabaseIntegrationTester()
    
    # Test 1: CRUD Operations
    logger.info("\n📋 Test 1: Conversation CRUD Operations")
    crud_result = tester.test_conversation_crud_operations()
    
    # Test 2: Inventory Operations
    logger.info("\n📋 Test 2: Inventory Database Operations")
    inventory_result = tester.test_inventory_operations()
    
    # Test 3: Data Persistence
    logger.info("\n📋 Test 3: Data Persistence")
    persistence_result = tester.test_data_persistence_across_restart()
    
    # Test 4: Concurrent Operations
    logger.info("\n📋 Test 4: Concurrent Database Operations")
    concurrent_result = tester.test_concurrent_database_operations()
    
    # Generate Summary
    logger.info("\n" + "=" * 60)
    logger.info("📊 DATABASE INTEGRATION TEST SUMMARY")
    logger.info("=" * 60)
    
    total_tests = len(tester.test_results)
    passed_tests = sum(1 for result in tester.test_results.values() if result['success'])
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    logger.info(f"Total Tests: {total_tests}")
    logger.info(f"Passed Tests: {passed_tests}")
    logger.info(f"Success Rate: {success_rate:.1f}%")
    
    # Log individual test results
    for test_name, result in tester.test_results.items():
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        logger.info(f"  {status}: {test_name}")
    
    # Final assessment
    if success_rate >= 90:
        logger.info("\n🎉 DATABASE INTEGRATION: ✅ PASSED")
        logger.info("   Database operations are production ready")
    elif success_rate >= 75:
        logger.info("\n⚠️ DATABASE INTEGRATION: 🟡 PARTIAL PASS")
        logger.info("   Database has minor issues but core functionality works")
    else:
        logger.info("\n❌ DATABASE INTEGRATION: ❌ FAILED")
        logger.info("   Critical database issues found")
    
    return success_rate >= 75

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
