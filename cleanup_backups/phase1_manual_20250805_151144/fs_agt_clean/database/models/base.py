"""
Base Model Compatibility Layer
==============================

This module provides backward compatibility for imports from the old base.py location.
All base models have been migrated to unified_base.py, but this file ensures
existing imports continue to work during the transition period.

This is a compatibility bridge that imports from the unified base models.
"""

# Import all base classes from the unified base module
from .unified_base import (
    AuditableModel,
    AuditMixin,
    Base,
    BaseModel,
    DatabaseSession,
    FullFeaturedModel,
    MetadataMixin,
    MetadataModel,
    QueryBuilder,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDMixin,
    create_model_dict,
    get_model_columns,
    get_model_relationships,
)

# Export all classes for backward compatibility
__all__ = [
    # Base classes
    "Base",
    "BaseModel",
    "AuditableModel", 
    "MetadataModel",
    "FullFeaturedModel",
    # Mixins
    "TimestampMixin",
    "UUIDMixin",
    "SoftDeleteMixin",
    "AuditMixin",
    "MetadataMixin",
    # Utilities
    "DatabaseSession",
    "QueryBuilder",
    "get_model_columns",
    "get_model_relationships",
    "create_model_dict",
]
