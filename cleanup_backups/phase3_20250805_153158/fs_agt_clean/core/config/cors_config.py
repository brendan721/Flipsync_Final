"""
Centralized CORS Configuration for FlipSync
Consolidates all CORS settings to eliminate redundancy and confusion.
Uses environment variables for production security.
"""

import os
from fastapi.middleware.cors import CORSMiddleware


def get_cors_origins():
    """Get CORS origins from environment variables with secure defaults."""
    # Get environment-specific origins
    env_origins = os.getenv("CORS_ORIGINS", "")
    if env_origins:
        return [origin.strip() for origin in env_origins.split(",") if origin.strip()]

    # Default production origins if no environment variable set
    default_origins = [
        "https://flipsyncai.com",
        "https://www.flipsyncai.com",
    ]

    # Add development origins only in development mode
    if os.getenv("ENVIRONMENT", "production").lower() in [
        "development",
        "dev",
        "local",
    ]:
        dev_origins = [
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
        ]
        default_origins.extend(dev_origins)

    return default_origins


# Get CORS origins dynamically (called at runtime, not import time)
def get_cors_origins_runtime():
    """Get CORS origins at runtime to ensure environment variables are loaded."""
    return get_cors_origins()


CORS_ORIGINS = get_cors_origins_runtime()

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
    Gets origins at runtime to ensure environment variables are loaded.
    """
    # Get origins at runtime to ensure environment variables are loaded
    runtime_origins = get_cors_origins()

    return CORSMiddleware, {
        "allow_origins": runtime_origins,
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
