"""
Base SQLAlchemy model configuration.

This module provides the unified base SQLAlchemy model configuration used across all database models.
It imports the Base from the main database models to ensure consistency.
"""

# Import the unified Base from the main database models
from fs_agt_clean.database.models.base import Base

__all__ = ["Base"]
