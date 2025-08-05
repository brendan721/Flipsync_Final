"""
Database migration to add eBay OAuth tables.

This migration creates the necessary tables for storing eBay OAuth tokens
and state parameters with proper security measures.
"""

from alembic import op
import sqlalchemy as sa


def upgrade():
    """Create eBay OAuth tables."""
    
    # Create ebay_oauth_tokens table
    op.create_table(
        'ebay_oauth_tokens',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('user_id', sa.String(255), nullable=False, index=True),
        sa.Column('access_token', sa.Text, nullable=False),
        sa.Column('refresh_token', sa.Text, nullable=True),
        sa.Column('token_type', sa.String(50), nullable=False, default='Bearer'),
        sa.Column('expires_in', sa.Integer, nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('scope', sa.Text, nullable=True),
        sa.Column('state', sa.String(255), nullable=True),
        sa.Column('ebay_user_id', sa.String(255), nullable=True),
        sa.Column('marketplace_id', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean, nullable=False, default=True),
        sa.Column('is_revoked', sa.Boolean, nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
    )
    
    # Create indexes for ebay_oauth_tokens
    op.create_index('ix_ebay_oauth_tokens_user_id', 'ebay_oauth_tokens', ['user_id'])
    op.create_index('ix_ebay_oauth_tokens_is_active', 'ebay_oauth_tokens', ['is_active'])
    op.create_index('ix_ebay_oauth_tokens_expires_at', 'ebay_oauth_tokens', ['expires_at'])
    
    # Create ebay_oauth_states table
    op.create_table(
        'ebay_oauth_states',
        sa.Column('id', sa.String(255), primary_key=True),
        sa.Column('state', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('user_id', sa.String(255), nullable=True, index=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('user_agent', sa.Text, nullable=True),
        sa.Column('is_used', sa.Boolean, nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    )
    
    # Create indexes for ebay_oauth_states
    op.create_index('ix_ebay_oauth_states_state', 'ebay_oauth_states', ['state'])
    op.create_index('ix_ebay_oauth_states_user_id', 'ebay_oauth_states', ['user_id'])
    op.create_index('ix_ebay_oauth_states_expires_at', 'ebay_oauth_states', ['expires_at'])
    op.create_index('ix_ebay_oauth_states_is_used', 'ebay_oauth_states', ['is_used'])


def downgrade():
    """Drop eBay OAuth tables."""
    
    # Drop indexes first
    op.drop_index('ix_ebay_oauth_states_is_used', 'ebay_oauth_states')
    op.drop_index('ix_ebay_oauth_states_expires_at', 'ebay_oauth_states')
    op.drop_index('ix_ebay_oauth_states_user_id', 'ebay_oauth_states')
    op.drop_index('ix_ebay_oauth_states_state', 'ebay_oauth_states')
    
    op.drop_index('ix_ebay_oauth_tokens_expires_at', 'ebay_oauth_tokens')
    op.drop_index('ix_ebay_oauth_tokens_is_active', 'ebay_oauth_tokens')
    op.drop_index('ix_ebay_oauth_tokens_user_id', 'ebay_oauth_tokens')
    
    # Drop tables
    op.drop_table('ebay_oauth_states')
    op.drop_table('ebay_oauth_tokens')
