"""
UnifiedUser models compatibility module.

This module provides backward compatibility for imports that expect
user models to be in fs_agt_clean.core.models.user.
"""

# Import all user models from the actual location
from fs_agt_clean.database.models.unified_user import *
