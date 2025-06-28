"""Error handling for FastAPI application."""

import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from fs_agt_clean.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    DatabaseError,
    ExternalServiceError,
    FlipSyncError,
    RateLimitError,
)
from fs_agt_clean.core.exceptions import ValidationError as FlipSyncValidationError

logger = logging.getLogger(__name__)


async def validation_exception_handler(
    request: Request, exc: ValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(f"Validation error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": "Invalid input data",
            "details": exc.errors(),
        },
    )


async def flipsync_validation_exception_handler(
    request: Request, exc: FlipSyncValidationError
) -> JSONResponse:
    """Handle FlipSync validation errors."""
    logger.warning(f"FlipSync validation error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": "Validation Error",
            "message": str(exc),
            "field": exc.field,
            "value": exc.value,
        },
    )


async def authentication_exception_handler(
    request: Request, exc: AuthenticationError
) -> JSONResponse:
    """Handle authentication errors."""
    logger.warning(f"Authentication error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": "Authentication Error",
            "message": str(exc),
        },
    )


async def authorization_exception_handler(
    request: Request, exc: AuthorizationError
) -> JSONResponse:
    """Handle authorization errors."""
    logger.warning(f"Authorization error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": "Authorization Error",
            "message": str(exc),
        },
    )


async def rate_limit_exception_handler(
    request: Request, exc: RateLimitError
) -> JSONResponse:
    """Handle rate limit errors."""
    logger.warning(f"Rate limit error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": "Rate Limit Exceeded",
            "message": str(exc),
        },
    )


async def database_exception_handler(
    request: Request, exc: DatabaseError
) -> JSONResponse:
    """Handle database errors."""
    logger.error(f"Database error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Database Error",
            "message": "A database error occurred",
        },
    )


async def external_service_exception_handler(
    request: Request, exc: ExternalServiceError
) -> JSONResponse:
    """Handle external service errors."""
    logger.error(f"External service error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": "External Service Error",
            "message": "An external service is unavailable",
        },
    )


async def configuration_exception_handler(
    request: Request, exc: ConfigurationError
) -> JSONResponse:
    """Handle configuration errors."""
    logger.error(f"Configuration error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Configuration Error",
            "message": "A configuration error occurred",
        },
    )


async def flipsync_exception_handler(
    request: Request, exc: FlipSyncError
) -> JSONResponse:
    """Handle general FlipSync errors."""
    logger.error(f"FlipSync error on {request.url}: {exc}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "FlipSync Error",
            "message": str(exc),
            "details": exc.details,
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions."""
    logger.warning(f"HTTP exception on {request.url}: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": "HTTP Error",
            "message": exc.detail,
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle general exceptions."""
    logger.error(f"Unhandled exception on {request.url}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
        },
    )


def setup_error_handlers(app: FastAPI) -> None:
    """Set up error handlers for the FastAPI application."""
    # Pydantic validation errors
    app.add_exception_handler(ValidationError, validation_exception_handler)

    # FlipSync specific errors
    app.add_exception_handler(
        FlipSyncValidationError, flipsync_validation_exception_handler
    )
    app.add_exception_handler(AuthenticationError, authentication_exception_handler)
    app.add_exception_handler(AuthorizationError, authorization_exception_handler)
    app.add_exception_handler(RateLimitError, rate_limit_exception_handler)
    app.add_exception_handler(DatabaseError, database_exception_handler)
    app.add_exception_handler(ExternalServiceError, external_service_exception_handler)
    app.add_exception_handler(ConfigurationError, configuration_exception_handler)
    app.add_exception_handler(FlipSyncError, flipsync_exception_handler)

    # HTTP exceptions
    app.add_exception_handler(HTTPException, http_exception_handler)

    # General exceptions (catch-all)
    app.add_exception_handler(Exception, general_exception_handler)

    logger.info("Error handlers configured successfully")
