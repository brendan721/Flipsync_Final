"""
Centralized CORS Configuration for FlipSync
Consolidates all CORS settings to eliminate redundancy and confusion.
"""

from fastapi.middleware.cors import CORSMiddleware
import os

# Comprehensive CORS Origins for all environments
CORS_ORIGINS = [
    # Development origins
    "http://localhost:3000",  # Flutter web app (primary)
    "http://localhost:3001",  # Flutter web app (current)
    "http://127.0.0.1:3000",  # Local loopback
    "http://127.0.0.1:3001",  # Local loopback
    "http://localhost:8080",  # API documentation
    "http://localhost:8081",  # Flutter web app
    "http://localhost:8082",  # Flutter web app (alternate port)
    "http://10.0.2.2:3000",  # Android emulator
    "http://0.0.0.0:3000",  # All interfaces
    # Production origins
    "https://flipsync.app",  # Production domain
    "https://www.flipsync.app",  # Production www domain
    "https://api.flipsync.app",  # Production API domain
    "https://mobile.flipsync.app",  # Production mobile domain
    # External OAuth domains
    "https://nashvillegeneral.store",  # External OAuth domain
    "https://www.nashvillegeneral.store",  # External OAuth domain with www
]

# WebSocket CORS Origins
WEBSOCKET_CORS_ORIGINS = CORS_ORIGINS

# CORS Headers
CORS_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# CORS Methods
CORS_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]


def get_cors_middleware():
    """
    Returns configured CORS middleware class and settings for FlipSync.
    This is the single source of truth for CORS configuration.
    """
    return CORSMiddleware, {
        "allow_origins": CORS_ORIGINS,
        "allow_credentials": True,
        "allow_methods": CORS_METHODS,
        "allow_headers": CORS_HEADERS,
        "expose_headers": ["*"],
        "max_age": 600,
    }


# Legacy settings for backward compatibility (DEPRECATED)
DEVELOPMENT_CORS_SETTINGS = {
    "allow_origins": CORS_ORIGINS,
    "allow_credentials": True,
    "allow_methods": CORS_METHODS,
    "allow_headers": CORS_HEADERS,
}
