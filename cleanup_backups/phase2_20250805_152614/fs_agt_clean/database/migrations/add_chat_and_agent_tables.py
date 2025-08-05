"""
Alembic Migration: Add Chat and UnifiedAgent Tables
============================================

This migration adds the core tables for chat functionality and agent management.

Revision ID: add_chat_and_agent_tables
Revises: 
Create Date: 2024-12-01 10:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_chat_and_agent_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Create chat and agent tables."""
    
    # Create conversations table
    op.create_table(
        'conversations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create messages table
    op.create_table(
        'messages',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('sender', sa.String(length=50), nullable=False),
        sa.Column('agent_type', sa.String(length=50), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('parent_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create chat_sessions table
    op.create_table(
        'chat_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('session_token', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.String(length=10), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('session_token')
    )
    
    # Create message_reactions table
    op.create_table(
        'message_reactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('reaction_type', sa.String(length=20), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['message_id'], ['messages.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create agent_status table
    op.create_table(
        'agent_status',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(length=100), nullable=False),
        sa.Column('agent_type', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('last_heartbeat', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('metrics', sa.JSON(), nullable=True),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('agent_id')
    )
    
    # Create agent_decisions table
    op.create_table(
        'agent_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(length=100), nullable=False),
        sa.Column('decision_type', sa.String(length=50), nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('rationale', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('execution_result', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create agent_performance_metrics table
    op.create_table(
        'agent_performance_metrics',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(length=100), nullable=False),
        sa.Column('metric_name', sa.String(length=100), nullable=False),
        sa.Column('metric_value', sa.Float(), nullable=False),
        sa.Column('metric_unit', sa.String(length=20), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('extra_metadata', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create agent_communications table
    op.create_table(
        'agent_communications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('from_agent_id', sa.String(length=100), nullable=False),
        sa.Column('to_agent_id', sa.String(length=100), nullable=False),
        sa.Column('message_type', sa.String(length=50), nullable=False),
        sa.Column('message_content', sa.JSON(), nullable=False),
        sa.Column('priority', sa.String(length=10), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('response_data', sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create agent_tasks table
    op.create_table(
        'agent_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(length=100), nullable=False),
        sa.Column('task_type', sa.String(length=50), nullable=False),
        sa.Column('task_name', sa.String(length=200), nullable=False),
        sa.Column('task_parameters', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('max_retries', sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better performance
    op.create_index('ix_conversations_user_id', 'conversations', ['user_id'])
    op.create_index('ix_conversations_created_at', 'conversations', ['created_at'])
    
    op.create_index('ix_messages_conversation_id', 'messages', ['conversation_id'])
    op.create_index('ix_messages_timestamp', 'messages', ['timestamp'])
    op.create_index('ix_messages_sender', 'messages', ['sender'])
    op.create_index('ix_messages_agent_type', 'messages', ['agent_type'])
    
    op.create_index('ix_agent_status_agent_type', 'agent_status', ['agent_type'])
    op.create_index('ix_agent_status_status', 'agent_status', ['status'])
    op.create_index('ix_agent_status_last_heartbeat', 'agent_status', ['last_heartbeat'])
    
    op.create_index('ix_agent_decisions_agent_id', 'agent_decisions', ['agent_id'])
    op.create_index('ix_agent_decisions_status', 'agent_decisions', ['status'])
    op.create_index('ix_agent_decisions_created_at', 'agent_decisions', ['created_at'])
    
    op.create_index('ix_agent_performance_metrics_agent_id', 'agent_performance_metrics', ['agent_id'])
    op.create_index('ix_agent_performance_metrics_timestamp', 'agent_performance_metrics', ['timestamp'])
    
    op.create_index('ix_agent_tasks_agent_id', 'agent_tasks', ['agent_id'])
    op.create_index('ix_agent_tasks_status', 'agent_tasks', ['status'])
    op.create_index('ix_agent_tasks_priority', 'agent_tasks', ['priority'])


def downgrade():
    """Drop chat and agent tables."""
    
    # Drop indexes first
    op.drop_index('ix_agent_tasks_priority')
    op.drop_index('ix_agent_tasks_status')
    op.drop_index('ix_agent_tasks_agent_id')
    
    op.drop_index('ix_agent_performance_metrics_timestamp')
    op.drop_index('ix_agent_performance_metrics_agent_id')
    
    op.drop_index('ix_agent_decisions_created_at')
    op.drop_index('ix_agent_decisions_status')
    op.drop_index('ix_agent_decisions_agent_id')
    
    op.drop_index('ix_agent_status_last_heartbeat')
    op.drop_index('ix_agent_status_status')
    op.drop_index('ix_agent_status_agent_type')
    
    op.drop_index('ix_messages_agent_type')
    op.drop_index('ix_messages_sender')
    op.drop_index('ix_messages_timestamp')
    op.drop_index('ix_messages_conversation_id')
    
    op.drop_index('ix_conversations_created_at')
    op.drop_index('ix_conversations_user_id')
    
    # Drop tables
    op.drop_table('agent_tasks')
    op.drop_table('agent_communications')
    op.drop_table('agent_performance_metrics')
    op.drop_table('agent_decisions')
    op.drop_table('agent_status')
    op.drop_table('message_reactions')
    op.drop_table('chat_sessions')
    op.drop_table('messages')
    op.drop_table('conversations')
