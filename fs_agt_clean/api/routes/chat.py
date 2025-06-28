"""Chat API routes for FlipSync conversational interface."""

import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from pydantic import BaseModel

from fs_agt_clean.core.auth.auth_service import AuthService
from fs_agt_clean.core.db.database import get_database
from fs_agt_clean.core.websocket.events import UnifiedAgentType, SenderType
from fs_agt_clean.database.repositories.chat_repository import ChatRepository
from fs_agt_clean.services.communication.chat_service import ChatService
from fs_agt_clean.services.realtime_service import realtime_service

logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["chat"],
    responses={404: {"description": "Not found"}},
)


@router.get("/")
async def get_chat_root():
    """
    Get chat service information and available endpoints.

    Returns:
        Information about the chat service and available endpoints
    """
    return {
        "service": "chat",
        "status": "operational",
        "description": "FlipSync Chat and Conversation Service",
        "endpoints": {
            "conversations": "/api/v1/chat/conversations",
            "create_conversation": "POST /api/v1/chat/conversations",
            "get_conversation": "/api/v1/chat/conversations/{conversation_id}",
            "get_messages": "/api/v1/chat/conversations/{conversation_id}/messages",
            "send_message": "POST /api/v1/chat/conversations/{conversation_id}/messages",
            "websocket": "/api/v1/ws/chat/{conversation_id}",
        },
        "features": [
            "Real-time messaging",
            "UnifiedAgent integration",
            "WebSocket support",
            "Conversation management",
            "Message history",
        ],
        "documentation": "/docs",
    }


@router.get("")
async def get_chat_root_no_slash():
    """
    Get chat service information and available endpoints (no trailing slash).

    This endpoint handles requests to /api/v1/chat without trailing slash.

    Returns:
        Information about the chat service and available endpoints
    """
    return {
        "service": "chat",
        "status": "operational",
        "description": "FlipSync Chat and Conversation Service",
        "endpoints": {
            "conversations": "/api/v1/chat/conversations",
            "create_conversation": "POST /api/v1/chat/conversations",
            "get_conversation": "/api/v1/chat/conversations/{conversation_id}",
            "get_messages": "/api/v1/chat/conversations/{conversation_id}/messages",
            "send_message": "POST /api/v1/chat/conversations/{conversation_id}/messages",
            "websocket": "/api/v1/ws/chat/{conversation_id}",
        },
        "features": [
            "Real-time messaging",
            "UnifiedAgent integration",
            "WebSocket support",
            "Conversation management",
            "Message history",
        ],
        "documentation": "/docs",
    }


# Helper function to resolve conversation IDs
async def _resolve_conversation_id(
    conversation_id: str, chat_repository: ChatRepository, session
) -> str:
    """
    Resolve conversation ID, handling special cases and creating conversations as needed.

    Args:
        conversation_id: The conversation ID from the request (could be 'main', a UUID, or any string)
        chat_repository: Chat repository instance
        session: Database session

    Returns:
        A valid UUID string for the conversation
    """
    import uuid

    # Default user ID for API requests
    default_user_id = "550e8400-e29b-41d4-a716-446655440000"

    # Check if it's already a valid UUID
    try:
        uuid.UUID(conversation_id)
        # It's a valid UUID, check if conversation exists
        existing = await chat_repository.get_conversation(session, conversation_id)
        if existing:
            return conversation_id
        # Valid UUID format but doesn't exist, create with this ID
        conversation = await chat_repository.create_conversation(
            session=session,
            user_id=default_user_id,
            title=f"Chat {conversation_id[:8]}",
            metadata={"created_via": "api", "original_id": conversation_id},
        )
        return str(conversation.id)
    except ValueError:
        # Not a valid UUID, handle special cases or create new conversation
        if conversation_id == "main":
            # Handle special case for "main" conversation
            conversations = await chat_repository.get_user_conversations(
                session=session, user_id=default_user_id, limit=1
            )
            if conversations:
                return str(conversations[0].id)
            else:
                conversation = await chat_repository.create_conversation(
                    session=session,
                    user_id=default_user_id,
                    title="FlipSync Assistant",
                    metadata={"type": "main", "created_via": "api"},
                )
                return str(conversation.id)
        else:
            # For any other non-UUID string, create a new conversation
            conversation = await chat_repository.create_conversation(
                session=session,
                user_id=default_user_id,
                title=f"Chat {conversation_id}",
                metadata={"created_via": "api", "original_id": conversation_id},
            )
            return str(conversation.id)


# Pydantic models for request/response
class ChatMessageRequest(BaseModel):
    text: str
    sender: str = "user"
    agent_type: Optional[str] = None
    thread_id: Optional[str] = None
    parent_id: Optional[str] = None


