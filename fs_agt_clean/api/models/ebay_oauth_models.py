"""
Pydantic models for eBay OAuth API requests and responses.

These models provide clean, validated data structures for the eBay OAuth
endpoints, designed for Flutter frontend integration.
"""

from datetime import datetime
from typing import List, Optional, Any, Dict
from pydantic import BaseModel, Field


class EbayOAuthAuthorizeRequest(BaseModel):
    """Request model for eBay OAuth authorization."""
    
    user_id: str = Field(..., description="User identifier for credential mapping")
    scopes: Optional[List[str]] = Field(
        default=[
            "https://api.ebay.com/oauth/api_scope",
            "https://api.ebay.com/oauth/api_scope/sell.inventory",
            "https://api.ebay.com/oauth/api_scope/sell.account",
            "https://api.ebay.com/oauth/api_scope/sell.fulfillment",
            "https://api.ebay.com/oauth/api_scope/sell.marketing"
        ],
        description="eBay API scopes to request"
    )


class EbayOAuthAuthorizeResponse(BaseModel):
    """Response model for eBay OAuth authorization."""
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Dict[str, Any] = Field(..., description="Response data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "OAuth authorization URL generated successfully",
                "data": {
                    "authorization_url": "https://auth.ebay.com/oauth2/authorize?...",
                    "state": "abc123...",
                    "user_id": "testuser",
                    "environment": "sandbox",
                    "expires_in": 600
                }
            }
        }


class EbayOAuthCallbackRequest(BaseModel):
    """Request model for eBay OAuth callback."""
    
    code: str = Field(..., description="Authorization code from eBay")
    state: str = Field(..., description="State parameter for validation")


class EbayOAuthCallbackResponse(BaseModel):
    """Response model for eBay OAuth callback."""
    
    success: bool = Field(..., description="Whether the callback was successful")
    message: str = Field(..., description="Response message")
    data: Dict[str, Any] = Field(..., description="Response data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "eBay OAuth completed successfully",
                "data": {
                    "user_id": "testuser",
                    "environment": "sandbox",
                    "token_type": "Bearer",
                    "expires_in": 7200,
                    "scopes": ["https://api.ebay.com/oauth/api_scope"],
                    "connected": True
                }
            }
        }


class EbayOAuthStatusResponse(BaseModel):
    """Response model for eBay OAuth status."""
    
    success: bool = Field(..., description="Whether the request was successful")
    message: str = Field(..., description="Response message")
    data: Dict[str, Any] = Field(..., description="Authentication status data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Authentication status retrieved",
                "data": {
                    "authenticated": True,
                    "user_id": "testuser",
                    "environment": "sandbox",
                    "token_type": "Bearer",
                    "expires_at": "2024-08-06T20:00:00Z",
                    "scopes": ["https://api.ebay.com/oauth/api_scope"],
                    "message": "Authentication valid"
                }
            }
        }


class EbayOAuthRefreshResponse(BaseModel):
    """Response model for eBay OAuth token refresh."""
    
    success: bool = Field(..., description="Whether the refresh was successful")
    message: str = Field(..., description="Response message")
    data: Dict[str, Any] = Field(..., description="Refreshed token data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Tokens refreshed successfully",
                "data": {
                    "user_id": "testuser",
                    "environment": "sandbox",
                    "token_type": "Bearer",
                    "expires_at": "2024-08-06T22:00:00Z",
                    "scopes": ["https://api.ebay.com/oauth/api_scope"]
                }
            }
        }


class EbayOAuthRevokeResponse(BaseModel):
    """Response model for eBay OAuth token revocation."""
    
    success: bool = Field(..., description="Whether the revocation was successful")
    message: str = Field(..., description="Response message")
    data: Dict[str, Any] = Field(..., description="Revocation result data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Tokens revoked successfully",
                "data": {
                    "user_id": "testuser",
                    "revoked": True
                }
            }
        }


class EbayOAuthErrorResponse(BaseModel):
    """Response model for eBay OAuth errors."""
    
    success: bool = Field(False, description="Always false for error responses")
    message: str = Field(..., description="Error message")
    error: str = Field(..., description="Error type")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional error data")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "OAuth authorization failed",
                "error": "invalid_state",
                "data": {
                    "user_id": "testuser",
                    "error_details": "State parameter expired or invalid"
                }
            }
        }


class WebSocketOAuthStatusMessage(BaseModel):
    """WebSocket message model for OAuth status updates."""
    
    type: str = Field("oauth_status", description="Message type")
    user_id: str = Field(..., description="User identifier")
    authenticated: bool = Field(..., description="Authentication status")
    environment: Optional[str] = Field(None, description="eBay environment")
    expires_at: Optional[datetime] = Field(None, description="Token expiry time")
    message: str = Field(..., description="Status message")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Message timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "type": "oauth_status",
                "user_id": "testuser",
                "authenticated": True,
                "environment": "sandbox",
                "expires_at": "2024-08-06T20:00:00Z",
                "message": "eBay authentication successful",
                "timestamp": "2024-08-06T18:00:00Z"
            }
        }
