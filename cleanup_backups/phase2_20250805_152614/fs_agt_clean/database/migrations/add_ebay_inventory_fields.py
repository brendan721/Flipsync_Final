"""Add eBay-specific fields to inventory_items table.

Revision ID: add_ebay_inventory_fields
Revises: 
Create Date: 2025-01-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_ebay_inventory_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add eBay-specific fields to inventory_items table."""
    # Add new columns for eBay integration
    op.add_column('inventory_items', 
                  sa.Column('condition_ebay', sa.String(50), nullable=True))
    op.add_column('inventory_items', 
                  sa.Column('marketplace_source', sa.String(50), nullable=True))
    op.add_column('inventory_items', 
                  sa.Column('metadata_json', sa.JSON(), nullable=True))
    op.add_column('inventory_items', 
                  sa.Column('last_sync_at', sa.DateTime(), nullable=True))
    
    # Create index on marketplace_source for efficient queries
    op.create_index('ix_inventory_items_marketplace_source', 
                    'inventory_items', ['marketplace_source'])
    
    # Create index on last_sync_at for sync operations
    op.create_index('ix_inventory_items_last_sync_at', 
                    'inventory_items', ['last_sync_at'])


def downgrade():
    """Remove eBay-specific fields from inventory_items table."""
    # Drop indexes
    op.drop_index('ix_inventory_items_last_sync_at', 'inventory_items')
    op.drop_index('ix_inventory_items_marketplace_source', 'inventory_items')
    
    # Drop columns
    op.drop_column('inventory_items', 'last_sync_at')
    op.drop_column('inventory_items', 'metadata_json')
    op.drop_column('inventory_items', 'marketplace_source')
    op.drop_column('inventory_items', 'condition_ebay')