class ChatMessageResponse(BaseModel):
    id: str
    text: str
    sender: str
    timestamp: str
    agent_type: Optional[str] = None
    thread_id: Optional[str] = None
    parent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ConversationRequest(BaseModel):
    title: Optional[str] = None


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int


# Import the enhanced WebSocket manager
from fs_agt_clean.core.websocket.manager import websocket_manager


# Dependency to get services
async def get_chat_service(request: Request) -> ChatService:
    """Get chat service from app state."""
    chat_service = getattr(request.app.state, "chat_service", None)
    if chat_service is None:
        # Fallback to creating a new instance with database from app state
        database = getattr(request.app.state, "database", None)
        if database:
            from fs_agt_clean.services.communication.chat_service import (
                EnhancedChatService,
            )

            chat_service = EnhancedChatService(database=database, app=request.app)
        else:
            raise HTTPException(status_code=500, detail="Chat service not available")
    else:
        # Ensure existing chat service has app reference for Real UnifiedAgent Manager access
        if not hasattr(chat_service, "app") or chat_service.app is None:
            chat_service.app = request.app
    return chat_service


async def get_auth_service(request: Request) -> Optional[AuthService]:
    """Get auth service from app state."""
    return getattr(request.app.state, "auth", None)


async def get_chat_repository() -> ChatRepository:
    """Get chat repository instance."""
    return ChatRepository()


async def get_database_session(request: Request):
    """Get database session from app state."""
    # Get the initialized database from app state
    database = getattr(request.app.state, "database", None)
    if database is None:
        # Fallback to global database if app state doesn't have it
        database = get_database()
        if not database._session_factory:
            raise HTTPException(status_code=500, detail="Database not available")

    async with database.get_session() as session:
        yield session


# Chat endpoints
@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationRequest,
    chat_repository: ChatRepository = Depends(get_chat_repository),
    session=Depends(get_database_session),
):
    """Create a new conversation."""
    try:
        # For now, use a default user ID - in production this would come from auth
        user_id = "550e8400-e29b-41d4-a716-446655440000"

        conversation = await chat_repository.create_conversation(
            session=session,
            user_id=user_id,
            title=request.title,
            metadata={"created_via": "api"},
        )

        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title or f"Conversation {str(conversation.id)[:8]}",
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            message_count=0,
        )
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


@router.get("/conversations", response_model=List[ConversationResponse])
async def get_conversations(
    chat_repository: ChatRepository = Depends(get_chat_repository),
    session=Depends(get_database_session),
):
    """Get all conversations for the current user."""
    try:
        # For now, use a default user ID - in production this would come from auth
        user_id = "550e8400-e29b-41d4-a716-446655440000"

        conversations = await chat_repository.get_user_conversations(
            session=session, user_id=user_id, limit=50
        )

        result = []
        for conv in conversations:
            # Get conversation stats
            stats = await chat_repository.get_conversation_stats(session, str(conv.id))

            result.append(
                ConversationResponse(
                    id=str(conv.id),
                    title=conv.title or f"Conversation {str(conv.id)[:8]}",
                    created_at=conv.created_at.isoformat(),
                    updated_at=conv.updated_at.isoformat(),
                    message_count=stats.get("message_count", 0),
                )
            )

        return result
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversations")


