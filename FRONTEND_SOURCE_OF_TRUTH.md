# FlipSync Frontend Chat System Documentation
Overview
This document serves as the definitive source of truth for how the FlipSync frontend chat system is configured and operates. Backend developers should reference this to ensure proper integration and avoid communication issues.

## Architecture Overview
Core Components
ChatService (lib/core/services/chat/chat_service.dart)
Primary interface for chat functionality
Manages WebSocket connections and message routing
Handles authentication and session management
WebSocketClient (lib/core/websocket/websocket_client.dart)
Low-level WebSocket connection management
Handles connection state, reconnection, and heartbeat
ChatBloc (lib/features/chat/presentation/bloc/chat_bloc.dart)
State management for chat UI
Processes chat events and manages UI state
ChatScreen (lib/features/chat/presentation/screens/chat_screen.dart)
Main chat interface
Handles user interactions and message display
## WebSocket Communication Protocol
Connection Establishment
Frontend Behavior:

Connects to: ws://10.0.2.2:8001/api/v1/ws/chat/{conversation_id}?token={jwt_token}
Default conversation ID: main
Requires valid JWT authentication token
Implements automatic reconnection with exponential backoff
Expected Backend Response:

{
  "type": "connection_established",
  "data": {
    "client_id": "client_uuid",
    "server_time": "2025-06-05T17:12:54.120685+00:00",
    "heartbeat_interval": 30,
    "heartbeat_timeout": 120
  }
}

## Message Format Standards
Outgoing Messages (Frontend → Backend)
User Message Structure:

{
  "type": "message",
  "conversation_id": "main",
  "data": {
    "id": "message_uuid",
    "content": "user message text",
    "sender": "user",
    "timestamp": "2025-06-05T17:12:56.046632+00:00"
  }
}

## Field Requirements:

agent_type: Should be null for user messages
thread_id: Should be null for new conversations
parent_id: Should be null unless replying to specific message
sender: Always "user" for user-generated messages

## Incoming Messages (Backend → Frontend)
Message Echo (Required):

{
  "type": "message",
  "timestamp": "2025-06-05T17:12:56.049648+00:00",
  "event_id": "event_uuid",
  "conversation_id": "backend_conversation_uuid",
  "data": {
    "id": "message_uuid",
    "conversation_id": "backend_conversation_uuid",
    "content": "hello",
    "sender": "user",
    "agent_type": null,
    "timestamp": "2025-06-05T17:12:56.046632+00:00",
    "thread_id": null,
    "parent_id": null,
    "status": "sent",
    "metadata": {
      "client_id": "client_uuid",
      "user_id": "test@example.com",
      "created_via": "websocket"
    }
  }
}

## AI Response Structure:

{
  "type": "message",
  "timestamp": "2025-06-05T17:12:58.000000+00:00",
  "event_id": "event_uuid",
  "conversation_id": "backend_conversation_uuid",
  "data": {
    "id": "response_uuid",
    "content": "AI response text",
    "sender": "agent",
    "agent_type": "assistant",
    "timestamp": "2025-06-05T17:12:58.000000+00:00",
    "thread_id": null,
    "parent_id": "original_message_id",
    "metadata": {
      "created_via": "websocket",
      "model": "gemma3:4b"
    }
  }
}

## Typing Indicator:

{
  "type": "typing",
  "timestamp": "2025-06-05T17:12:56.054927+00:00",
  "event_id": "event_uuid",
  "conversation_id": "backend_conversation_uuid",
  "data": {
    "user_id": null,
    "agent_type": "assistant",
    "is_typing": true,
    "conversation_id": "backend_conversation_uuid"
  }
}

## Heartbeat Protocol
Frontend Behavior:

Responds to ping messages with pong
Maintains connection health
Implements reconnection on heartbeat failure
Ping Message (Backend → Frontend):

{
  "type": "ping",
  "timestamp": 1749143574.1310425
}

Pong Response (Frontend → Backend):

{
  "type": "pong",
  "timestamp": "2025-06-05T17:12:54.131Z"
}

## Conversation ID Handling
Frontend Behavior
Default Conversation ID: "main"
Conversation ID Flexibility: Frontend accepts any conversation ID from backend
UUID Mapping: Backend can create UUID conversation IDs; frontend will accept and use them

## Backend Requirements
Echo Conversation ID: Must include conversation_id in all message responses
Consistency: Use the same conversation_id throughout the session
UUID Generation: Backend should generate proper UUIDs for conversation tracking

## Authentication Integration
Token Management
Source: JWT tokens from AuthService (lib/core/services/auth_service.dart)
Format: Bearer token passed as query parameter in WebSocket URL
Refresh: Frontend handles token refresh automatically
Retry Logic: 2-second delay retry if token not available during connection
Authentication Flow
User logs in via AuthService
JWT token stored securely
WebSocket connection established with token
Token included in all WebSocket communications
Error Handling & Fallback Behavior
WebSocket Connection Failures
Retry Mechanism: Exponential backoff (2s, 4s, 8s, etc.)
Max Attempts: Configurable (default: 5 attempts)
Fallback: HTTP API fallback if WebSocket fails completely
API Fallback Protocol
Endpoint: POST /api/v1/chat/conversations/{conversation_id}/messages

