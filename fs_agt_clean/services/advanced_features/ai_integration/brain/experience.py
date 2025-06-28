from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Optional

"Experience module for brain functionality."


@dataclass
class Experience:
    """Experience data structure."""

    id: str
    type: str
    content: Dict
    context: Dict
    created_at: datetime
    metadata: Optional[Dict] = None
    importance: float = 0.0

    def __post_init__(self):
        """Initialize experience."""
        if not self.id:
            self.id = f"exp_{datetime.now().timestamp()}"
        if not self.created_at:
            self.created_at = datetime.now()
