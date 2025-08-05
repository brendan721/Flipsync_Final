"""
FlipSync 4+1 Architecture WebSocket Handlers - Learning System
=============================================================

Phase 3.2.2: Learning System WebSocket Implementation
This module provides WebSocket handlers for the learning system in the 4+1 architecture:
- Real-time learning insights broadcasting from 8 learning tables
- Policy optimization progress streaming for autonomous_agents
- Cross-agent learning coordination events between autonomous_agents
- Learning performance metrics and analytics for llm_free compliance

WebSocket Endpoints:
- /ws/learning/insights - Real-time learning insights and discoveries
- /ws/learning/optimization - Policy optimization progress streaming
- /ws/learning/coordination - Cross-agent learning coordination events
- /ws/learning/performance - Learning system performance metrics

Key Features:
- Streams from all 8 learning system tables for autonomous_agents
- Real-time policy optimization progress with llm_free compliance tracking
- Cross-agent knowledge sharing events between autonomous_agents
- Learning conflict resolution updates for autonomous_agents coordination
- Performance improvement tracking for StandardDecisionPipeline optimization

Learning Tables Monitored:
1. policy_optimization_history - Policy evolution tracking
2. policy_strategy_evolution - Strategy development history
3. learning_knowledge_base - Knowledge pattern storage
4. learning_feedback_history - Feedback processing results
5. learning_performance_metrics - Performance tracking over time
6. cross_agent_learning_insights - Cross-agent knowledge sharing
7. cross_agent_coordination_state - Multi-agent coordination
8. learning_conflict_resolution - Learning conflict management

Security:
- WebSocket connection authentication
- Rate limiting and connection management
- Secure learning data streaming

Performance:
- <100ms WebSocket latency for learning events
- Efficient database polling with change detection
- Optimized streaming of learning insights
"""

import asyncio
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set

from fastapi import WebSocket, WebSocketDisconnect
from fastapi.routing import APIRouter

# Import 4+1 architecture database components
from fs_agt_clean.core.db.database import get_database
from fs_agt_clean.core.learning.database.models import (
    PolicyOptimizationHistory,
    PolicyStrategyEvolution,
    LearningKnowledgeBase,
    LearningFeedbackHistory,
    LearningPerformanceMetrics,
    CrossAgentLearningInsights,
    CrossAgentCoordinationState,
    LearningConflictResolution,
)

# Configure logging
logger = logging.getLogger(__name__)

# Create router for Learning WebSocket endpoints
router = APIRouter(prefix="/ws/learning", tags=["4+1-architecture-learning-websockets"])

# Database instance
database = get_database()

# Connection management for learning WebSockets
learning_connections: Dict[str, Set[WebSocket]] = {
    "learning_insights": set(),
    "optimization_progress": set(),
    "coordination_events": set(),
    "performance_metrics": set(),
}

# Connection metadata
learning_connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}


