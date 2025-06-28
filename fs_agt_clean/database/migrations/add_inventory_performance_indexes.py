"""Add performance indexes for inventory tables

Revision ID: add_inventory_indexes
Revises: 
Create Date: 2025-06-16 03:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_inventory_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add performance indexes for inventory tables."""
    
    # Add indexes for inventory_items table
    # These indexes will dramatically improve query performance
    
    # Single column indexes for commonly filtered fields
    op.create_index('idx_inventory_items_is_active', 'inventory_items', ['is_active'])
    op.create_index('idx_inventory_items_category', 'inventory_items', ['category'])
    op.create_index('idx_inventory_items_created_by', 'inventory_items', ['created_by'])
    op.create_index('idx_inventory_items_created_at', 'inventory_items', ['created_at'])
    op.create_index('idx_inventory_items_updated_at', 'inventory_items', ['updated_at'])
    op.create_index('idx_inventory_items_quantity', 'inventory_items', ['quantity'])
    op.create_index('idx_inventory_items_location', 'inventory_items', ['location'])
    op.create_index('idx_inventory_items_supplier', 'inventory_items', ['supplier'])
    
    # Composite indexes for common query patterns
    # Active items by user (most common query pattern)
    op.create_index('idx_inventory_items_active_user', 'inventory_items', ['is_active', 'created_by'])
    
    # Active items by category
    op.create_index('idx_inventory_items_active_category', 'inventory_items', ['is_active', 'category'])
    
    # Active items ordered by creation date (for pagination)
    op.create_index('idx_inventory_items_active_created', 'inventory_items', ['is_active', 'created_at'])
    
    # Low stock items (for alerts)
    op.create_index('idx_inventory_items_low_stock', 'inventory_items', ['is_active', 'quantity', 'low_stock_threshold'])
    
    # Search optimization - partial indexes for text search
    # Note: These are PostgreSQL-specific partial indexes
    op.execute("""
        CREATE INDEX idx_inventory_items_name_search 
        ON inventory_items USING gin(to_tsvector('english', name)) 
        WHERE is_active = true
    """)
    
    op.execute("""
        CREATE INDEX idx_inventory_items_description_search 
        ON inventory_items USING gin(to_tsvector('english', description)) 
        WHERE is_active = true AND description IS NOT NULL
    """)
    
    # Add indexes for inventory_transactions table
    op.create_index('idx_inventory_transactions_item_id', 'inventory_transactions', ['item_id'])
    op.create_index('idx_inventory_transactions_type', 'inventory_transactions', ['transaction_type'])
    op.create_index('idx_inventory_transactions_date', 'inventory_transactions', ['transaction_date'])
    op.create_index('idx_inventory_transactions_item_date', 'inventory_transactions', ['item_id', 'transaction_date'])
    
    # Add indexes for inventory_adjustments table  
    op.create_index('idx_inventory_adjustments_item_id', 'inventory_adjustments', ['item_id'])
    op.create_index('idx_inventory_adjustments_type', 'inventory_adjustments', ['adjustment_type'])
    op.create_index('idx_inventory_adjustments_date', 'inventory_adjustments', ['adjustment_date'])
    op.create_index('idx_inventory_adjustments_item_date', 'inventory_adjustments', ['item_id', 'adjustment_date'])
    
    # Add indexes for inventory_movements table
    op.create_index('idx_inventory_movements_item_id', 'inventory_movements', ['item_id'])
    op.create_index('idx_inventory_movements_type', 'inventory_movements', ['movement_type'])
    op.create_index('idx_inventory_movements_date', 'inventory_movements', ['movement_date'])
    op.create_index('idx_inventory_movements_from_location', 'inventory_movements', ['from_location_id'])
    op.create_index('idx_inventory_movements_to_location', 'inventory_movements', ['to_location_id'])
    
    # Add indexes for inventory_locations table
    op.create_index('idx_inventory_locations_is_active', 'inventory_locations', ['is_active'])
    op.create_index('idx_inventory_locations_code', 'inventory_locations', ['code'])


def downgrade():
    """Remove performance indexes for inventory tables."""
    
    # Drop inventory_items indexes
    op.drop_index('idx_inventory_items_is_active')
    op.drop_index('idx_inventory_items_category')
    op.drop_index('idx_inventory_items_created_by')
    op.drop_index('idx_inventory_items_created_at')
    op.drop_index('idx_inventory_items_updated_at')
    op.drop_index('idx_inventory_items_quantity')
    op.drop_index('idx_inventory_items_location')
    op.drop_index('idx_inventory_items_supplier')
    
    # Drop composite indexes
    op.drop_index('idx_inventory_items_active_user')
    op.drop_index('idx_inventory_items_active_category')
    op.drop_index('idx_inventory_items_active_created')
    op.drop_index('idx_inventory_items_low_stock')
    
    # Drop search indexes
    op.execute("DROP INDEX IF EXISTS idx_inventory_items_name_search")
    op.execute("DROP INDEX IF EXISTS idx_inventory_items_description_search")
    
    # Drop inventory_transactions indexes
    op.drop_index('idx_inventory_transactions_item_id')
    op.drop_index('idx_inventory_transactions_type')
    op.drop_index('idx_inventory_transactions_date')
    op.drop_index('idx_inventory_transactions_item_date')
    
    # Drop inventory_adjustments indexes
    op.drop_index('idx_inventory_adjustments_item_id')
    op.drop_index('idx_inventory_adjustments_type')
    op.drop_index('idx_inventory_adjustments_date')
    op.drop_index('idx_inventory_adjustments_item_date')
    
    # Drop inventory_movements indexes
    op.drop_index('idx_inventory_movements_item_id')
    op.drop_index('idx_inventory_movements_type')
    op.drop_index('idx_inventory_movements_date')
    op.drop_index('idx_inventory_movements_from_location')
    op.drop_index('idx_inventory_movements_to_location')
    
    # Drop inventory_locations indexes
    op.drop_index('idx_inventory_locations_is_active')
    op.drop_index('idx_inventory_locations_code')
