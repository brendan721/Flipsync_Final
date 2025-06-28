"""
Unified Base Models for FlipSync Database
=========================================

This module consolidates all base database models into a single,
standardized hierarchy, eliminating duplication across:
- fs_agt_clean/database/models/base.py
- fs_agt_clean/core/models/database/base.py

AGENT_CONTEXT: Unified database base classes and common functionality
AGENT_PRIORITY: Database foundation with consistent patterns and utilities
AGENT_PATTERN: SQLAlchemy declarative base with common mixins and utilities
"""

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import Column, DateTime, String, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

# Create the unified declarative base
Base = declarative_base()


class TimestampMixin:
    """Mixin for adding timestamp fields to models"""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        nullable=False, 
        server_default=func.now(),
        comment="Record creation timestamp"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Record last update timestamp"
    )


class UUIDMixin:
    """Mixin for adding UUID primary key to models"""
    
    id: Mapped[str] = mapped_column(
        String(255), 
        primary_key=True, 
        default=lambda: str(uuid.uuid4()),
        comment="Unique identifier"
    )


class SoftDeleteMixin:
    """Mixin for adding soft delete functionality to models"""
    
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True,
        comment="Soft delete timestamp"
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
        comment="Soft delete flag"
    )
    
    def soft_delete(self):
        """Mark record as soft deleted"""
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self):
        """Restore soft deleted record"""
        self.is_deleted = False
        self.deleted_at = None


class AuditMixin:
    """Mixin for adding audit trail functionality to models"""
    
    created_by: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        comment="UnifiedUser who created the record"
    )
    updated_by: Mapped[Optional[str]] = mapped_column(
        String(255), 
        nullable=True,
        comment="UnifiedUser who last updated the record"
    )
    version: Mapped[int] = mapped_column(
        default=1,
        nullable=False,
        comment="Record version for optimistic locking"
    )


class MetadataMixin:
    """Mixin for adding metadata functionality to models"""
    
    metadata_json: Mapped[Optional[str]] = mapped_column(
        String,  # TEXT type for JSON storage
        nullable=True,
        comment="Additional metadata as JSON string"
    )
    tags: Mapped[Optional[str]] = mapped_column(
        String,  # TEXT type for JSON array storage
        nullable=True,
        comment="Tags as JSON array string"
    )


class BaseModel(Base, TimestampMixin, UUIDMixin):
    """
    Base model class with common functionality
    
    Provides:
    - UUID primary key
    - Timestamp tracking (created_at, updated_at)
    - Common utility methods
    """
    
    __abstract__ = True
    
    def to_dict(self, exclude: Optional[list] = None) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        exclude = exclude or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                # Handle datetime serialization
                if isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[list] = None):
        """Update model instance from dictionary"""
        exclude = exclude or ['id', 'created_at']
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)
    
    def __repr__(self):
        """Generic string representation"""
        return f"<{self.__class__.__name__}(id={self.id})>"


class AuditableModel(BaseModel, AuditMixin, SoftDeleteMixin):
    """
    Auditable model class with full audit trail
    
    Provides:
    - All BaseModel functionality
    - Audit trail (created_by, updated_by, version)
    - Soft delete functionality
    """
    
    __abstract__ = True
    
    def increment_version(self):
        """Increment version for optimistic locking"""
        self.version += 1


class MetadataModel(BaseModel, MetadataMixin):
    """
    Model class with metadata support
    
    Provides:
    - All BaseModel functionality
    - Metadata and tags support
    """
    
    __abstract__ = True
    
    def set_metadata(self, metadata: Dict[str, Any]):
        """Set metadata as JSON string"""
        import json
        self.metadata_json = json.dumps(metadata)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata from JSON string"""
        import json
        if self.metadata_json:
            try:
                return json.loads(self.metadata_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    def set_tags(self, tags: list):
        """Set tags as JSON array string"""
        import json
        self.tags = json.dumps(tags)
    
    def get_tags(self) -> list:
        """Get tags from JSON array string"""
        import json
        if self.tags:
            try:
                return json.loads(self.tags)
            except json.JSONDecodeError:
                return []
        return []


class FullFeaturedModel(AuditableModel, MetadataMixin):
    """
    Full-featured model class with all functionality
    
    Provides:
    - All BaseModel functionality
    - Audit trail
    - Soft delete
    - Metadata and tags support
    """
    
    __abstract__ = True


# Event listeners for automatic timestamp updates
@event.listens_for(BaseModel, 'before_update', propagate=True)
def receive_before_update(mapper, connection, target):
    """Update the updated_at timestamp before update"""
    target.updated_at = datetime.now(timezone.utc)


@event.listens_for(AuditableModel, 'before_update', propagate=True)
def receive_before_update_auditable(mapper, connection, target):
    """Increment version before update for auditable models"""
    target.increment_version()


# Utility functions for model operations
def get_model_columns(model_class) -> list:
    """Get list of column names for a model class"""
    return [column.name for column in model_class.__table__.columns]


def get_model_relationships(model_class) -> list:
    """Get list of relationship names for a model class"""
    return [rel.key for rel in model_class.__mapper__.relationships]


def create_model_dict(instance, include_relationships: bool = False) -> Dict[str, Any]:
    """Create dictionary from model instance with optional relationships"""
    result = instance.to_dict()
    
    if include_relationships:
        for rel_name in get_model_relationships(instance.__class__):
            rel_value = getattr(instance, rel_name, None)
            if rel_value is not None:
                if hasattr(rel_value, '__iter__') and not isinstance(rel_value, str):
                    # Handle collections
                    result[rel_name] = [
                        item.to_dict() if hasattr(item, 'to_dict') else str(item)
                        for item in rel_value
                    ]
                else:
                    # Handle single relationships
                    result[rel_name] = (
                        rel_value.to_dict() if hasattr(rel_value, 'to_dict') else str(rel_value)
                    )
    
    return result


# Database session utilities
class DatabaseSession:
    """Context manager for database sessions"""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session = None
    
    async def __aenter__(self):
        self.session = self.session_factory()
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            await self.session.rollback()
        else:
            await self.session.commit()
        await self.session.close()


# Query utilities
class QueryBuilder:
    """Utility class for building common queries"""
    
    @staticmethod
    def build_filter_query(model_class, filters: Dict[str, Any]):
        """Build a filtered query for a model"""
        query = model_class.query
        
        for field, value in filters.items():
            if hasattr(model_class, field):
                if isinstance(value, list):
                    query = query.filter(getattr(model_class, field).in_(value))
                else:
                    query = query.filter(getattr(model_class, field) == value)
        
        return query
    
    @staticmethod
    def build_search_query(model_class, search_term: str, search_fields: list):
        """Build a search query across multiple fields"""
        query = model_class.query
        
        if search_term and search_fields:
            conditions = []
            for field in search_fields:
                if hasattr(model_class, field):
                    conditions.append(
                        getattr(model_class, field).ilike(f"%{search_term}%")
                    )
            
            if conditions:
                from sqlalchemy import or_
                query = query.filter(or_(*conditions))
        
        return query


# Export all classes and utilities
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
