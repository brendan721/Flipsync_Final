"""Database module for FlipSync."""

from .database import Database, get_database
from .init_webhook_db import init_webhook_db

__all__ = [
    "Database",
    "get_database",
    "init_webhook_db",
]
