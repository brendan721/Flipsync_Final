"""OpenAPI documentation configuration for the FlipSync API.

This module configures the OpenAPI documentation for the FastAPI app,
enhancing the automatically generated docs with additional information,
examples, and customizations.
"""

from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi


def custom_openapi(app: FastAPI):
    """
    Generate custom OpenAPI schema for the application.

    This function enhances the automatically generated OpenAPI schema
    with additional information like examples, descriptions, and tags.

    Args:
        app: The FastAPI application instance

    Returns:
        dict: The customized OpenAPI schema
    """
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="FlipSync API",
        version="1.0.0",
        description="""
        # FlipSync API Documentation

        This API provides access to the FlipSync UnifiedAgent System, allowing you to manage
        marketplace listings, inventory, orders, and agent configurations.

        ## Authentication

        All API endpoints require authentication using an API key or OAuth2 token.
        Include the token in the Authorization header as follows:

        ```
        Authorization: Bearer YOUR_API_TOKEN
        ```

        ## Rate Limiting

        API calls are limited to:
        - 100 requests per minute for standard accounts
        - 250 requests per minute for premium accounts

        Exceeding these limits will result in HTTP 429 (Too Many Requests) responses.

        ## Errors

        The API uses conventional HTTP response codes to indicate success or failure:
        - 2xx: Success
        - 4xx: Client errors (invalid request)
        - 5xx: Server errors

        All error responses include a JSON object with:
        - `error`: Error type/code
        - `message`: Human-readable error message
        - `details`: Additional details about the error (when available)
        """,
        routes=app.routes,
    )

    # Add components section if it doesn't exist
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    # Add authentication schemes
    if "securitySchemes" not in openapi_schema["components"]:
        openapi_schema["components"]["securitySchemes"] = {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": 'Enter the token with the `Bearer: ` prefix, e.g. "Bearer abcde12345".',
            },
            "APIKeyHeader": {
                "type": "apiKey",
                "in": "header",
                "name": "X-API-Key",
                "description": "API key for authentication",
            },
        }

    # Add global security requirement
    openapi_schema["security"] = [{"bearerAuth": []}]

    # Add tags metadata
    openapi_schema["tags"] = [
        {
            "name": "agents",
            "description": "Operations related to agent management and configuration",
        },
        {"name": "health", "description": "Health and status endpoints"},
        {
            "name": "inventory",
            "description": "Inventory management across marketplaces",
        },
        {
            "name": "marketplaces",
            "description": "Marketplace connections and operations",
        },
        {"name": "monitoring", "description": "System monitoring endpoints"},
        {"name": "sales", "description": "Sales and order management"},
    ]

    # Enhanced examples for specific endpoints (add as needed)
    if "paths" in openapi_schema:
        # Example for marketplace listing endpoint
        if "/marketplaces" in openapi_schema["paths"]:
            if "get" in openapi_schema["paths"]["/marketplaces"]:
                openapi_schema["paths"]["/marketplaces"]["get"]["responses"]["200"][
                    "content"
                ]["application/json"]["examples"] = {
                    "success": {
                        "summary": "List of connected marketplaces",
                        "value": {
                            "marketplaces": [
                                {
                                    "id": "amazon",
                                    "name": "Amazon",
                                    "connected": True,
                                    "products_count": 125,
                                    "last_sync": "2023-04-01T12:00:00Z",
                                },
                                {
                                    "id": "ebay",
                                    "name": "eBay",
                                    "connected": True,
                                    "products_count": 87,
                                    "last_sync": "2023-04-01T10:00:00Z",
                                },
                            ]
                        },
                    }
                }

    # Set the schemas
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def load_consolidated_openapi():
    """
    Load the consolidated OpenAPI schema from file.

    Returns:
        dict: The consolidated OpenAPI schema
    """
    import json
    import logging
    import os
    from pathlib import Path

    logger = logging.getLogger(__name__)

    # Try to load the optimized schema first
    schema_path = (
        Path(__file__).parent.parent.parent / "docs" / "api" / "optimized_openapi.json"
    )

    if os.path.exists(schema_path):
        logger.info(f"Using optimized OpenAPI schema from {schema_path}")
    else:
        # Fall back to the full OpenAPI schema
        schema_path = (
            Path(__file__).parent.parent.parent / "docs" / "api" / "full_openapi.json"
        )

        # Check if the file exists
        if not os.path.exists(schema_path):
            # Fall back to the consolidated schema
            schema_path = (
                Path(__file__).parent.parent.parent
                / "docs"
                / "api"
                / "consolidated_openapi.json"
            )
            if not os.path.exists(schema_path):
                raise FileNotFoundError(f"OpenAPI schema not found at {schema_path}")

    # Load the schema
    with open(schema_path, "r") as f:
        schema = json.load(f)

    return schema


def setup_openapi(app: FastAPI):
    """
    Set up OpenAPI documentation for the FastAPI app.

    Args:
        app: The FastAPI application instance
    """
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Try to load the consolidated schema
        consolidated_schema = load_consolidated_openapi()

        # Log the original openapi method type
        logger.info(f"Original openapi method type: {type(app.openapi).__name__}")

        # Define a new openapi method that always returns our schema
        def get_openapi():
            logger.info("Using consolidated OpenAPI schema")
            return consolidated_schema

        # Replace the app's openapi method
        app.openapi = get_openapi

        # Also set the openapi_schema for good measure
        app.openapi_schema = consolidated_schema

        logger.info("Successfully loaded consolidated OpenAPI schema")

    except Exception as e:
        # Fall back to the custom schema if loading fails
        logger.error(f"Failed to load consolidated OpenAPI schema: {str(e)}")
        logger.info("Falling back to dynamically generated OpenAPI schema")
        app.openapi = lambda: custom_openapi(app)