@router.get("/conversations/{conversation_id}", response_model=Dict[str, Any])
async def get_conversation(
    conversation_id: str,
    chat_repository: ChatRepository = Depends(get_chat_repository),
    session=Depends(get_database_session),
):
    """Get conversation details."""
    try:
        conversation = await chat_repository.get_conversation(
            session=session, conversation_id=conversation_id
        )

        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        stats = await chat_repository.get_conversation_stats(session, conversation_id)

        return {
            "id": str(conversation.id),
            "title": conversation.title or f"Conversation {str(conversation.id)[:8]}",
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
            "message_count": stats.get("message_count", 0),
            "metadata": conversation.metadata,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversation")


@router.get(
    "/conversations/{conversation_id}/messages",
    response_model=List[ChatMessageResponse],
)
async def get_conversation_messages(
    conversation_id: str,
    chat_repository: ChatRepository = Depends(get_chat_repository),
    session=Depends(get_database_session),
):
    """Get messages for a conversation."""
    try:
        # Handle special case for "main" conversation ID
        actual_conversation_id = await _resolve_conversation_id(
            conversation_id, chat_repository, session
        )

        messages = await chat_repository.get_conversation_messages(
            session=session, conversation_id=actual_conversation_id, limit=100
        )

        return [
            ChatMessageResponse(
                id=str(msg.id),
                text=msg.content,
                sender=msg.sender,
                timestamp=msg.timestamp.isoformat(),
                agent_type=msg.agent_type,
                thread_id=str(msg.thread_id) if msg.thread_id else None,
                parent_id=str(msg.parent_id) if msg.parent_id else None,
                metadata=msg.extra_metadata or {},
            )
            for msg in messages
        ]
    except Exception as e:
        logger.error(f"Error getting messages for conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messages")


@router.post(
    "/conversations/{conversation_id}/messages", response_model=ChatMessageResponse
)
async def send_message(
    request: Request,
    conversation_id: str,
    message_request: ChatMessageRequest,
    chat_repository: ChatRepository = Depends(get_chat_repository),
    chat_service: ChatService = Depends(get_chat_service),
    session=Depends(get_database_session),
):
    """Send a message in a conversation."""
    try:
        # Handle special case for "main" conversation ID
        actual_conversation_id = await _resolve_conversation_id(
            conversation_id, chat_repository, session
        )

        # Store user message in database
        user_message = await chat_repository.create_message(
            session=session,
            conversation_id=actual_conversation_id,
            content=message_request.text,
            sender=message_request.sender,
            agent_type=message_request.agent_type,
            thread_id=message_request.thread_id,
            parent_id=message_request.parent_id,
            metadata={"created_via": "api"},
        )

        # Create response object
        user_message_response = ChatMessageResponse(
            id=str(user_message.id),
            text=user_message.content,
            sender=user_message.sender,
            timestamp=user_message.timestamp.isoformat(),
            agent_type=user_message.agent_type,
            thread_id=str(user_message.thread_id) if user_message.thread_id else None,
            parent_id=str(user_message.parent_id) if user_message.parent_id else None,
            metadata=user_message.extra_metadata or {},
        )

        # Send via realtime service (handles WebSocket broadcasting)
        realtime_service_instance = getattr(request.app.state, "realtime_service", None)
        if realtime_service_instance:
            await realtime_service_instance.send_chat_message(
                conversation_id=actual_conversation_id,
                content=message_request.text,
                sender=SenderType.USER,
                user_id="550e8400-e29b-41d4-a716-446655440000",  # Default user for now
                thread_id=message_request.thread_id,
                parent_id=message_request.parent_id,
                metadata={"created_via": "api"},
                session=session,
            )

        # PHASE 2B: Check for workflow intent before processing with chat service
        asyncio.create_task(
            process_message_with_workflow_detection(
                request,
                actual_conversation_id,
                message_request.text,
                chat_service,
                chat_repository,
            )
        )

        return user_message_response
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        raise HTTPException(status_code=500, detail="Failed to send message")


async def process_message_with_workflow_detection(
    request: Request,
    conversation_id: str,
    user_message: str,
    chat_service: ChatService,
    chat_repository: ChatRepository,
):
    """Process user message with workflow intent detection (Phase 2B)."""
    try:
        # PHASE 2B: Check for workflow intent first
        logger.info(
            f"🔄 [REST API] Checking for workflow intent in message: '{user_message[:50]}...'"
        )

        try:
            from fs_agt_clean.core.workflow_intent_detector import (
                workflow_intent_detector,
            )

            workflow_intent = workflow_intent_detector.detect_workflow_intent(
                user_message
            )
        except Exception as e:
            logger.error(f"Error detecting workflow intent: {e}")
            workflow_intent = None

        if workflow_intent:
            logger.info(
                f"🎯 [REST API] Workflow intent detected: {workflow_intent.workflow_type} (confidence: {workflow_intent.confidence:.2f})"
            )
            # Trigger workflow instead of single agent response
            await trigger_workflow_from_rest_api(
                request, workflow_intent, user_message, conversation_id
            )
            return

        logger.info(
            f"🔄 [REST API] No workflow intent detected, proceeding with single agent response"
        )

        # No workflow intent detected, proceed with original enhanced processing
        await process_agent_response_enhanced(
            request, conversation_id, user_message, chat_service, chat_repository
        )

    except Exception as e:
        logger.error(f"Error in workflow detection processing: {e}")
        # Fallback to original processing
        await process_agent_response_enhanced(
            request, conversation_id, user_message, chat_service, chat_repository
        )


async def trigger_workflow_from_rest_api(
    request: Request, workflow_intent, user_message: str, conversation_id: str
):
    """Trigger a workflow from REST API based on detected intent."""
    try:
        logger.info(
            f"🚀 [REST API] Triggering workflow: {workflow_intent.workflow_type}"
        )

        # Get realtime service for sending messages
        realtime_service_instance = getattr(request.app.state, "realtime_service", None)
        if not realtime_service_instance:
            logger.warning("Realtime service not available for workflow triggering")
            return

        # Import orchestration service
        from fs_agt_clean.services.agent_orchestration import orchestration_service

        # Prepare workflow context
        workflow_context = {
            "user_message": user_message,
            "conversation_id": conversation_id,
            "trigger_phrases": workflow_intent.trigger_phrases,
            "confidence": workflow_intent.confidence,
            "triggered_via": "rest_api",
            **workflow_intent.context,
        }

        # Send immediate acknowledgment to user
        acknowledgment = generate_workflow_acknowledgment(workflow_intent, user_message)

        # Send acknowledgment via realtime service
        await realtime_service_instance.send_chat_message(
            conversation_id=conversation_id,
            content=acknowledgment,
            sender=SenderType.AGENT,
            agent_type=UnifiedAgentType.EXECUTIVE,
            metadata={
                "message_type": "workflow_acknowledgment",
                "generated_by": "workflow_system",
            },
        )

        # Trigger the workflow (non-blocking)
        asyncio.create_task(
            orchestration_service.coordinate_agents(
                workflow_type=workflow_intent.workflow_type,
                participating_agents=workflow_intent.participating_agents,
                context=workflow_context,
                user_id="user_1",  # In production, get from auth
            )
        )

        logger.info(
            f"✅ [REST API] Workflow {workflow_intent.workflow_type} triggered successfully"
        )

    except Exception as e:
        logger.error(f"Error triggering workflow from REST API: {e}")
        # Send error message to user
        error_message = f"I understand you want to {workflow_intent.workflow_type.replace('_', ' ')}, but I'm having trouble coordinating the agents right now. Let me try a different approach."

        realtime_service_instance = getattr(request.app.state, "realtime_service", None)
        if realtime_service_instance:
            await realtime_service_instance.send_chat_message(
                conversation_id=conversation_id,
                content=error_message,
                sender=SenderType.AGENT,
                agent_type=UnifiedAgentType.EXECUTIVE,
                metadata={
                    "message_type": "workflow_error",
                    "generated_by": "workflow_system",
                },
            )


def generate_workflow_acknowledgment(workflow_intent, user_message: str) -> str:
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

    return f"{base_message}\n\n🤝 **UnifiedAgents involved:** {agents_list}\n⏱️ **Estimated time:** 30-60 seconds\n\nI'll update you as we progress!"


async def process_agent_response_enhanced(
    request: Request,
    conversation_id: str,
    user_message: str,
    chat_service: ChatService,
    chat_repository: ChatRepository,
):
    """Process user message and generate agent response using enhanced realtime service."""
    try:
        # Get realtime service from app state
        realtime_service_instance = getattr(request.app.state, "realtime_service", None)
        if not realtime_service_instance:
            logger.warning(
                "Realtime service not available for agent response processing"
            )
            return

        # Send typing indicator
        await realtime_service_instance.send_typing_indicator(
            conversation_id=conversation_id,
            is_typing=True,
            agent_type=UnifiedAgentType.ASSISTANT,
        )

        # Simulate processing delay
        await asyncio.sleep(1)

        # Get response from enhanced chat service
        response = await chat_service.handle_message_enhanced(
            user_id="user_1",  # In production, get from auth
            message=user_message,
            conversation_id=conversation_id,
            app_context="flipsync_mobile",
        )

        # Send agent message via realtime service
        agent_type_str = response.get("agent_type", "assistant")
        agent_type_enum = UnifiedAgentType.ASSISTANT
        try:
            agent_type_enum = UnifiedAgentType(agent_type_str)
        except ValueError:
            pass

        await realtime_service_instance.send_chat_message(
            conversation_id=conversation_id,
            content=response.get(
                "response", "I'm here to help with your FlipSync needs!"
            ),
            sender=SenderType.AGENT,
            agent_type=agent_type_enum,
            metadata=response.get(
                "metadata", {"generated_by": "enhanced_chat_service"}
            ),
        )

        # Stop typing indicator
        await realtime_service_instance.send_typing_indicator(
            conversation_id=conversation_id,
            is_typing=False,
            agent_type=UnifiedAgentType.ASSISTANT,
        )

    except Exception as e:
        logger.error(f"Error processing agent response: {e}")


# OPTIONS handlers for CORS preflight requests









@router.options("/conversations/{conversation_id}")
async def options_conversation(conversation_id: str):
    """Handle CORS preflight for specific conversation endpoint."""
    return {"message": "OK"}


@router.options("/conversations/{conversation_id}/messages")
async def options_conversation_messages(conversation_id: str):
    """Handle CORS preflight for conversation messages endpoint."""
    return {"message": "OK"}


# REMOVED: Redundant WebSocket endpoint
# The main WebSocket endpoint is now at /api/v1/ws/chat/{conversation_id}
# This provides proper authentication and uses the enhanced WebSocket handler
#
# Previous endpoint: /conversations/{conversation_id}/ws
# New endpoint: /api/v1/ws/chat/{conversation_id} (in websocket.py)
#
# This removal eliminates confusion and ensures all WebSocket connections
# go through the proper authentication flow.
