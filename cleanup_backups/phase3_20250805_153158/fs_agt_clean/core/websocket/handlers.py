"""
WebSocket Event Handlers for FlipSync Real-time Communication
=============================================================

This module provides event handlers for processing incoming WebSocket messages
and coordinating responses with the real AI chat service.
"""
# NOTE: OrchestrationService disabled for 4+1 architecture compliance


import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import WebSocket, WebSocketDisconnect

from fs_agt_clean.core.db.database import get_database
from fs_agt_clean.core.websocket.events import (
    AutonomousAgentType,
    EventType,
    SenderType,
    WebSocketMessage,
    create_error_event,
    create_message_event,
    create_typing_event,
)
from fs_agt_clean.core.websocket.manager import ClientConnection, websocket_manager
from fs_agt_clean.database.repositories.agent_repository import AutonomousAgentRepository
from fs_agt_clean.database.repositories.chat_repository import ChatRepository
from fs_agt_clean.services.communication.chat_service import EnhancedChatService

logger = logging.getLogger(__name__)


class WebSocketEventHandler:
    """Handles WebSocket events and coordinates with backend services."""

    def __init__(self, database=None, app=None):
        self.database = database or get_database()
        self.app = app  # Store app reference for accessing real agent manager
        self.chat_repository = ChatRepository()
        self.agent_repository = AutonomousAgentRepository()
        # ✅ CRITICAL FIX: Pass app reference to chat service for Real Agent Manager access
        self.chat_service = EnhancedChatService(database=self.database, app=self.app)
        self._database_initialized = False
        self._background_tasks = set()  # Track background tasks for cleanup

        logger.info(
            "WebSocket handler initialized with real AI chat service and app reference"
        )

    async def handle_client_connection(
        self,
        websocket: WebSocket,
        client_id: str,
        conversation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Handle new client connection and maintain it until disconnection."""
        try:
            connection = await websocket_manager.connect(
                websocket=websocket,
                client_id=client_id,
                user_id=user_id,
                conversation_id=conversation_id,
            )

            # Add any additional metadata
            if metadata:
                connection.metadata.update(metadata)

            # Add subscriptions for system connections
            if metadata and metadata.get("is_system"):
                connection.subscriptions.add("system_alerts")
                connection.subscriptions.add("system_notifications")

            logger.info(f"WebSocket connection established: {client_id}")

            # Handle client messages - this will block until disconnection
            await self._handle_client_messages(connection)

        except Exception as e:
            logger.error(f"Error handling client connection {client_id}: {e}")
            raise

    async def _handle_client_messages(self, connection: ClientConnection):
        """Handle incoming messages from a client."""
        client_id = connection.client_id
        logger.info(f"🔄 Starting message handler for client {client_id}")

        try:
            while True:
                logger.info(f"🔄 Waiting for message from client {client_id}")
                # Receive message
                raw_message = await connection.websocket.receive_text()
                logger.info(
                    f"🔄 Received raw message from client {client_id}: {raw_message}"
                )

                try:
                    message_data = json.loads(raw_message)
                    logger.info(
                        f"🔄 Parsed message data from client {client_id}: {message_data}"
                    )
                    await self._process_message(connection, message_data)

                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON from client {client_id}: {e}")
                    await self._send_error(
                        connection, "INVALID_JSON", "Invalid JSON format"
                    )

                except Exception as e:
                    logger.error(
                        f"Error processing message from client {client_id}: {e}"
                    )
                    await self._send_error(connection, "PROCESSING_ERROR", str(e))

        except WebSocketDisconnect:
            logger.info(f"Client {client_id} disconnected")
            await websocket_manager.disconnect(client_id, "client_disconnect")

        except Exception as e:
            logger.error(f"Error in message handler for client {client_id}: {e}")
            await websocket_manager.disconnect(client_id, f"handler_error: {e}")

    async def _process_message(
        self, connection: ClientConnection, message_data: Dict[str, Any]
    ):
        """Process an incoming message based on its type."""
        try:
            logger.info(
                f"🔄 Processing message for client {connection.client_id}: {message_data}"
            )
            # Store original message data for subscription handling
            self._current_message_data = message_data

            # Transform message data to match WebSocketMessage structure
            # Move content and other fields into data field if they exist
            transformed_data = {
                "type": message_data.get("type", "message"),
                "conversation_id": message_data.get("conversation_id"),
                "data": {},
            }

            # Move content and other fields to data
            for key, value in message_data.items():
                if key not in ["type", "conversation_id", "timestamp", "event_id"]:
                    transformed_data["data"][key] = value

            message = WebSocketMessage(**transformed_data)
            logger.info(
                f"🔄 Created WebSocketMessage object: type={message.type}, data_keys={list(message.data.keys())}"
            )

            # Update client activity
            connection.last_ping = time.time()

            # Route message based on type
            if message.type == EventType.MESSAGE:
                logger.info(
                    f"🔄 Routing to chat message handler for client {connection.client_id}"
                )
                await self._handle_chat_message(connection, message)
            elif message.type == EventType.TYPING:
                logger.info(
                    f"🔄 Routing to typing indicator handler for client {connection.client_id}"
                )
                await self._handle_typing_indicator(connection, message)
            elif message.type == EventType.PING:
                logger.info(
                    f"🔄 Routing to ping handler for client {connection.client_id}"
                )
                await self._handle_ping(connection, message)
            elif message.type == EventType.PONG:
                logger.info(
                    f"🔄 Routing to pong handler for client {connection.client_id}"
                )
                await self._handle_pong(connection, message)
            elif message.type == EventType.MESSAGE_REACTION:
                logger.info(
                    f"🔄 Routing to message reaction handler for client {connection.client_id}"
                )
                await self._handle_message_reaction(connection, message)
            elif message.type == EventType.SUBSCRIBE:
                logger.info(
                    f"🔄 Routing to subscription handler for client {connection.client_id}"
                )
                await self._handle_subscription(connection, message)
            elif message.type == EventType.CONNECTION_ESTABLISHED:
                logger.info(
                    f"🔄 Routing to connection established handler for client {connection.client_id}"
                )
                await self._handle_connection_established(connection, message)
            elif message.type == "subscription_confirmed":
                logger.info(
                    f"🔄 Routing to subscription confirmed handler for client {connection.client_id}"
                )
                await self._handle_subscription_confirmed(connection, message)
            else:
                logger.warning(f"Unhandled message type: {message.type}")
                await self._send_error(
                    connection,
                    "UNSUPPORTED_TYPE",
                    f"Message type {message.type} not supported",
                )

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            await self._send_error(connection, "PROCESSING_ERROR", str(e))

    async def _ensure_database_initialized(self):
        """Ensure database is initialized before use."""
        if not self._database_initialized:
            try:
                # Get the current database instance from the global state
                from fs_agt_clean.core.db.database import get_database

                current_db = get_database()

                # Check if we need to update our database instance
                if (
                    current_db != self.database
                    and hasattr(current_db, "_session_factory")
                    and current_db._session_factory
                ):
                    logger.info(
                        "Updating WebSocket handler to use initialized database"
                    )
                    self.database = current_db
                    self._database_initialized = True
                    return

                # Try to initialize the current database
                if (
                    hasattr(self.database, "initialize")
                    and not self.database._session_factory
                ):
                    await self.database.initialize()
                self._database_initialized = True
                logger.info("Database initialized for WebSocket handler")
            except Exception as e:
                logger.error(f"Failed to initialize database: {e}")
                raise RuntimeError("Database not initialized")

    async def _ensure_conversation_exists(
        self, conversation_id: str, user_id: str
    ) -> str:
        """Ensure conversation exists, create if needed, and return valid UUID."""
        import uuid

        # Ensure we have a valid UUID for user_id
        valid_user_id = self._ensure_valid_user_id(user_id)

        # Check if conversation_id is already a valid UUID
        try:
            uuid.UUID(conversation_id)
            # It's a valid UUID, check if conversation exists
            async with self.database.get_session() as session:
                existing = await self.chat_repository.get_conversation(
                    session, conversation_id
                )
                if existing:
                    return conversation_id
                # UUID format but doesn't exist, create with this ID
                conversation = await self.chat_repository.create_conversation(
                    session=session,
                    user_id=valid_user_id,
                    title=f"Chat {conversation_id[:8]}",
                    metadata={
                        "created_via": "websocket",
                        "original_id": conversation_id,
                    },
                )
                return str(conversation.id)
        except ValueError:
            # Not a valid UUID, check if we already have a conversation for this user with this original_id
            async with self.database.get_session() as session:
                # First, try to find existing conversation by original_id in metadata
                existing_conversations = (
                    await self.chat_repository.get_user_conversations(
                        session, valid_user_id
                    )
                )
                for conv in existing_conversations:
                    if (
                        conv.extra_metadata
                        and conv.extra_metadata.get("original_id") == conversation_id
                        and conv.extra_metadata.get("created_via") == "websocket"
                    ):
                        logger.info(
                            f"Found existing conversation {conv.id} for original ID {conversation_id}"
                        )
                        return str(conv.id)

                # No existing conversation found, create new one
                conversation = await self.chat_repository.create_conversation(
                    session=session,
                    user_id=valid_user_id,
                    title=f"Chat {conversation_id}",
                    metadata={
                        "created_via": "websocket",
                        "original_id": conversation_id,
                        "websocket_conversation_id": conversation_id,
                    },
                )
                logger.info(
                    f"Created new conversation {conversation.id} for original ID {conversation_id}"
                )

                # CRITICAL FIX: Register conversation mapping for WebSocket routing
                from .manager import websocket_manager

                websocket_manager.register_conversation_mapping(
                    conversation_id, str(conversation.id)
                )

                return str(conversation.id)

    def _ensure_valid_user_id(self, user_id: str) -> str:
        """Ensure user_id is a valid UUID, convert if needed."""
        import uuid

        if not user_id:
            return "550e8400-e29b-41d4-a716-446655440000"  # Default user UUID

        try:
            # Check if it's already a valid UUID
            uuid.UUID(user_id)
            return user_id
        except ValueError:
            # Not a valid UUID, use default user UUID
            logger.info(f"Converting non-UUID user_id '{user_id}' to default UUID")
            return "550e8400-e29b-41d4-a716-446655440000"

    async def _update_all_clients_conversation_id(
        self, old_conversation_id: str, new_conversation_id: str
    ):
        """Update all clients connected to old_conversation_id to use new_conversation_id."""
        from .manager import websocket_manager

        # Get all clients connected to the old conversation ID
        if old_conversation_id in websocket_manager.conversation_connections:
            client_ids = list(
                websocket_manager.conversation_connections[old_conversation_id]
            )

            for client_id in client_ids:
                success = websocket_manager.update_client_conversation(
                    client_id, new_conversation_id
                )
                if success:
                    logger.info(
                        f"Updated client {client_id} conversation from {old_conversation_id} to {new_conversation_id}"
                    )
                else:
                    logger.warning(
                        f"Failed to update client {client_id} conversation ID"
                    )

            logger.info(
                f"Updated {len(client_ids)} clients from conversation {old_conversation_id} to {new_conversation_id}"
            )

    async def _handle_chat_message(
        self, connection: ClientConnection, message: WebSocketMessage
    ):
        """Handle incoming chat message."""
        try:
            logger.info(
                f"🔄 Starting chat message handling for client {connection.client_id}"
            )
            conversation_id = message.conversation_id or connection.conversation_id
            logger.info(f"🔄 Using conversation_id: {conversation_id}")

            if not conversation_id:
                logger.error(f"🔄 No conversation ID provided")
                await self._send_error(
                    connection, "NO_CONVERSATION", "No conversation ID provided"
                )
                return

            # Extract message data
            content = message.data.get("content", "")
            logger.info(f"🔄 Extracted message content: '{content}'")

            if not content.strip():
                logger.error(f"🔄 Empty message content")
                await self._send_error(
                    connection, "EMPTY_MESSAGE", "Message content cannot be empty"
                )
                return

            # Ensure database is initialized
            logger.info(f"🔄 Ensuring database is initialized")
            await self._ensure_database_initialized()

            # Ensure conversation exists (auto-create if needed)
            logger.info(f"🔄 Ensuring conversation exists for ID: {conversation_id}")
            resolved_conversation_id = await self._ensure_conversation_exists(
                conversation_id, connection.user_id
            )
            logger.info(f"🔄 Resolved conversation ID: {resolved_conversation_id}")

            # Update ALL clients connected to this conversation ID to match the resolved one
            if resolved_conversation_id != conversation_id:
                logger.info(
                    f"Updating all clients from conversation ID {conversation_id} to {resolved_conversation_id}"
                )
                await self._update_all_clients_conversation_id(
                    conversation_id, resolved_conversation_id
                )

            # Store message in database
            logger.info(f"🔄 Storing message in database")
            async with self.database.get_session() as session:
                db_message = await self.chat_repository.create_message(
                    session=session,
                    conversation_id=resolved_conversation_id,
                    content=content,
                    sender="user",
                    agent_type=None,
                    thread_id=message.data.get("thread_id"),
                    parent_id=message.data.get("parent_id"),
                    metadata={
                        "client_id": connection.client_id,
                        "user_id": connection.user_id,
                        "created_via": "websocket",
                    },
                )
            logger.info(f"🔄 Message stored with ID: {db_message.id}")

            # FIXED: Don't immediately broadcast user messages back to conversation
            # This was causing clients to receive their own message as an immediate "response"
            # UnifiedUser messages are stored in database but only AI responses are broadcast
            logger.info(
                f"🔄 UnifiedUser message stored, waiting for AI response before broadcasting"
            )

            # Trigger agent response if needed (non-blocking)
            # Use original conversation_id for agent routing, resolved_conversation_id for database
            logger.info(
                f"🔄 Triggering agent response (non-blocking) with original_id: {conversation_id}"
            )
            task = asyncio.create_task(
                self._trigger_agent_response(
                    conversation_id,
                    content,
                    connection.user_id,
                    resolved_conversation_id,
                )
            )

            # Add task to tracking set and set up cleanup
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            logger.info(f"🔄 Chat message handling completed successfully")

        except Exception as e:
            logger.error(f"Error handling chat message: {e}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            await self._send_error(connection, "MESSAGE_ERROR", str(e))

    async def _handle_typing_indicator(
        self, connection: ClientConnection, message: WebSocketMessage
    ):
        """Handle typing indicator."""
        try:
            conversation_id = message.conversation_id or connection.conversation_id
            if not conversation_id:
                return

            is_typing = message.data.get("is_typing", False)

            # Create typing event
            typing_event = create_typing_event(
                conversation_id=conversation_id,
                is_typing=is_typing,
                user_id=connection.user_id,
            )

            # Broadcast to conversation participants (excluding sender)
            clients = websocket_manager.conversation_connections.get(
                conversation_id, set()
            )
            for client_id in clients:
                if client_id != connection.client_id:
                    await websocket_manager.send_to_client(
                        client_id, typing_event.dict()
                    )

        except Exception as e:
            logger.error(f"Error handling typing indicator: {e}")

    async def _handle_ping(
        self, connection: ClientConnection, message: WebSocketMessage
    ):
        """Handle ping request and send pong response."""
        try:
            # Update client activity
            connection.last_ping = time.time()

            # Send pong response
            pong_event = {
                "type": "pong",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": message.data,  # Echo back any data from ping
            }

            await websocket_manager.send_to_client(connection.client_id, pong_event)
            logger.debug(f"Sent pong response to client {connection.client_id}")

        except Exception as e:
            logger.error(f"Error handling ping: {e}")

    async def _handle_pong(
        self, connection: ClientConnection, message: WebSocketMessage
    ):
        """Handle pong response to ping."""
        connection.last_ping = time.time()
        logger.debug(f"Received pong from client {connection.client_id}")

    async def _handle_message_reaction(
        self, connection: ClientConnection, message: WebSocketMessage
    ):
        """Handle message reaction."""
        try:
            message_id = message.data.get("message_id")
            reaction_type = message.data.get("reaction_type")
            action = message.data.get("action", "add")

            if not message_id or not reaction_type:
                await self._send_error(
                    connection,
                    "INVALID_REACTION",
                    "Missing message_id or reaction_type",
                )
                return

            if not connection.user_id:
                await self._send_error(
                    connection, "NO_USER", "UnifiedUser ID required for reactions"
                )
                return

            # Store reaction in database
            if action == "add":
                # Ensure database is initialized
                await self._ensure_database_initialized()

                async with self.database.get_session() as session:
                    await self.chat_repository.add_message_reaction(
                        session=session,
                        message_id=message_id,
                        user_id=connection.user_id,
                        reaction_type=reaction_type,
                    )

            # Broadcast reaction to conversation
            conversation_id = message.conversation_id or connection.conversation_id
            if conversation_id:
                reaction_event = {
                    "type": EventType.MESSAGE_REACTION,
                    "conversation_id": conversation_id,
                    "data": {
                        "message_id": message_id,
                        "user_id": connection.user_id,
                        "reaction_type": reaction_type,
                        "action": action,
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }

                await websocket_manager.send_to_conversation(
                    conversation_id, reaction_event
                )

        except Exception as e:
            logger.error(f"Error handling message reaction: {e}")
            await self._send_error(connection, "REACTION_ERROR", str(e))

    async def _trigger_agent_response(
        self,
        original_conversation_id: str,
        user_message: str,
        user_id: Optional[str],
        resolved_conversation_id: Optional[str] = None,
    ):
        """Trigger agent response to user message with proper agent type attribution."""
        try:
            # Use resolved_conversation_id for database operations, original for routing
            db_conversation_id = resolved_conversation_id or original_conversation_id
            routing_conversation_id = original_conversation_id

            logger.info(
                f"🔄 Starting agent response for conversation {routing_conversation_id} (DB: {db_conversation_id})"
            )

            # PHASE 2B: Check for workflow intent first (unless it's a direct agent conversation)
            if not routing_conversation_id.startswith("direct_"):
                logger.info(
                    f"🔄 Checking for workflow intent in message: '{user_message[:50]}...'"
                )
                workflow_intent = await self._detect_workflow_intent(user_message)

                if workflow_intent:
                    logger.info(
                        f"🎯 Workflow intent detected: {workflow_intent.workflow_type} (confidence: {workflow_intent.confidence:.2f})"
                    )
                    # Trigger workflow instead of single agent response
                    # Pass both original and resolved conversation IDs for proper message routing
                    await self._trigger_workflow_from_intent(
                        workflow_intent,
                        user_message,
                        user_id,
                        db_conversation_id,
                        routing_conversation_id,
                    )
                    return

                logger.info(
                    f"🔄 No workflow intent detected, proceeding with single agent response"
                )

            # Determine agent type from ORIGINAL conversation ID for proper attribution
            actual_agent_type = "assistant"  # Default
            if routing_conversation_id.startswith("direct_"):
                actual_agent_type = routing_conversation_id.replace("direct_", "")
                logger.info(
                    f"🎯 Direct agent conversation detected: {actual_agent_type}"
                )

            # Send typing indicator with correct agent type
            logger.info(f"🔄 Sending typing indicator for {actual_agent_type}")
            typing_event = create_typing_event(
                conversation_id=db_conversation_id,
                is_typing=True,
                agent_type=(
                    AutonomousAgentType(actual_agent_type)
                    if actual_agent_type != "assistant"
                    else AutonomousAgentType.ASSISTANT
                ),
            )
            await websocket_manager.send_to_conversation(
                db_conversation_id, typing_event.dict()
            )

            # Start keep-alive task to prevent client disconnection during AI processing
            keepalive_task = asyncio.create_task(
                self._send_keepalive_pings(db_conversation_id)
            )

            # Simulate processing delay
            logger.info(f"🔄 Processing delay...")
            await asyncio.sleep(1)

            # Generate agent response using ORIGINAL conversation ID for routing
            logger.info(
                f"🔄 Generating AI response for message: '{user_message}' with routing_id: {routing_conversation_id}"
            )
            ai_response = await self._generate_ai_response(
                routing_conversation_id, user_message, user_id
            )
            logger.info(f"🔄 Generated AI response: '{ai_response[:100]}...'")

            # Ensure database is initialized
            logger.info(f"🔄 Ensuring database is initialized for agent response")
            await self._ensure_database_initialized()

            # Database conversation ID is already resolved, no need to call _ensure_conversation_exists again
            logger.info(
                f"🔄 Using resolved conversation ID for database: {db_conversation_id}"
            )

            # Store agent message in database with correct agent type
            logger.info(f"🔄 Storing {actual_agent_type} agent message in database")
            async with self.database.get_session() as session:
                db_message = await self.chat_repository.create_message(
                    session=session,
                    conversation_id=db_conversation_id,
                    content=ai_response,
                    sender="agent",
                    agent_type=actual_agent_type,
                    metadata={
                        "generated_by": "ai_chat_service",
                        "agent_type": actual_agent_type,
                    },
                )
            logger.info(
                f"🔄 {actual_agent_type} agent message stored with ID: {db_message.id}"
            )

            # Create and send agent message event with correct agent type
            logger.info(f"🔄 Creating {actual_agent_type} agent message event")
            message_event = create_message_event(
                conversation_id=db_conversation_id,
                message_id=str(db_message.id),
                content=ai_response,
                sender=SenderType.AGENT,
                agent_type=(
                    AutonomousAgentType(actual_agent_type)
                    if actual_agent_type != "assistant"
                    else AutonomousAgentType.ASSISTANT
                ),
            )

            logger.info(f"🔄 Sending {actual_agent_type} agent message to conversation")

            # CRITICAL DEBUG: Test if this line is reached
            logger.error(f"🚨 CRITICAL TEST: This line should appear in logs!")

            # CRITICAL DEBUG: Test WebSocket manager
            logger.error(f"🚨 WEBSOCKET MANAGER TEST: {websocket_manager}")
            logger.error(f"🚨 WEBSOCKET MANAGER TYPE: {type(websocket_manager)}")
            logger.error(f"🚨 MESSAGE EVENT: {message_event}")
            logger.error(f"🚨 DB CONVERSATION ID: '{db_conversation_id}'")

            # CRITICAL FIX: Use enhanced send_to_conversation method
            # This automatically tries both UUID and "main" conversation IDs
            logger.info(
                f"🔧 DEBUG: About to call send_to_conversation with db_conversation_id='{db_conversation_id}'"
            )
            logger.info(
                f"🔧 GRANULAR DEBUG: Line 694 reached - calling send_to_conversation"
            )
            try:
                sent_count = await websocket_manager.send_to_conversation(
                    db_conversation_id, message_event.dict()
                )
                logger.info(
                    f"🔧 DEBUG: send_to_conversation completed successfully with sent_count={sent_count}"
                )
                logger.info(
                    f"🔧 GRANULAR DEBUG: Line 700 reached - send_to_conversation successful"
                )
            except Exception as e:
                logger.error(f"🔧 DEBUG: Exception in send_to_conversation: {e}")
                import traceback

                logger.error(f"🔧 DEBUG: Full traceback: {traceback.format_exc()}")
                sent_count = 0
                logger.info(f"🔧 GRANULAR DEBUG: Line 706 reached - exception handled")

            logger.info(
                f"🔧 GRANULAR DEBUG: Line 708 reached - about to stop typing indicator"
            )
            # Stop typing indicator with correct agent type
            logger.info(f"🔄 Stopping typing indicator for {actual_agent_type}")
            typing_event = create_typing_event(
                conversation_id=db_conversation_id,
                is_typing=False,
                agent_type=(
                    AutonomousAgentType(actual_agent_type)
                    if actual_agent_type != "assistant"
                    else AutonomousAgentType.ASSISTANT
                ),
            )
            await websocket_manager.send_to_conversation(
                db_conversation_id, typing_event.dict()
            )
            logger.info(f"🔄 {actual_agent_type} agent response completed successfully")

        except Exception as e:
            logger.error(f"Error triggering agent response: {e}")
            import traceback

            logger.error(f"Full agent response traceback: {traceback.format_exc()}")
        finally:
            # Stop keep-alive task
            if "keepalive_task" in locals():
                keepalive_task.cancel()
                try:
                    await keepalive_task
                except asyncio.CancelledError:
                    pass

    async def _generate_ai_response(
        self, conversation_id: str, user_message: str, user_id: Optional[str]
    ) -> str:
        """Generate AI response with enhanced agent routing capability (Phase 2 Enhancement)."""
        try:
            logger.info(f"🤖 Generating AI response for message: '{user_message}'")
            logger.info(
                f"🔍 DEBUG: conversation_id = '{conversation_id}' (type: {type(conversation_id)})"
            )
            logger.info(
                f"🔍 DEBUG: conversation_id.startswith('direct_') = {conversation_id.startswith('direct_') if conversation_id else 'conversation_id is None'}"
            )

            # Check if this is a direct agent conversation
            if conversation_id and conversation_id.startswith("direct_"):
                agent_type = conversation_id.replace("direct_", "")
                logger.info(
                    f"🎯 DIRECT AGENT ROUTING: Detected agent_type = '{agent_type}'"
                )
                return await self._generate_direct_agent_response(
                    agent_type, user_message, user_id
                )

            # 4+1 ARCHITECTURE: Route to autonomous agents or conversational interface
            return await self._route_to_4plus1_architecture(
                user_message, conversation_id, user_id
            )

        except Exception as e:
            logger.error(
                f"🚨 WEBSOCKET CHAT ERROR: Error generating AI response: {type(e).__name__}: {str(e)}"
            )
            import traceback
            import os

            logger.error(
                f"🚨 WEBSOCKET CHAT ERROR: Full traceback: {traceback.format_exc()}"
            )

            # Enhanced error logging for WebSocket path
            logger.error(
                f"🔍 WEBSOCKET DEBUG: OpenAI API Key present: {bool(os.getenv('OPENAI_API_KEY'))}"
            )
            logger.error(
                f"🔍 WEBSOCKET DEBUG: OpenAI API Key length: {len(os.getenv('OPENAI_API_KEY', ''))}"
            )
            logger.error(f"🔍 WEBSOCKET DEBUG: Message: '{user_message}'")
            logger.error(f"🔍 WEBSOCKET DEBUG: Conversation ID: {conversation_id}")
            logger.error(f"🔍 WEBSOCKET DEBUG: User ID: {user_id}")

            # WEBSOCKET ENHANCED FALLBACK: Try OpenAI-independent response system
            logger.info(
                "🔄 WEBSOCKET ENHANCED FALLBACK: Attempting OpenAI-independent response system"
            )
            try:
                # Import the chat service to use its enhanced fallback
                from fs_agt_clean.services.communication.chat_service import ChatService

                chat_service = ChatService()
                independent_response = (
                    await chat_service._handle_openai_independent_response(
                        user_message, user_id or "websocket_user"
                    )
                )
                logger.info(
                    f"✅ WEBSOCKET ENHANCED FALLBACK: OpenAI-independent response successful: {independent_response[:100]}..."
                )
                return independent_response
            except Exception as independent_error:
                logger.error(
                    f"❌ WEBSOCKET ENHANCED FALLBACK: OpenAI-independent system failed: {type(independent_error).__name__}: {str(independent_error)}"
                )
                logger.exception(
                    "❌ WEBSOCKET ENHANCED FALLBACK: Full independent system error details:"
                )

            return "I apologize, but I'm having trouble processing your request right now. Please try again."

    async def _route_to_4plus1_architecture(
        self, user_message: str, conversation_id: str, user_id: Optional[str]
    ) -> str:
        """Route message to 4+1 architecture (4 autonomous agents + 1 conversational interface)."""
        try:
            logger.info(f"🎯 Routing to 4+1 architecture for message: '{user_message}'")

            # NEW: Try enhanced chat service first for better intent recognition and routing
            try:
                logger.info("🚀 Attempting enhanced chat service processing...")
                enhanced_response = await self.chat_service.handle_message_enhanced(
                    user_id=user_id or "websocket_user",
                    message=user_message,
                    conversation_id=conversation_id,
                    app_context="flipsync",
                    use_fast_model=True,
                )

                if enhanced_response and enhanced_response.get("response"):
                    logger.info("✅ Enhanced chat service provided response")
                    return enhanced_response["response"]
                else:
                    logger.info(
                        "⚠️ Enhanced chat service returned empty response, falling back to agent system"
                    )
            except Exception as e:
                logger.warning(
                    f"Enhanced chat service failed: {e}, falling back to agent system"
                )

            # Get real agent manager from app state
            real_agent_manager = (
                getattr(self.app.state, "real_agent_manager", None)
                if hasattr(self, "app")
                else None
            )

            if not real_agent_manager:
                logger.warning(
                    "Real agent manager not available, falling back to simple AI response"
                )
                return await self._generate_fallback_ai_response(user_message)

            # Determine which agent should handle this message based on intent
            target_agent_id = await self._determine_target_agent_from_intent(
                user_message
            )

            # Get the specific agent instance
            agent_instance = real_agent_manager.get_agent_instance(target_agent_id)

            if not agent_instance:
                logger.warning(
                    f"AutonomousAgent {target_agent_id} not available, using executive agent as fallback"
                )
                agent_instance = real_agent_manager.get_agent_instance(
                    "executive_agent"
                )

            if agent_instance:
                # Route to the real agent instance
                response = await self._send_message_to_real_agent(
                    agent_instance,
                    target_agent_id,
                    user_message,
                    conversation_id,
                    user_id,
                )
                logger.info(f"✅ Real agent {target_agent_id} response generated")
                return response
            else:
                logger.warning(
                    "No real agents available, falling back to simple AI response"
                )
                return await self._generate_fallback_ai_response(user_message)

        except Exception as e:
            logger.error(f"Error routing to real agent system: {e}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")
            return await self._generate_fallback_ai_response(user_message)

    async def _generate_direct_agent_response(
        self, agent_type: str, message: str, user_id: str
    ) -> str:
        """Generate response from specific agent for direct agent conversations (Phase 2 Enhancement)."""
        try:
            logger.info(f"🎯 Generating direct response from {agent_type} agent")

            # Get agent from orchestration service
            
            target_agent = await {"error": "OrchestrationService disabled for 4+1 architecture"}

            if target_agent:
                # Use the agent's handle_message method
                response = await target_agent.handle_message(
                    message=message,
                    user_id=user_id,
                    conversation_id=f"direct_{agent_type}",
                    context={"direct_agent_chat": True},
                )

                logger.info(
                    f"✅ Direct {agent_type} agent response generated in {response.response_time:.2f}s"
                )
                return response.content
            else:
                logger.warning(f"AutonomousAgent {agent_type} not available")
                return f"I apologize, but the {agent_type} agent is not available right now. Please try again later."

        except Exception as e:
            logger.error(
                f"Error generating direct agent response for {agent_type}: {e}"
            )
            return f"I apologize, but I'm having trouble connecting to the {agent_type} agent right now. Please try again."

    async def _determine_target_agent_from_intent(self, user_message: str) -> str:
        """Determine which of the 12 real agents should handle the message based on intent."""
        message_lower = user_message.lower().strip()

        # Intent-to-agent mapping for 4+1 architecture (4 autonomous agents only)
        intent_patterns = {
            # 4 Autonomous Agents
            "executive_agent": [
                "strategy",
                "decision",
                "plan",
                "coordinate",
                "manage",
                "executive",
                "business plan",
                "roadmap",
                "vision",
                "leadership",
                "overall",
            ],
            "market_agent": [
                "market",
                "price",
                "pricing",
                "competition",
                "competitor",
                "trend",
                "analysis",
                "forecast",
                "demand",
                "supply",
                "inventory",
                "stock",
                "how many items",
                "item count",
                "listing count",
                "my inventory",
                "my listings",
                "total items",
                "active items",
                "ebay inventory",
                "marketplace inventory",
            ],
            "content_agent": [
                "content",
                "listing",
                "description",
                "seo",
                "optimize",
                "write",
                "title",
                "keywords",
                "copy",
                "text",
            ],
            "logistics_agent": [
                "shipping",
                "warehouse",
                "fulfillment",
                "delivery",
                "supplier",
                "logistics",
            ],
            # Note: Only 4 autonomous agents in 4+1 architecture
            # All other specialized functionality is handled by these core agents
        }

        # Score each agent based on keyword matches
        agent_scores = {}
        for agent_id, keywords in intent_patterns.items():
            score = 0
            for keyword in keywords:
                if keyword in message_lower:
                    score += 1
            agent_scores[agent_id] = score

        # Find the best matching agent
        best_agent = max(agent_scores.keys(), key=lambda k: agent_scores[k])
        best_score = agent_scores[best_agent]

        # If no clear match, default to executive agent for coordination
        if best_score == 0:
            logger.info(f"No specific intent detected, routing to executive_agent")
            return "executive_agent"

        logger.info(f"Intent analysis: {best_agent} (score: {best_score})")
        return best_agent

    async def _send_message_to_real_agent(
        self,
        agent_instance,
        agent_id: str,
        message: str,
        conversation_id: str,
        user_id: Optional[str],
    ) -> str:
        """Send message to a real agent instance and get response."""
        try:
            # Check if agent has a process_message method
            if hasattr(agent_instance, "process_message"):
                response = await agent_instance.process_message(message)
                return self._extract_content_from_response(response)

            # Check if agent has a handle_message method
            elif hasattr(agent_instance, "handle_message"):
                # Call with required parameters
                response = await agent_instance.handle_message(
                    message=message,
                    user_id=user_id or "default_user",
                    conversation_id=conversation_id,
                    conversation_history=None,
                    context=None,
                )
                return self._extract_content_from_response(response)

            # For marketplace services, use appropriate methods
            elif hasattr(agent_instance, "get_health_status"):
                # This is likely a marketplace service, provide a contextual response
                health = await agent_instance.get_health_status()
                return f"I'm the {agent_id} and I'm currently {health.get('status', 'active')}. How can I help you with your marketplace operations?"

            else:
                # Fallback: generate a response based on agent type
                return await self._generate_agent_specific_response(agent_id, message)

        except Exception as e:
            logger.error(f"Error communicating with agent {agent_id}: {e}")
            return await self._generate_agent_specific_response(agent_id, message)

    def _extract_content_from_response(self, response) -> str:
        """Extract clean content from various response types."""
        try:
            # If it's already a string, return as-is
            if isinstance(response, str):
                return response

            # If it's an AutonomousAgentResponse object, extract the content
            if hasattr(response, "content"):
                content = response.content
                # Handle nested content extraction
                if hasattr(content, "content"):
                    return str(content.content)
                return str(content)

            # If it's a dict with content key
            if isinstance(response, dict) and "content" in response:
                return str(response["content"])

            # If it's a dict with message key
            if isinstance(response, dict) and "message" in response:
                return str(response["message"])

            # If it's a dict with text key
            if isinstance(response, dict) and "text" in response:
                return str(response["text"])

            # Fallback: convert to string but log warning
            logger.warning(
                f"Unknown response type {type(response)}, converting to string: {str(response)[:100]}..."
            )
            return str(response)

        except Exception as e:
            logger.error(f"Error extracting content from response: {e}")
            return str(response)

    async def _generate_agent_specific_response(
        self, agent_id: str, message: str
    ) -> str:
        """Generate a contextual response based on agent type when direct communication fails."""
        # 4+1 ARCHITECTURE: Only the 4 autonomous agents + conversational interface
        agent_responses = {
            "executive_agent": f"As your Executive Agent, I understand you're asking about: '{message}'. I'm coordinating with our specialized agents to provide you with strategic insights and actionable recommendations.",
            "market_agent": f"As your Market Agent, I'm analyzing your request: '{message}'. I can help with pricing strategies, market trends, and competitive analysis to optimize your marketplace performance.",
            "content_agent": f"As your Content Agent, I see you're interested in: '{message}'. I specialize in optimizing listings, improving SEO, and creating compelling product descriptions to boost your sales.",
            "logistics_agent": f"As your Logistics Agent, regarding your question: '{message}', I can assist with inventory management, shipping optimization, and supply chain coordination.",
            # REMOVED: All legacy specialized agents (listing_agent, advertising_agent, competitor_analyzer,
            # auto_pricing_agent, auto_listing_agent, auto_inventory_agent, trend_detector, market_analyzer)
            # These functions are now handled by the 4 autonomous agents above
        }

        return agent_responses.get(
            agent_id,
            f"I'm the {agent_id} and I'm here to help with your request: '{message}'. Let me provide you with specialized assistance.",
        )

    async def _generate_fallback_ai_response(self, user_message: str) -> str:
        """Generate a fallback AI response when real agents are not available."""
        try:
            # Use HybridLLMAdapter for intelligent routing and OpenAI reduction
            from fs_agt_clean.core.ai.hybrid_llm_adapter import HybridLLMAdapterFactory

            client = HybridLLMAdapterFactory.create_fast_client()
            response = await client.generate_response(
                prompt=user_message,
                system_prompt="You are FlipSync Assistant. Help eBay sellers with friendly, practical advice.",
            )

            return response.content

        except Exception as e:
            logger.error(f"Error generating fallback response: {e}")
            return "I'm here to help with your eBay selling needs. Could you please rephrase your question?"

    # NOTE: Removed _route_to_complex_agent method
    # Now using 4+1 architecture via _route_to_4plus1_architecture

    def _should_use_fast_model(self, message: str) -> bool:
        """Determine if we should use fast model based on message characteristics."""
        # Use fast model for simple queries to meet <100ms requirement
        message_lower = message.lower().strip()

        # Short messages typically need quick responses
        if len(message) < 50:
            return True

        # Common quick queries that benefit from fast responses
        quick_patterns = [
            "hello",
            "hi",
            "hey",
            "thanks",
            "thank you",
            "yes",
            "no",
            "ok",
            "okay",
            "sure",
            "what is",
            "how much",
            "when should",
            "can you",
            "do you",
            "will you",
            "price",
            "cost",
            "shipping",
            "fast",
        ]

        for pattern in quick_patterns:
            if pattern in message_lower:
                return True

        # Use complex model for detailed analysis requests
        complex_patterns = [
            "analyze",
            "detailed",
            "comprehensive",
            "strategy",
            "explain why",
            "compare",
            "evaluate",
            "recommend",
            "business plan",
            "market analysis",
            "competitive",
        ]

        for pattern in complex_patterns:
            if pattern in message_lower:
                return False

        # Default to fast model for real-time chat experience
        return True

    async def _detect_workflow_intent(self, user_message: str):
        """Detect if a user message should trigger a workflow."""
        try:
            from fs_agt_clean.core.workflow_intent_detector import (
                workflow_intent_detector,
            )

            return workflow_intent_detector.detect_workflow_intent(user_message)
        except Exception as e:
            logger.error(f"Error detecting workflow intent: {e}")
            return None

    async def _trigger_workflow_from_intent(
        self,
        workflow_intent,
        user_message: str,
        user_id: Optional[str],
        conversation_id: str,
        original_conversation_id: Optional[str] = None,
    ):
        """Trigger a workflow based on detected intent."""
        try:
            logger.info(f"🚀 Triggering workflow: {workflow_intent.workflow_type}")

            # Import orchestration service
            
            # Prepare workflow context with both conversation IDs for proper message routing
            workflow_context = {
                "user_message": user_message,
                "conversation_id": conversation_id,  # Resolved UUID conversation ID
                "original_conversation_id": original_conversation_id,  # Original conversation ID (e.g., "main")
                "trigger_phrases": workflow_intent.trigger_phrases,
                "confidence": workflow_intent.confidence,
                **workflow_intent.context,
            }

            # Add user_id to context if available
            if user_id:
                workflow_context["user_id"] = user_id

            # Send immediate acknowledgment to user
            acknowledgment = self._generate_workflow_acknowledgment(
                workflow_intent, user_message
            )
            await self._send_workflow_acknowledgment(acknowledgment, conversation_id)

            # Trigger the workflow (non-blocking)
            task = asyncio.create_task(
                {"error": "OrchestrationService disabled for 4+1 architecture"}
            )

            # Add task to tracking set for cleanup
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)

            logger.info(
                f"✅ Workflow {workflow_intent.workflow_type} triggered successfully"
            )

        except Exception as e:
            logger.error(f"Error triggering workflow: {e}")
            # Send error message to user
            error_message = f"I understand you want to {workflow_intent.workflow_type.replace('_', ' ')}, but I'm having trouble coordinating the agents right now. Let me try a different approach."
            await self._send_workflow_error(error_message, conversation_id)

    def _generate_workflow_acknowledgment(
        self, workflow_intent, user_message: str
    ) -> str:
        """Generate an acknowledgment message for workflow triggering."""
        workflow_descriptions = {
            "product_analysis": "I'll analyze this product with our market, content, and executive agents to give you comprehensive insights.",
            "listing_optimization": "I'm coordinating with our content and market agents to optimize your listing for better performance.",
            "decision_consensus": "Let me gather input from multiple agents to help you make the best decision.",
            "pricing_strategy": "I'll work with our market and pricing experts to develop the optimal pricing strategy.",
            "market_research": "I'm initiating comprehensive market research with our specialized analysis agents.",
        }

        base_message = workflow_descriptions.get(
            workflow_intent.workflow_type,
            f"I'm coordinating multiple agents to help with your {workflow_intent.workflow_type.replace('_', ' ')} request.",
        )

        agents_list = ", ".join(
            [
                agent.replace("_", " ").title()
                for agent in workflow_intent.participating_agents
            ]
        )

        return f"{base_message}\n\n🤝 **AutonomousAgents involved:** {agents_list}\n⏱️ **Estimated time:** 30-60 seconds\n\nI'll update you as we progress!"

    async def _send_workflow_acknowledgment(self, message: str, conversation_id: str):
        """Send workflow acknowledgment message to user."""
        try:
            # Store acknowledgment in database
            await self._ensure_database_initialized()
            async with self.database.get_session() as session:
                db_message = await self.chat_repository.create_message(
                    session=session,
                    conversation_id=conversation_id,
                    content=message,
                    sender="agent",
                    agent_type="executive",
                    metadata={
                        "message_type": "workflow_acknowledgment",
                        "generated_by": "workflow_system",
                    },
                )

            # Create and send message event
            message_event = create_message_event(
                conversation_id=conversation_id,
                message_id=str(db_message.id),
                content=message,
                sender=SenderType.AGENT,
                agent_type=AutonomousAgentType.EXECUTIVE,
            )

            await websocket_manager.send_to_conversation(
                conversation_id, message_event.dict()
            )
            logger.info("✅ Workflow acknowledgment sent")

        except Exception as e:
            logger.error(f"Error sending workflow acknowledgment: {e}")

    async def _send_workflow_error(self, message: str, conversation_id: str):
        """Send workflow error message to user."""
        try:
            # Store error message in database
            await self._ensure_database_initialized()
            async with self.database.get_session() as session:
                db_message = await self.chat_repository.create_message(
                    session=session,
                    conversation_id=conversation_id,
                    content=message,
                    sender="agent",
                    agent_type="executive",
                    metadata={
                        "message_type": "workflow_error",
                        "generated_by": "workflow_system",
                    },
                )

            # Create and send message event
            message_event = create_message_event(
                conversation_id=conversation_id,
                message_id=str(db_message.id),
                content=message,
                sender=SenderType.AGENT,
                agent_type=AutonomousAgentType.EXECUTIVE,
            )

            await websocket_manager.send_to_conversation(
                conversation_id, message_event.dict()
            )
            logger.info("✅ Workflow error message sent")

        except Exception as e:
            logger.error(f"Error sending workflow error message: {e}")

    async def _send_error(
        self, connection: ClientConnection, error_code: str, error_message: str
    ):
        """Send error message to client."""
        error_event = create_error_event(error_code, error_message)
        await websocket_manager.send_to_client(connection.client_id, error_event.dict())

    async def _send_keepalive_pings(self, conversation_id: str):
        """Send periodic keep-alive pings to prevent client disconnection during AI processing."""
        try:
            # Send keep-alive pings every 15 seconds for max 5 minutes (20 pings)
            ping_count = 0
            max_pings = 20  # 5 minutes max

            while ping_count < max_pings:
                await asyncio.sleep(15)
                ping_count += 1

                # Send ping to all clients in the conversation
                ping_event = {
                    "type": "ping",
                    "timestamp": datetime.now().isoformat(),
                    "data": {"keep_alive": True, "processing": True},
                }
                await websocket_manager.send_to_conversation(
                    conversation_id, ping_event
                )
                logger.info(
                    f"🏓 Sent keep-alive ping {ping_count}/{max_pings} to conversation {conversation_id}"
                )

            logger.info(
                f"🏓 Keep-alive task completed for conversation {conversation_id}"
            )

        except asyncio.CancelledError:
            logger.info(
                f"🏓 Keep-alive task cancelled for conversation {conversation_id}"
            )
            raise
        except Exception as e:
            logger.warning(
                f"Keep-alive task error for conversation {conversation_id}: {e}"
            )

    async def _handle_subscription(
        self, connection: ClientConnection, message: WebSocketMessage
    ):
        """Handle subscription requests for agent monitoring and system status."""
        try:
            logger.info(
                f"🔄 Processing subscription request from client {connection.client_id}"
            )

            # Extract subscription details from the original message data
            # The channel and filter are in the top-level message, not in data
            channel = (
                self._current_message_data.get("channel", "")
                if hasattr(self, "_current_message_data")
                else message.data.get("channel", "")
            )
            filter_type = (
                self._current_message_data.get("filter", "")
                if hasattr(self, "_current_message_data")
                else message.data.get("filter", "")
            )

            logger.info(
                f"📡 Subscription request - Channel: {channel}, Filter: {filter_type}"
            )

            # Send confirmation response with conversation_id for Flutter app compatibility
            response = {
                "type": "subscription_confirmed",
                "conversation_id": connection.conversation_id,  # Include conversation_id for Flutter app
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "channel": channel,
                    "filter": filter_type,
                    "status": "subscribed",
                    "message": f"Successfully subscribed to {channel}",
                },
            }

            await connection.websocket.send_text(json.dumps(response))
            logger.info(
                f"✅ Subscription confirmed for client {connection.client_id} to channel {channel}"
            )

        except Exception as e:
            logger.error(f"Error handling subscription: {e}")
            await self._send_error(connection, "SUBSCRIPTION_ERROR", str(e))

    async def _handle_connection_established(
        self, connection: ClientConnection, message: WebSocketMessage
    ):
        """Handle connection established messages."""
        try:
            logger.info(
                f"🔄 Processing connection established from client {connection.client_id}"
            )

            # Send confirmation response
            response = {
                "type": "connection_confirmed",
                "conversation_id": connection.conversation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "client_id": connection.client_id,
                    "status": "connected",
                    "message": "Connection established successfully",
                },
            }

            await connection.websocket.send_text(json.dumps(response))
            logger.info(f"✅ Connection confirmed for client {connection.client_id}")

        except Exception as e:
            logger.error(f"Error handling connection established: {e}")
            await self._send_error(connection, "CONNECTION_ERROR", str(e))

    async def _handle_subscription_confirmed(
        self, connection: ClientConnection, message: WebSocketMessage
    ):
        """Handle subscription confirmed messages."""
        try:
            logger.info(
                f"🔄 Processing subscription confirmed from client {connection.client_id}"
            )

            # This is typically sent by the server, but if received from client,
            # we can acknowledge it
            response = {
                "type": "subscription_acknowledged",
                "conversation_id": connection.conversation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data": {
                    "status": "acknowledged",
                    "message": "Subscription confirmation received",
                },
            }

            await connection.websocket.send_text(json.dumps(response))
            logger.info(
                f"✅ Subscription confirmation acknowledged for client {connection.client_id}"
            )

        except Exception as e:
            logger.error(f"Error handling subscription confirmed: {e}")
            await self._send_error(connection, "SUBSCRIPTION_CONFIRMED_ERROR", str(e))


# Global handler instance
websocket_handler = WebSocketEventHandler()


def initialize_websocket_handler(database, app=None):
    """Initialize the global WebSocket handler with the provided database and AI services."""
    global websocket_handler
    websocket_handler = WebSocketEventHandler(database=database, app=app)
    logger.info("WebSocket handler initialized with database and real AI chat service")