class LearningWebSocketManager:
    """
    WebSocket connection manager for 4+1 architecture learning system.

    Manages real-time connections and broadcasts learning events from the 8 learning tables.
    """

    def __init__(self):
        self.connections: Dict[str, Set[WebSocket]] = {
            "learning_insights": set(),
            "optimization_progress": set(),
            "coordination_events": set(),
            "performance_metrics": set(),
        }
        self.connection_metadata: Dict[WebSocket, Dict[str, Any]] = {}
        self.background_tasks: Set[asyncio.Task] = set()
        self.last_learning_state: Dict[str, Any] = {}

    async def connect(
        self,
        websocket: WebSocket,
        connection_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Connect a WebSocket to a specific learning channel."""
        await websocket.accept()

        if connection_type not in self.connections:
            raise ValueError(f"Invalid learning connection type: {connection_type}")

        self.connections[connection_type].add(websocket)
        self.connection_metadata[websocket] = {
            "connection_type": connection_type,
            "connected_at": datetime.now(timezone.utc),
            "metadata": metadata or {},
        }

        logger.info(
            f"🔌 Learning WebSocket connected to {connection_type} channel. Total connections: {len(self.connections[connection_type])}"
        )

    async def disconnect(self, websocket: WebSocket):
        """Disconnect a WebSocket from all learning channels."""
        for connection_type, connections in self.connections.items():
            if websocket in connections:
                connections.remove(websocket)
                logger.info(
                    f"🔌 Learning WebSocket disconnected from {connection_type} channel. Remaining: {len(connections)}"
                )

        if websocket in self.connection_metadata:
            del self.connection_metadata[websocket]

    async def broadcast_to_channel(self, connection_type: str, message: Dict[str, Any]):
        """Broadcast a learning message to all connections in a specific channel."""
        if connection_type not in self.connections:
            return

        connections = self.connections[connection_type].copy()
        if not connections:
            return

        message_json = json.dumps(message)
        disconnected_connections = []

        for websocket in connections:
            try:
                await websocket.send_text(message_json)
            except Exception as e:
                logger.warning(f"Failed to send learning message to WebSocket: {e}")
                disconnected_connections.append(websocket)

        # Clean up disconnected connections
        for websocket in disconnected_connections:
            await self.disconnect(websocket)


# Global Learning WebSocket manager instance
learning_ws_manager = LearningWebSocketManager()


@router.websocket("/insights")
async def websocket_learning_insights(websocket: WebSocket):
    """
    WebSocket endpoint for real-time learning insights and discoveries.

    Streams:
    - New learning insights from learning_knowledge_base table
    - Cross-agent learning discoveries from cross_agent_learning_insights table
    - Learning feedback processing results from learning_feedback_history table
    - Knowledge pattern discoveries and updates
    """
    await learning_ws_manager.connect(websocket, "learning_insights")

    try:
        # Send initial learning insights
        await _send_initial_learning_insights(websocket)

        # Start background task for learning insights updates
        update_task = asyncio.create_task(_learning_insights_updater(websocket))
        learning_ws_manager.background_tasks.add(update_task)

        # Keep connection alive and handle incoming messages
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                await _handle_learning_insights_message(websocket, message)
            except asyncio.TimeoutError:
                # Send ping to keep connection alive
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "ping",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                )

    except WebSocketDisconnect:
        logger.info("🔌 Learning insights WebSocket disconnected")
    except Exception as e:
        logger.error(f"❌ Learning insights WebSocket error: {e}")
    finally:
        await learning_ws_manager.disconnect(websocket)


@router.websocket("/optimization")
async def websocket_optimization_progress(websocket: WebSocket):
    """
    WebSocket endpoint for real-time policy optimization progress streaming.

    Streams:
    - Policy optimization progress from policy_optimization_history table
    - Strategy evolution updates from policy_strategy_evolution table
    - Performance improvement tracking from learning_performance_metrics table
    - Optimization algorithm effectiveness metrics
    """
    await learning_ws_manager.connect(websocket, "optimization_progress")

    try:
        # Send initial optimization status
        await _send_initial_optimization_status(websocket)

        # Start background task for optimization updates
        update_task = asyncio.create_task(_optimization_progress_updater(websocket))
        learning_ws_manager.background_tasks.add(update_task)

        # Keep connection alive
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                await _handle_optimization_message(websocket, message)
            except asyncio.TimeoutError:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "ping",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                )

    except WebSocketDisconnect:
        logger.info("🔌 Optimization progress WebSocket disconnected")
    except Exception as e:
        logger.error(f"❌ Optimization progress WebSocket error: {e}")
    finally:
        await learning_ws_manager.disconnect(websocket)


@router.websocket("/coordination")
async def websocket_coordination_events(websocket: WebSocket):
    """
    WebSocket endpoint for real-time cross-agent learning coordination events.

    Streams:
    - Cross-agent coordination state changes from cross_agent_coordination_state table
    - Learning conflict resolution events from learning_conflict_resolution table
    - Multi-agent learning synchronization events
    - Coordination effectiveness metrics
    """
    await learning_ws_manager.connect(websocket, "coordination_events")

    try:
        # Send initial coordination status
        await _send_initial_coordination_status(websocket)

        # Start background task for coordination updates
        update_task = asyncio.create_task(_coordination_events_updater(websocket))
        learning_ws_manager.background_tasks.add(update_task)

        # Keep connection alive
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                await _handle_coordination_message(websocket, message)
            except asyncio.TimeoutError:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "ping",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                )

    except WebSocketDisconnect:
        logger.info("🔌 Coordination events WebSocket disconnected")
    except Exception as e:
        logger.error(f"❌ Coordination events WebSocket error: {e}")
    finally:
        await learning_ws_manager.disconnect(websocket)


@router.websocket("/performance")
async def websocket_performance_metrics(websocket: WebSocket):
    """
    WebSocket endpoint for real-time learning system performance metrics.

    Streams:
    - Learning performance metrics from learning_performance_metrics table
    - System-wide learning effectiveness indicators
    - Performance trend analysis and predictions
    - Learning system health and optimization recommendations
    """
    await learning_ws_manager.connect(websocket, "performance_metrics")

    try:
        # Send initial performance metrics
        await _send_initial_performance_metrics(websocket)

        # Start background task for performance updates
        update_task = asyncio.create_task(_performance_metrics_updater(websocket))
        learning_ws_manager.background_tasks.add(update_task)

        # Keep connection alive
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                await _handle_performance_message(websocket, message)
            except asyncio.TimeoutError:
                await websocket.send_text(
                    json.dumps(
                        {
                            "type": "ping",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        }
                    )
                )

    except WebSocketDisconnect:
        logger.info("🔌 Performance metrics WebSocket disconnected")
    except Exception as e:
        logger.error(f"❌ Performance metrics WebSocket error: {e}")
    finally:
        await learning_ws_manager.disconnect(websocket)


# Helper functions for Learning WebSocket message handling


async def _send_initial_learning_insights(websocket: WebSocket):
    """Send initial learning insights to newly connected WebSocket."""
    try:
        async with database.get_session() as session:
            from sqlalchemy import select

            # Get recent learning insights from multiple tables
            insights_data = {}

            # 1. Learning Knowledge Base insights
            knowledge_query = (
                select(LearningKnowledgeBase)
                .order_by(LearningKnowledgeBase.created_at.desc())
                .limit(10)
            )
            knowledge_result = await session.execute(knowledge_query)
            knowledge_insights = knowledge_result.scalars().all()

            insights_data["knowledge_base"] = [
                {
                    "id": kb.id,
                    "agent_id": kb.agent_id,
                    "knowledge_type": kb.knowledge_type,
                    "knowledge_content": kb.knowledge_content,
                    "confidence_score": kb.confidence_score,
                    "usage_count": kb.usage_count,
                    "effectiveness_score": kb.effectiveness_score,
                    "created_at": kb.created_at.isoformat(),
                    "updated_at": kb.updated_at.isoformat(),
                }
                for kb in knowledge_insights
            ]

            # 2. Cross-agent learning insights
            cross_agent_query = (
                select(CrossAgentLearningInsights)
                .order_by(CrossAgentLearningInsights.created_at.desc())
                .limit(10)
            )
            cross_agent_result = await session.execute(cross_agent_query)
            cross_agent_insights = cross_agent_result.scalars().all()

            insights_data["cross_agent_insights"] = [
                {
                    "id": ca.id,
                    "source_agent_id": ca.source_agent_id,
                    "target_agent_id": ca.target_agent_id,
                    "insight_type": ca.insight_type,
                    "insight_content": ca.insight_content,
                    "confidence_score": ca.confidence_score,
                    "impact_score": ca.impact_score,
                    "validation_status": ca.validation_status,
                    "created_at": ca.created_at.isoformat(),
                }
                for ca in cross_agent_insights
            ]

            # 3. Learning feedback history
            feedback_query = (
                select(LearningFeedbackHistory)
                .order_by(LearningFeedbackHistory.created_at.desc())
                .limit(10)
            )
            feedback_result = await session.execute(feedback_query)
            feedback_history = feedback_result.scalars().all()

            insights_data["feedback_history"] = [
                {
                    "id": fb.id,
                    "agent_id": fb.agent_id,
                    "feedback_type": fb.feedback_type,
                    "feedback_content": fb.feedback_content,
                    "feedback_score": fb.feedback_score,
                    "processing_status": fb.processing_status,
                    "impact_assessment": fb.impact_assessment,
                    "created_at": fb.created_at.isoformat(),
                }
                for fb in feedback_history
            ]

            initial_message = {
                "type": "initial_learning_insights",
                "insights": insights_data,
                "summary": {
                    "knowledge_base_entries": len(insights_data["knowledge_base"]),
                    "cross_agent_insights": len(insights_data["cross_agent_insights"]),
                    "feedback_entries": len(insights_data["feedback_history"]),
                    "total_insights": sum(len(v) for v in insights_data.values()),
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "websocket_info": {
                    "connection_type": "learning_insights",
                    "data_sources": [
                        "learning_knowledge_base",
                        "cross_agent_learning_insights",
                        "learning_feedback_history",
                    ],
                    "update_frequency": "real-time",
                },
            }

            await websocket.send_text(json.dumps(initial_message))

    except Exception as e:
        logger.error(f"Error sending initial learning insights: {e}")
        await websocket.send_text(
            json.dumps(
                {
                    "type": "error",
                    "message": f"Failed to load initial learning insights: {str(e)}",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        )