## Payload Structure:

{
  "text": "message content",
  "sender": "user",
  "agent_type": null,
  "thread_id": null,
  "parent_id": null,
  "metadata": {
    "created_via": "api",
    "message_id": "frontend_message_id",
    "timestamp": "2025-06-05T11:53:02.180128"

Expected Response:

{
  "id": "backend_message_uuid",
  "text": "message content",
  "sender": "user",
  "timestamp": "2025-06-05T16:53:04.486236+00:00",
  "agent_type": null,
  "thread_id": null,
  "parent_id": null,
  "metadata": {
    "created_via": "api"
  }
}

## Session Management
Chat Session Lifecycle
Session Start: Called on user login
Fresh Conversation: Clears history, establishes WebSocket
Message Flow: Real-time via WebSocket
Session End: Called on logout/app close
Session Clearing Behavior
Trigger: Every user login
Action: Clears local message cache
Preservation: Maintains WebSocket connection
Backend Expectation: Should clear server-side conversation history
Message State Management
Message Caching
Local Cache: Messages stored in memory during session
Duplicate Prevention: ID-based and content-based deduplication
Cache Clearing: Automatic on new session start
Message Status Tracking
Sent: Message transmitted via WebSocket/API
Delivered: Echo received from backend
Failed: Transmission failed (marked in metadata)
Agent Integration
Agent Types
assistant: Default conversational AI (Gemma3)
market: Market analysis agent
content: Content optimization agent
logistics: Shipping/logistics agent

## Agent Routing
Intent Detection: Automatic routing based on message content
Manual Selection: User can select specific agents
Handoff Messages: System messages for agent transitions
Agent Response Format

{
  "sender": "agent",
  "agent_type": "assistant|market|content|logistics",
  "content": "Agent response text",
  "metadata": {
    "model": "gemma3:4b",
    "confidence": 0.95,
    "intent": "general_query"
  }
}

## Performance Requirements
Response Time Expectations
WebSocket Connection: < 2 seconds
Message Transmission: < 100ms
Message Echo: < 500ms
AI Response: < 45 seconds (Ollama timeout)
Connection Stability
Heartbeat Interval: 30 seconds
Heartbeat Timeout: 120 seconds
Reconnection: Automatic with exponential backoff
Max Reconnection Attempts: 5
Development Configuration
Environment Settings

// Development Configuration
Environment.dev:
- API Base URL: http://10.0.2.2:8001/api/v1
- WebSocket URL: ws://10.0.2.2:8001/api/v1/ws/chat
- Logging: Enabled
- Mock Data: Disabled

Debug Logging
Frontend provides extensive debug logging for:

## WebSocket connection state
Message transmission/reception
Authentication token handling
Error conditions and retries
Backend Integration Checklist
Required Backend Endpoints
✅ WebSocket: /api/v1/ws/chat/{conversation_id}
✅ POST: /api/v1/chat/conversations/{conversation_id}/messages
✅ GET: /api/v1/chat/conversations/{conversation_id}/messages
✅ POST: /api/v1/auth/login
Required WebSocket Message Types
✅ connection_established
✅ message (echo and AI responses)
✅ typing
✅ ping/pong
✅ agent_status (optional)
Critical Backend Behaviors
Message Echo: Must echo user messages back via WebSocket
Conversation ID: Must maintain consistent conversation UUIDs
Typing Indicators: Should send typing events during AI processing
Authentication: Must validate JWT tokens in WebSocket connections
Heartbeat: Must implement ping/pong heartbeat protocol
## Common Integration Issues
Issue: "0 recipients" in Backend Logs
Cause: WebSocket client not properly connected
Solution: Ensure WebSocket connection established before message processing

Issue: Messages via API instead of WebSocket
Cause: WebSocket connection failed or authentication missing
Solution: Verify JWT token availability and WebSocket connection state

Issue: Null field values
Cause: Misunderstanding of field requirements
Solution: User messages should have null agent_type, thread_id, parent_id

Issue: Conversation ID mismatch
Cause: Frontend sends "main", backend creates UUID
Solution: Frontend accepts any conversation ID from backend

## Testing & Validation
Frontend Test Scenarios
Connection Test: WebSocket establishes successfully
Authentication Test: JWT token properly transmitted
Message Test: Messages sent via WebSocket (not API fallback)
Echo Test: User messages echoed back from backend
Typing Test: Typing indicators received and displayed
Reconnection Test: Automatic reconnection on connection loss
Expected Log Patterns

✅ WebSocket connected successfully
✅ Message sent via WebSocket only: [message_id]
📨 Received message: [content] from MessageSender.user
🔍 WEBSOCKET DEBUG: Handling typing indicator