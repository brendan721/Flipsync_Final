# AGENT_CONTEXT: main - Core FlipSync component with established patterns
"""Main entry point for the FlipSync application."""

import logging
import os
from typing import Dict

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="FlipSync API",
    description="API for the FlipSync agentic architecture",
    version="0.1.0",
)

# Import centralized CORS configuration
from fs_agt_clean.core.config.cors_config import get_cors_middleware

# Configure CORS with centralized, production-ready settings
cors_middleware_class, cors_settings = get_cors_middleware()
app.add_middleware(cors_middleware_class, **cors_settings)


@app.get("/api/v1/health", response_model=Dict[str, str])
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on startup."""
    logger.info("Starting FlipSync API")
    # Initialize services here


@app.on_event("shutdown")
async def shutdown_event() -> None:
    """Clean up resources on shutdown."""
    logger.info("Shutting down FlipSync API")
    # Clean up resources here


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("fs_agt_clean.main:app", host="0.0.0.0", port=port, reload=True)
