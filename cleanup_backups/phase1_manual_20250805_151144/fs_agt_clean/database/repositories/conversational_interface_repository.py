"""
Conversational Interface Repository for 4+1 Architecture
=======================================================

Repository pattern for conversational interface database operations in FlipSync's 4+1 architecture.
Handles the +1 conversational interface: StrategicChatService.

Key Features:
- Strict 4+1 architecture compliance
- Gemini-exclusive LLM constraint enforcement
- Cost tracking and budget management
- Conversation and message metrics
- Strategic chat service management
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from fs_agt_clean.database.base_repository import BaseRepository
from fs_agt_clean.database.models.autonomous_agent import (
    ConversationalInterface,
    ConversationalInterfaceType,
)


class ConversationalInterfaceRepository(BaseRepository):
    """Repository for 4+1 architecture conversational interface."""

    def __init__(self):
        # Initialize with ConversationalInterface as the primary model
        super().__init__(model_class=ConversationalInterface, table_name="conversational_interfaces")

    async def create_or_update_interface(
        self,
        session: AsyncSession,
        interface_id: str,
        interface_type: ConversationalInterfaceType,
        service_class: str,
        llm_provider: str = "gemini",
        gemini_model: str = "gemini-pro",
        daily_budget: float = 10.0,
        status: str = "active",
        **kwargs
    ) -> ConversationalInterface:
        """Create or update conversational interface with 4+1 compliance.

        Args:
            session: Database session
            interface_id: Unique identifier for the interface
            interface_type: Type of interface (strategic_chat)
            service_class: Python class name of the service
            llm_provider: LLM provider (must be 'gemini')
            gemini_model: Gemini model to use
            daily_budget: Daily budget for LLM costs
            status: Interface status
            **kwargs: Additional interface properties

        Returns:
            Created or updated conversational interface

        Raises:
            ValueError: If interface violates 4+1 architecture constraints
        """
        # Validate 4+1 architecture compliance
        if llm_provider != "gemini":
            raise ValueError(f"4+1 architecture requires Gemini-exclusive LLM usage, got: {llm_provider}")
        
        if interface_type != ConversationalInterfaceType.STRATEGIC_CHAT:
            raise ValueError(f"Invalid interface type for 4+1 architecture: {interface_type}")

        # Check if interface already exists
        existing_query = select(ConversationalInterface).where(
            ConversationalInterface.interface_id == interface_id
        )
        result = await session.execute(existing_query)
        existing_interface = result.scalar_one_or_none()

        if existing_interface:
            # Update existing interface
            existing_interface.interface_type = interface_type
            existing_interface.service_class = service_class
            existing_interface.llm_provider = llm_provider
            existing_interface.gemini_model = gemini_model
            existing_interface.daily_budget = daily_budget
            existing_interface.status = status
            
            # Update timestamps
            existing_interface.last_activity = datetime.now(timezone.utc)
            existing_interface.updated_at = datetime.now(timezone.utc)
            
            # Apply additional kwargs
            for key, value in kwargs.items():
                if hasattr(existing_interface, key):
                    setattr(existing_interface, key, value)

            await session.commit()
            await session.refresh(existing_interface)
            return existing_interface
        else:
            # Create new interface with 4+1 architecture compliance
            interface = ConversationalInterface(
                id=str(uuid.uuid4()),
                interface_id=interface_id,
                interface_type=interface_type,
                service_class=service_class,
                # Enforce 4+1 architecture constraints
                llm_provider=llm_provider,  # Must be 'gemini'
                gemini_model=gemini_model,
                # Configuration
                status=status,
                daily_budget=daily_budget,
                total_conversations=0,
                total_messages=0,
                total_cost=0.0,
                health_status="unknown",
                # Timestamps
                initialized_at=datetime.now(timezone.utc),
                last_activity=datetime.now(timezone.utc),
            )
            
            # Apply additional kwargs
            for key, value in kwargs.items():
                if hasattr(interface, key):
                    setattr(interface, key, value)

            session.add(interface)
            await session.commit()
            await session.refresh(interface)
            return interface

    async def get_conversational_interface(
        self, session: AsyncSession, interface_id: str
    ) -> Optional[ConversationalInterface]:
        """Get conversational interface by ID.

        Args:
            session: Database session
            interface_id: ID of the interface

        Returns:
            ConversationalInterface if found, None otherwise
        """
        query = select(ConversationalInterface).where(
            ConversationalInterface.interface_id == interface_id
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def get_strategic_chat_service(
        self, session: AsyncSession
    ) -> Optional[ConversationalInterface]:
        """Get the strategic chat service interface.

        Args:
            session: Database session

        Returns:
            StrategicChatService interface if found, None otherwise
        """
        query = select(ConversationalInterface).where(
            ConversationalInterface.interface_type == ConversationalInterfaceType.STRATEGIC_CHAT
        )
        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def record_conversation(
        self,
        session: AsyncSession,
        interface_id: str,
        conversation_data: Dict[str, Any],
        cost: float = 0.0,
        message_count: int = 1,
    ) -> bool:
        """Record conversation activity and update metrics.

        Args:
            session: Database session
            interface_id: ID of the interface
            conversation_data: Conversation metadata
            cost: Cost of the conversation
            message_count: Number of messages in the conversation

        Returns:
            True if recorded successfully, False if interface not found
        """
        interface = await self.get_conversational_interface(session, interface_id)
        if not interface:
            return False

        # Update conversation metrics
        interface.total_conversations += 1
        interface.total_messages += message_count
        interface.total_cost += cost
        interface.last_activity = datetime.now(timezone.utc)
        interface.updated_at = datetime.now(timezone.utc)

        # Check budget compliance
        if interface.total_cost > interface.daily_budget:
            interface.health_status = "budget_exceeded"
        else:
            interface.health_status = "healthy"

        await session.commit()
        return True

    async def update_interface_status(
        self, 
        session: AsyncSession, 
        interface_id: str, 
        status: str,
        health_status: Optional[str] = None
    ) -> bool:
        """Update interface status.

        Args:
            session: Database session
            interface_id: ID of the interface
            status: New status
            health_status: Optional health status

        Returns:
            True if updated successfully, False if interface not found
        """
        interface = await self.get_conversational_interface(session, interface_id)
        if not interface:
            return False

        interface.status = status
        if health_status:
            interface.health_status = health_status
        interface.last_activity = datetime.now(timezone.utc)
        interface.updated_at = datetime.now(timezone.utc)
        
        await session.commit()
        return True

    async def reset_daily_budget(
        self, session: AsyncSession, interface_id: str
    ) -> bool:
        """Reset daily budget and cost tracking.

        Args:
            session: Database session
            interface_id: ID of the interface

        Returns:
            True if reset successfully, False if interface not found
        """
        interface = await self.get_conversational_interface(session, interface_id)
        if not interface:
            return False

        interface.total_cost = 0.0
        interface.health_status = "healthy"
        interface.updated_at = datetime.now(timezone.utc)
        
        await session.commit()
        return True

    async def get_interface_metrics(
        self, session: AsyncSession, interface_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get interface metrics and statistics.

        Args:
            session: Database session
            interface_id: ID of the interface

        Returns:
            Interface metrics dictionary or None if not found
        """
        interface = await self.get_conversational_interface(session, interface_id)
        if not interface:
            return None

        return {
            "interface_id": interface.interface_id,
            "interface_type": interface.interface_type,
            "service_class": interface.service_class,
            "llm_provider": interface.llm_provider,
            "gemini_model": interface.gemini_model,
            "status": interface.status,
            "health_status": interface.health_status,
            "total_conversations": interface.total_conversations,
            "total_messages": interface.total_messages,
            "total_cost": interface.total_cost,
            "daily_budget": interface.daily_budget,
            "budget_utilization": (interface.total_cost / interface.daily_budget) * 100 if interface.daily_budget > 0 else 0,
            "average_cost_per_conversation": interface.total_cost / max(interface.total_conversations, 1),
            "average_messages_per_conversation": interface.total_messages / max(interface.total_conversations, 1),
            "initialized_at": interface.initialized_at.isoformat() if interface.initialized_at else None,
            "last_activity": interface.last_activity.isoformat() if interface.last_activity else None,
            "created_at": interface.created_at.isoformat(),
            "updated_at": interface.updated_at.isoformat(),
        }

    async def get_all_interfaces(
        self, session: AsyncSession
    ) -> List[ConversationalInterface]:
        """Get all conversational interfaces.

        Args:
            session: Database session

        Returns:
            List of all conversational interfaces (should be exactly 1 in 4+1 architecture)
        """
        query = select(ConversationalInterface).order_by(ConversationalInterface.interface_type)
        result = await session.execute(query)
        return result.scalars().all()

    async def validate_4plus1_compliance(
        self, session: AsyncSession
    ) -> Dict[str, Any]:
        """Validate 4+1 architecture compliance for conversational interfaces.

        Args:
            session: Database session

        Returns:
            Compliance validation report
        """
        interfaces = await self.get_all_interfaces(session)
        
        # Should have exactly 1 conversational interface
        interface_count_compliance = len(interfaces) == 1
        
        # All interfaces should use Gemini exclusively
        gemini_compliance = all(interface.llm_provider == "gemini" for interface in interfaces)
        
        # All interfaces should be strategic chat type
        strategic_chat_compliance = all(
            interface.interface_type == ConversationalInterfaceType.STRATEGIC_CHAT 
            for interface in interfaces
        )
        
        # Budget compliance (not exceeding daily budget)
        budget_compliance = all(
            interface.total_cost <= interface.daily_budget 
            for interface in interfaces
        )
        
        return {
            "architecture_type": "4+1_conversational",
            "conversational_interfaces_count": len(interfaces),
            "expected_conversational_interfaces": 1,
            "interface_count_compliance": interface_count_compliance,
            "gemini_exclusive_compliance": gemini_compliance,
            "strategic_chat_compliance": strategic_chat_compliance,
            "budget_compliance": budget_compliance,
            "interfaces": [
                {
                    "interface_id": interface.interface_id,
                    "interface_type": interface.interface_type,
                    "llm_provider": interface.llm_provider,
                    "status": interface.status,
                    "health_status": interface.health_status,
                    "total_cost": interface.total_cost,
                    "daily_budget": interface.daily_budget,
                }
                for interface in interfaces
            ],
            "compliance_score": (
                (interface_count_compliance * 0.4) +
                (gemini_compliance * 0.3) +
                (strategic_chat_compliance * 0.2) +
                (budget_compliance * 0.1)
            ),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
