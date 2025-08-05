"""UnifiedUser management API routes package."""

# Import the main router from the parent users.py file
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

try:
    from ..users import router
except ImportError:
    # Fallback: create a simple router if the main users.py has issues
    from fastapi import APIRouter

    router = APIRouter(prefix="/users", tags=["users"])
