"""
Agent Decisions Database Adapter
===============================

Adapter to handle schema differences between expected workflow schema
and actual database schema for agent_decisions table.
"""

import asyncio
import json
import time
from typing import Any, Dict, Optional
from datetime import datetime, timezone

import asyncpg


class AgentDecisionsAdapter:
    """
    Adapter to handle agent_decisions table operations with schema mapping.

    Maps between workflow expected schema and actual database schema:

    Workflow Expected:
    - agent_type -> agent_id
    - decision_type -> decision_type
    - input_data -> parameters
    - output_data -> result
    - confidence_score -> confidence
    - processing_time -> (stored in result metadata)
    - timestamp -> created_at
    """

    def __init__(self, connection: asyncpg.Connection):
        """Initialize adapter with database connection."""
        self.conn = connection

    async def insert_decision(
        self,
        agent_type: str,
        decision_type: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any],
        confidence_score: float,
        processing_time: float,
        timestamp: Optional[datetime] = None,
    ) -> int:
        """
        Insert a decision record with schema mapping.

        Args:
            agent_type: Type of agent making the decision
            decision_type: Type of decision being made
            input_data: Input data for the decision
            output_data: Output/result data from the decision
            confidence_score: Confidence score (0.0 to 1.0)
            processing_time: Time taken to process in seconds
            timestamp: Optional timestamp (defaults to now)

        Returns:
            int: ID of the inserted record
        """
        if timestamp is None:
            timestamp = datetime.now(timezone.utc)

        # Map workflow schema to database schema
        mapped_agent_id = agent_type
        mapped_decision_type = decision_type
        mapped_parameters = input_data
        mapped_confidence = confidence_score

        # Include processing time in result metadata
        mapped_result = {
            **output_data,
            "processing_time": processing_time,
            "workflow_timestamp": timestamp.isoformat(),
        }

        # Generate rationale from decision type and confidence
        rationale = (
            f"Decision made by {agent_type} with {confidence_score:.2%} confidence"
        )

        # Insert with mapped schema
        decision_id = await self.conn.fetchval(
            """
            INSERT INTO agent_decisions (
                agent_id, decision_type, parameters, confidence, 
                rationale, status, created_at, executed_at, result
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $7, $8
            ) RETURNING id
        """,
            mapped_agent_id,
            mapped_decision_type,
            (
                json.dumps(mapped_parameters)
                if isinstance(mapped_parameters, dict)
                else mapped_parameters
            ),
            mapped_confidence,
            rationale,
            "completed",
            timestamp,
            (
                json.dumps(mapped_result)
                if isinstance(mapped_result, dict)
                else mapped_result
            ),
        )

        return decision_id

    async def update_decision(
        self, decision_id: int, output_data: Dict[str, Any], processing_time: float
    ) -> bool:
        """
        Update a decision record with results.

        Args:
            decision_id: ID of the decision to update
            output_data: Updated output data
            processing_time: Total processing time

        Returns:
            bool: True if update was successful
        """
        # Include processing time in result metadata
        mapped_result = {
            **output_data,
            "processing_time": processing_time,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        rows_affected = await self.conn.execute(
            """
            UPDATE agent_decisions 
            SET result = $1, executed_at = CURRENT_TIMESTAMP, status = 'completed'
            WHERE id = $2
        """,
            (
                json.dumps(mapped_result)
                if isinstance(mapped_result, dict)
                else mapped_result
            ),
            decision_id,
        )

        return rows_affected == "UPDATE 1"

    async def get_decision(self, decision_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a decision record by ID with schema mapping back to workflow format.

        Args:
            decision_id: ID of the decision to retrieve

        Returns:
            Dict with workflow-compatible schema or None if not found
        """
        record = await self.conn.fetchrow(
            """
            SELECT id, agent_id, decision_type, parameters, confidence,
                   rationale, status, created_at, executed_at, result
            FROM agent_decisions
            WHERE id = $1
        """,
            decision_id,
        )

        if not record:
            return None

        # Map database schema back to workflow schema
        result_data = json.loads(record["result"]) if record["result"] else {}
        processing_time = result_data.get("processing_time", 0.0)

        return {
            "id": record["id"],
            "agent_type": record["agent_id"],
            "decision_type": record["decision_type"],
            "input_data": (
                json.loads(record["parameters"]) if record["parameters"] else {}
            ),
            "output_data": result_data,
            "confidence_score": record["confidence"],
            "processing_time": processing_time,
            "timestamp": record["created_at"],
            "status": record["status"],
        }

    async def get_recent_decisions(
        self, agent_type: Optional[str] = None, limit: int = 10
    ) -> list[Dict[str, Any]]:
        """
        Get recent decisions with optional filtering by agent type.

        Args:
            agent_type: Optional agent type to filter by
            limit: Maximum number of records to return

        Returns:
            List of decision records in workflow-compatible format
        """
        if agent_type:
            records = await self.conn.fetch(
                """
                SELECT id, agent_id, decision_type, parameters, confidence,
                       rationale, status, created_at, executed_at, result
                FROM agent_decisions
                WHERE agent_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """,
                agent_type,
                limit,
            )
        else:
            records = await self.conn.fetch(
                """
                SELECT id, agent_id, decision_type, parameters, confidence,
                       rationale, status, created_at, executed_at, result
                FROM agent_decisions
                ORDER BY created_at DESC
                LIMIT $1
            """,
                limit,
            )

        # Map all records to workflow schema
        mapped_records = []
        for record in records:
            result_data = json.loads(record["result"]) if record["result"] else {}
            processing_time = result_data.get("processing_time", 0.0)

            mapped_records.append(
                {
                    "id": record["id"],
                    "agent_type": record["agent_id"],
                    "decision_type": record["decision_type"],
                    "input_data": (
                        json.loads(record["parameters"]) if record["parameters"] else {}
                    ),
                    "output_data": result_data,
                    "confidence_score": record["confidence"],
                    "processing_time": processing_time,
                    "timestamp": record["created_at"],
                    "status": record["status"],
                }
            )

        return mapped_records


async def create_adapter(
    host: str = "174.138.77.110",
    port: int = 5432,
    database: str = "flipsync_agentic_test",
    user: str = "postgres",
    password: str = os.getenv("DB_PASSWORD", "your_password"),
) -> AgentDecisionsAdapter:
    """
    Create an AgentDecisionsAdapter with database connection.

    Returns:
        AgentDecisionsAdapter: Configured adapter instance
    """
    conn = await asyncpg.connect(
        host=host, port=port, database=database, user=user, password=password
    )

    return AgentDecisionsAdapter(conn)


# Test function
async def test_adapter():
    """Test the adapter functionality."""
    adapter = await create_adapter()

    # Test insertion
    decision_id = await adapter.insert_decision(
        agent_type="test_agent",
        decision_type="test_decision",
        input_data={"test": "input"},
        output_data={"test": "output"},
        confidence_score=0.95,
        processing_time=0.123,
    )

    print(f"Inserted decision ID: {decision_id}")

    # Test retrieval
    decision = await adapter.get_decision(decision_id)
    print(f"Retrieved decision: {decision}")

    # Clean up
    await adapter.conn.execute("DELETE FROM agent_decisions WHERE id = $1", decision_id)
    await adapter.conn.close()

    return True


if __name__ == "__main__":
    asyncio.run(test_adapter())
