"""
Database Migration: Add 4+1 Architecture Tables
==============================================

This migration creates the core tables for FlipSync's 4+1 architecture:
- autonomous_agents: 4 autonomous agents (Market, Content, Executive, Logistics)
- conversational_interfaces: 1 conversational interface (StrategicChatService)
- autonomous_agent_decisions: LLM-free decision tracking with compliance

Key Features:
- Strict 4+1 architecture compliance
- LLM-free autonomous agent tracking
- Gemini-exclusive conversational interface
- Performance optimization with proper indexes
- Rollback capability preserving existing tables

Revision ID: add_4plus1_architecture_tables
Revises: add_metrics_tables
Create Date: 2024-12-01 15:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = "add_4plus1_architecture_tables"
down_revision = "add_metrics_tables"
branch_labels = None
depends_on = None


def upgrade():
    """Create 4+1 architecture tables."""

    # Create autonomous_agents table (4 agents: Market, Content, Executive, Logistics)
    op.create_table(
        "autonomous_agents",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("agent_id", sa.String(255), nullable=False, unique=True),
        sa.Column("agent_type", sa.String(50), nullable=False),
        sa.Column("agent_class", sa.String(255), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, default="initializing"),
        sa.Column("health_status", sa.String(50), nullable=True, default="unknown"),
        # 4+1 Architecture Compliance Fields
        sa.Column("llm_free", sa.Boolean, nullable=False, default=True),
        sa.Column(
            "uses_standard_decision_pipeline", sa.Boolean, nullable=False, default=True
        ),
        sa.Column(
            "architecture_type", sa.String(50), nullable=False, default="autonomous"
        ),
        # Performance Metrics
        sa.Column("total_decisions", sa.Integer, nullable=False, default=0),
        sa.Column("successful_decisions", sa.Integer, nullable=False, default=0),
        sa.Column("average_decision_time_ms", sa.Float, nullable=True),
        sa.Column("last_decision_time_ms", sa.Float, nullable=True),
        # Configuration
        sa.Column("capabilities", sa.Text, nullable=True),  # JSON string
        sa.Column("optimization_config", sa.Text, nullable=True),  # JSON string
        # Timestamps
        sa.Column("initialized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Constraints
        sa.CheckConstraint(
            "agent_type IN ('market', 'content', 'executive', 'logistics')",
            name="ck_autonomous_agents_type",
        ),
        sa.CheckConstraint(
            "status IN ('initializing', 'active', 'idle', 'processing', 'error', 'shutdown')",
            name="ck_autonomous_agents_status",
        ),
        sa.CheckConstraint(
            "llm_free = true", name="ck_autonomous_agents_llm_free"
        ),  # Enforce LLM-free constraint
        sa.CheckConstraint(
            "uses_standard_decision_pipeline = true",
            name="ck_autonomous_agents_pipeline",
        ),
    )

    # Create conversational_interfaces table (1 interface: StrategicChatService)
    op.create_table(
        "conversational_interfaces",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("interface_id", sa.String(255), nullable=False, unique=True),
        sa.Column(
            "interface_type", sa.String(50), nullable=False, default="strategic_chat"
        ),
        sa.Column("service_class", sa.String(255), nullable=False),
        # LLM Configuration (Gemini-exclusive)
        sa.Column("llm_provider", sa.String(100), nullable=False, default="gemini"),
        sa.Column("gemini_model", sa.String(100), nullable=False),
        # Status and Metrics
        sa.Column("status", sa.String(50), nullable=False, default="active"),
        sa.Column("total_conversations", sa.Integer, nullable=False, default=0),
        sa.Column("total_messages", sa.Integer, nullable=False, default=0),
        sa.Column("total_cost", sa.Float, nullable=False, default=0.0),
        sa.Column("daily_budget", sa.Float, nullable=False, default=10.0),
        sa.Column("health_status", sa.String(50), nullable=True, default="unknown"),
        # Timestamps
        sa.Column("initialized_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_activity", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Constraints
        sa.CheckConstraint(
            "interface_type IN ('strategic_chat')",
            name="ck_conversational_interfaces_type",
        ),
        sa.CheckConstraint(
            "llm_provider = 'gemini'", name="ck_conversational_interfaces_gemini_only"
        ),  # Enforce Gemini-only
        sa.CheckConstraint(
            "status IN ('active', 'inactive', 'maintenance', 'error')",
            name="ck_conversational_interfaces_status",
        ),
    )

    # Create autonomous_agent_decisions table (LLM-free decision tracking)
    op.create_table(
        "autonomous_agent_decisions",
        sa.Column("id", sa.String(255), primary_key=True),
        sa.Column("decision_id", sa.String(255), nullable=False),
        sa.Column("agent_id", sa.String(255), nullable=False),
        # Decision Details
        sa.Column("decision_type", sa.String(255), nullable=False),
        sa.Column("context", sa.Text, nullable=True),  # JSON string
        sa.Column("result", sa.Text, nullable=True),  # JSON string
        # Performance Tracking
        sa.Column("execution_time_ms", sa.Float, nullable=False),
        sa.Column("confidence", sa.Float, nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        # 4+1 Architecture Compliance Tracking
        sa.Column(
            "used_llm", sa.Boolean, nullable=False, default=False
        ),  # Must always be False
        sa.Column(
            "used_standard_pipeline", sa.Boolean, nullable=False, default=True
        ),  # Must always be True
        sa.Column("algorithm_used", sa.String(255), nullable=True),
        # Timestamps
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Foreign Key Constraints
        sa.ForeignKeyConstraint(
            ["agent_id"],
            ["autonomous_agents.id"],
            name="fk_autonomous_agent_decisions_agent_id",
        ),
        # Constraints
        sa.CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'failed')",
            name="ck_autonomous_agent_decisions_status",
        ),
        sa.CheckConstraint(
            "used_llm = false", name="ck_autonomous_agent_decisions_no_llm"
        ),  # Enforce LLM-free
        sa.CheckConstraint(
            "used_standard_pipeline = true",
            name="ck_autonomous_agent_decisions_standard_pipeline",
        ),
        sa.CheckConstraint(
            "confidence >= 0.0 AND confidence <= 1.0",
            name="ck_autonomous_agent_decisions_confidence",
        ),
        sa.CheckConstraint(
            "execution_time_ms >= 0.0",
            name="ck_autonomous_agent_decisions_execution_time",
        ),
    )

    # Create Performance Indexes for Autonomous Agents
    op.create_index("idx_autonomous_agents_type", "autonomous_agents", ["agent_type"])
    op.create_index("idx_autonomous_agents_status", "autonomous_agents", ["status"])
    op.create_index(
        "idx_autonomous_agents_heartbeat", "autonomous_agents", ["last_heartbeat"]
    )
    op.create_index(
        "idx_autonomous_agents_activity", "autonomous_agents", ["last_activity"]
    )
    op.create_index(
        "idx_autonomous_agents_compliance",
        "autonomous_agents",
        ["llm_free", "uses_standard_decision_pipeline"],
    )

    # Create Performance Indexes for Conversational Interfaces
    op.create_index(
        "idx_conversational_interfaces_type",
        "conversational_interfaces",
        ["interface_type"],
    )
    op.create_index(
        "idx_conversational_interfaces_status", "conversational_interfaces", ["status"]
    )
    op.create_index(
        "idx_conversational_interfaces_activity",
        "conversational_interfaces",
        ["last_activity"],
    )

    # Create Performance Indexes for Autonomous Agent Decisions
    op.create_index(
        "idx_autonomous_decisions_agent", "autonomous_agent_decisions", ["agent_id"]
    )
    op.create_index(
        "idx_autonomous_decisions_type", "autonomous_agent_decisions", ["decision_type"]
    )
    op.create_index(
        "idx_autonomous_decisions_status", "autonomous_agent_decisions", ["status"]
    )
    op.create_index(
        "idx_autonomous_decisions_execution_time",
        "autonomous_agent_decisions",
        ["execution_time_ms"],
    )
    op.create_index(
        "idx_autonomous_decisions_started_at",
        "autonomous_agent_decisions",
        ["started_at"],
    )
    op.create_index(
        "idx_autonomous_decisions_compliance",
        "autonomous_agent_decisions",
        ["used_llm", "used_standard_pipeline"],
    )

    # Create Composite Indexes for Common Query Patterns
    op.create_index(
        "idx_agent_decisions_composite",
        "autonomous_agent_decisions",
        ["agent_id", "status", "started_at"],
    )
    op.create_index(
        "idx_autonomous_agents_type_status",
        "autonomous_agents",
        ["agent_type", "status"],
    )


def downgrade():
    """Drop 4+1 architecture tables."""

    # Drop indexes first
    op.drop_index("idx_autonomous_agents_type_status")
    op.drop_index("idx_agent_decisions_composite")
    op.drop_index("idx_autonomous_decisions_compliance")
    op.drop_index("idx_autonomous_decisions_started_at")
    op.drop_index("idx_autonomous_decisions_execution_time")
    op.drop_index("idx_autonomous_decisions_status")
    op.drop_index("idx_autonomous_decisions_type")
    op.drop_index("idx_autonomous_decisions_agent")
    op.drop_index("idx_conversational_interfaces_activity")
    op.drop_index("idx_conversational_interfaces_status")
    op.drop_index("idx_conversational_interfaces_type")
    op.drop_index("idx_autonomous_agents_compliance")
    op.drop_index("idx_autonomous_agents_activity")
    op.drop_index("idx_autonomous_agents_heartbeat")
    op.drop_index("idx_autonomous_agents_status")
    op.drop_index("idx_autonomous_agents_type")

    # Drop tables in reverse order (respecting foreign key dependencies)
    op.drop_table("autonomous_agent_decisions")
    op.drop_table("conversational_interfaces")
    op.drop_table("autonomous_agents")
