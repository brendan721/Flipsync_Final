"""API response model."""

from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

# ApiError will be migrated later if needed
# from fs_agt_clean.core.utils.error import ApiError


class ApiResponse(BaseModel):
    """API response data model."""

    status: int
    success: bool = Field(default=True)
    message: str
    data: Optional[Dict[str, Any]] = None
    error: Optional[Union[str, Dict[str, Any]]] = None

    @property
    def status_code(self) -> int:
        """Get the status code.

        Returns:
            int: HTTP status code
        """
        return self.status

    @property
    def is_success(self) -> bool:
        """Check if response indicates success.

        Returns:
            bool: True if status code indicates success
        """
        return 200 <= self.status < 300

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary.

        Returns:
            Dict[str, Any]: Response as dictionary
        """
        return {
            "status": self.status,
            "success": self.success,
            "message": self.message,
            "data": self.data,
            "error": self.error,
        }

    class Config:
        """Pydantic config."""

        arbitrary_types_allowed = True
