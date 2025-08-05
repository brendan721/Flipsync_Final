"""
Database-backed Decision Maker for FlipSync Agentic System

This module provides a production-ready database-backed implementation of the
DecisionMaker interface, storing all decisions in PostgreSQL for persistence
across agent restarts and enabling cross-agent decision sharing.
"""

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from fs_agt_clean.core.coordination.decision.interfaces import DecisionMaker
from fs_agt_clean.core.coordination.decision.models import (
    Decision,
    DecisionError,
    DecisionMetadata,
    DecisionStatus,
    DecisionType,
)
from fs_agt_clean.core.db.database import Database

logger = logging.getLogger(__name__)


class DatabaseDecisionMaker(DecisionMaker):
    """Database-backed implementation of DecisionMaker.

    This implementation stores all decisions in PostgreSQL, providing:
    - Persistent decision storage across agent restarts
    - Cross-agent decision sharing and history
    - Transaction-safe decision operations
    - Performance optimized database queries
    """

    def __init__(self, maker_id: str, database: Database):
        """Initialize the database decision maker.

        Args:
            maker_id: Unique identifier for this decision maker
            database: Database instance for persistence operations
        """
        self.maker_id = maker_id
        self.database = database
        self._decision_cache: Dict[str, Decision] = {}
        logger.info(f"Initialized DatabaseDecisionMaker {maker_id}")

    async def make_decision(
        self,
        context: Dict[str, Any],
        options: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Decision:
        """Make a decision and persist it to the database.

        Args:
            context: Context in which the decision is being made
            options: Available options to choose from
            constraints: Optional constraints on the decision

        Returns:
            The decision that was made

        Raises:
            DecisionError: If the decision cannot be made or stored
        """
        logger.debug(f"Making decision with {len(options)} options")

        # Validate inputs
        if not options:
            raise DecisionError(
                "Cannot make decision: no options provided",
                decision_id=None,
                maker_id=self.maker_id,
            )

        try:
            # Generate unique decision ID
            decision_id = str(uuid.uuid4())

            # Analyze options and make decision
            selected_option = await self._analyze_options(context, options, constraints)
            confidence = await self._calculate_confidence(
                context, selected_option, options
            )
            reasoning = await self._generate_reasoning(
                context, selected_option, options, constraints
            )

            # Create decision metadata
            metadata = DecisionMetadata(
                decision_id=decision_id,
                source=self.maker_id,
                created_at=datetime.now(timezone.utc),
                status=DecisionStatus.PENDING,
            )

            # Create decision object
            decision = Decision(
                decision_type=self._determine_decision_type(context),
                action=selected_option.get("action", "unknown"),
                confidence=confidence,
                reasoning=reasoning,
                alternatives=[
                    opt.get("action", "unknown")
                    for opt in options
                    if opt != selected_option
                ],
                metadata=metadata,
                context=context,
                battery_efficient=context.get("battery_efficient", False),
                network_efficient=context.get("network_efficient", False),
            )

            # Store decision in database
            await self._store_decision(decision)

            # Cache decision for quick access
            self._decision_cache[decision_id] = decision

            logger.info(f"Decision {decision_id} made and stored successfully")
            return decision

        except Exception as e:
            logger.error(f"Failed to make decision: {e}")
            raise DecisionError(
                f"Failed to make decision: {str(e)}",
                error_code="DECISION_CREATION_FAILED",
                details={
                    "decision_id": decision_id if "decision_id" in locals() else None,
                    "maker_id": self.maker_id,
                },
            )

    async def get_decision(self, decision_id: str) -> Optional[Decision]:
        """Get a decision by ID from database or cache.

        Args:
            decision_id: ID of the decision to get

        Returns:
            The decision, or None if not found
        """
        # Check cache first
        if decision_id in self._decision_cache:
            return self._decision_cache[decision_id]

        try:
            async with self.database.get_session() as session:
                # First try to find by UUID in parameters
                result = await session.execute(
                    text(
                        """
                        SELECT id, agent_id, decision_type, parameters, confidence,
                               rationale, status, created_at, executed_at, result
                        FROM agent_decisions
                        WHERE parameters::jsonb ->> 'decision_id' = :decision_id
                        AND agent_id = :agent_id
                    """
                    ),
                    {"decision_id": decision_id, "agent_id": self.maker_id},
                )
                row = result.fetchone()

                if not row:
                    return None

                # Reconstruct decision from database row
                decision = await self._reconstruct_decision(decision_id, row)

                # Cache for future access
                self._decision_cache[decision_id] = decision

                return decision

        except Exception as e:
            logger.error(f"Failed to get decision {decision_id}: {e}")
            return None

    async def list_decisions(
        self, filters: Optional[Dict[str, Any]] = None
    ) -> List[Decision]:
        """List decisions with optional filtering.

        Args:
            filters: Optional filters to apply

        Returns:
            List of decisions matching the filters
        """
        try:
            async with self.database.get_session() as session:
                # Build query with filters
                query = """
                    SELECT id, agent_id, decision_type, parameters, confidence, 
                           rationale, status, created_at, executed_at, result
                    FROM agent_decisions 
                    WHERE agent_id = :maker_id
                """
                params = {"maker_id": self.maker_id}

                if filters:
                    if "decision_type" in filters:
                        query += " AND decision_type = :decision_type"
                        params["decision_type"] = filters["decision_type"]

                    if "status" in filters:
                        query += " AND status = :status"
                        params["status"] = filters["status"]

                    if "min_confidence" in filters:
                        query += " AND confidence >= :min_confidence"
                        params["min_confidence"] = filters["min_confidence"]

                query += " ORDER BY created_at DESC"

                result = await session.execute(text(query), params)
                rows = result.fetchall()

                decisions = []
                for row in rows:
                    decision_id = str(row[0])
                    decision = await self._reconstruct_decision(decision_id, row[1:])
                    decisions.append(decision)

                logger.debug(
                    f"Retrieved {len(decisions)} decisions with filters: {filters}"
                )
                return decisions

        except Exception as e:
            logger.error(f"Failed to list decisions: {e}")
            return []

    async def _analyze_options(
        self,
        context: Dict[str, Any],
        options: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Analyze options and select the best one."""
        # Simple scoring algorithm - can be enhanced with ML in future
        best_option = None
        best_score = -1

        for option in options:
            score = 0

            # Score based on context relevance
            if "priority" in option:
                priority_value = option["priority"]
                # Handle string priorities
                if isinstance(priority_value, str):
                    priority_map = {
                        "low": 0.2,
                        "normal": 0.5,
                        "high": 0.8,
                        "urgent": 1.0,
                    }
                    priority_value = priority_map.get(priority_value, 0.5)
                score += priority_value * 0.4

            if "expected_outcome" in option:
                score += option.get("success_probability", 0.5) * 0.3

            # Apply constraints
            if constraints:
                if not self._satisfies_constraints(option, constraints):
                    continue

            # Prefer options with more information
            score += len(option) * 0.1

            if score > best_score:
                best_score = score
                best_option = option

        return best_option or options[0]  # Fallback to first option

    async def _calculate_confidence(
        self,
        context: Dict[str, Any],
        selected_option: Dict[str, Any],
        all_options: List[Dict[str, Any]],
    ) -> float:
        """Calculate confidence in the decision."""
        base_confidence = 0.5

        # Increase confidence if option has high success probability
        if "success_probability" in selected_option:
            base_confidence += selected_option["success_probability"] * 0.3

        # Increase confidence if we have good context
        if len(context) > 3:
            base_confidence += 0.1

        # Decrease confidence if many similar options
        if len(all_options) > 5:
            base_confidence -= 0.1

        return max(0.0, min(1.0, base_confidence))

    async def _generate_reasoning(
        self,
        context: Dict[str, Any],
        selected_option: Dict[str, Any],
        all_options: List[Dict[str, Any]],
        constraints: Optional[Dict[str, Any]],
    ) -> str:
        """Generate reasoning for the decision."""
        reasoning_parts = []

        reasoning_parts.append(
            f"Selected option: {selected_option.get('action', 'unknown')}"
        )
        reasoning_parts.append(f"Context factors: {len(context)} parameters considered")
        reasoning_parts.append(f"Alternatives evaluated: {len(all_options)} options")

        if constraints:
            reasoning_parts.append(f"Constraints applied: {list(constraints.keys())}")

        if "success_probability" in selected_option:
            reasoning_parts.append(
                f"Expected success: {selected_option['success_probability']:.2%}"
            )

        return "; ".join(reasoning_parts)

    def _determine_decision_type(self, context: Dict[str, Any]) -> DecisionType:
        """Determine the type of decision based on context."""
        if "inventory" in context:
            return DecisionType.OPTIMIZATION
        elif "action" in context:
            return DecisionType.ACTION
        elif "recommendation" in context:
            return DecisionType.RECOMMENDATION
        else:
            return DecisionType.CUSTOM

    def _satisfies_constraints(
        self, option: Dict[str, Any], constraints: Dict[str, Any]
    ) -> bool:
        """Check if an option satisfies the given constraints."""
        for constraint_key, constraint_value in constraints.items():
            if constraint_key in option:
                if option[constraint_key] != constraint_value:
                    return False
        return True

    async def _store_decision(self, decision: Decision) -> None:
        """Store decision in the database."""
        try:
            async with self.database.get_session() as session:
                result = await session.execute(
                    text(
                        """
                        INSERT INTO agent_decisions
                        (id, agent_id, decision_type, parameters, confidence, rationale,
                         status, created_at, executed_at, result)
                        VALUES (gen_random_uuid(), :agent_id, :decision_type, :parameters, :confidence,
                                :rationale, :status, :created_at, :executed_at, :result)
                        RETURNING id
                    """
                    ),
                    {
                        "agent_id": self.maker_id,
                        "decision_type": decision.decision_type.value,
                        "parameters": json.dumps(
                            {
                                "decision_id": decision.metadata.decision_id,
                                "action": decision.action,
                                "alternatives": decision.alternatives,
                                "context": decision.context,
                                "battery_efficient": decision.battery_efficient,
                                "network_efficient": decision.network_efficient,
                            }
                        ),
                        "confidence": decision.confidence,
                        "rationale": decision.reasoning,
                        "status": decision.metadata.status.value,
                        "created_at": decision.metadata.created_at,
                        "executed_at": None,
                        "result": None,
                    },
                )

                # Get the auto-generated database ID
                db_id = result.scalar()

                # Store the mapping between UUID and database ID
                decision._db_id = db_id  # Store database ID for future reference
                await session.commit()
                logger.debug(
                    f"Stored decision {decision.metadata.decision_id} in database"
                )

        except Exception as e:
            logger.error(f"Failed to store decision: {e}")
            raise DecisionError(f"Failed to store decision: {str(e)}")

    async def _reconstruct_decision(self, decision_id: str, row) -> Decision:
        """Reconstruct a Decision object from database row."""
        try:
            # Row structure: id, agent_id, decision_type, parameters, confidence, rationale, status, created_at, executed_at, result
            if isinstance(row[3], str):
                parameters = json.loads(row[3]) if row[3] else {}
            elif isinstance(row[3], dict):
                parameters = row[3]
            else:
                parameters = {}

            metadata = DecisionMetadata(
                decision_id=parameters.get("decision_id", decision_id),
                source=row[1],  # agent_id
                created_at=row[7],  # created_at
                status=DecisionStatus(row[6]),  # status
            )

            decision = Decision(
                decision_type=DecisionType(row[2]),  # decision_type
                action=parameters.get("action", "unknown"),
                confidence=row[4],  # confidence
                reasoning=row[5],  # rationale
                alternatives=parameters.get("alternatives", []),
                metadata=metadata,
                context=parameters.get("context", {}),
                battery_efficient=parameters.get("battery_efficient", False),
                network_efficient=parameters.get("network_efficient", False),
            )

            # Store database ID for future reference
            decision._db_id = row[0]  # id

            return decision

        except Exception as e:
            logger.error(f"Failed to reconstruct decision {decision_id}: {e}")
            raise DecisionError(f"Failed to reconstruct decision: {str(e)}")
