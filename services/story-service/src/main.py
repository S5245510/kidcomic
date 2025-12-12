"""
Story Service Main Application
Per T036 [US1]: FastAPI app with /health, /ready, /stories endpoints
Per T038 [US1]: Integrated with observability libraries (logging, metrics, tracing)
Per T103-T104 [US4]: Multi-version API support (v1 and v2)

Implements contracts/story-service-openapi.yml
Supports API versioning for backward compatibility
"""

import os
import sys
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import logging

# Import observability libraries
# Note: PYTHONPATH is set in start.sh to include /app/shared
from lib_logging.logger import configure_logging, get_logger, get_logger_with_trace
from lib_logging.metrics import get_metrics_app, MetricsMiddleware, set_service_health
from lib_tracing.tracer import configure_tracing, instrument_fastapi, get_current_trace_id

# Import config and health checks
from lib_config.config import load_env_config, get_config
from lib_config.database import get_database_manager
from lib_config.service_registry import register_service

# Import health endpoints
from .health import router as health_router, initialize_health_checks

# Import versioned API routers
from .api.v1 import router as v1_router
from .api.v2 import router as v2_router

# Configuration
SERVICE_NAME = "story-service"
SERVICE_VERSION = "v2.0.0"  # Updated for multi-version support
SERVICE_PORT = int(os.getenv("STORY_SERVICE_PORT", "8000"))

# Initialize configuration
load_env_config(".env")
config = get_config()

# Configure observability
configure_logging(
    service_name=SERVICE_NAME,
    log_level=config.get("LOG_LEVEL", "INFO"),
    log_format=config.get("LOG_FORMAT", "json")
)

configure_tracing(
    service_name=SERVICE_NAME,
    service_version=SERVICE_VERSION,
    trace_endpoint=config.get("TRACE_ENDPOINT", "http://tempo:4317"),
    enabled=config.get_bool("TRACING_ENABLED", True)
)

logger = get_logger(__name__)

# Initialize database manager
db_manager = get_database_manager(SERVICE_NAME)
initialize_health_checks(db_manager)

# Service registry instance (will be set during startup)
service_registry = None

# Create FastAPI app
app = FastAPI(
    title="Story Service",
    description="Manages children's stories and personalization",
    version=SERVICE_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add observability middleware
app.add_middleware(MetricsMiddleware, service_name=SERVICE_NAME)

# Instrument FastAPI with distributed tracing
instrument_fastapi(app)

# Include health check routes
app.include_router(health_router, tags=["Health"])

# Include versioned API routers
app.include_router(v1_router, tags=["API v1"])
app.include_router(v2_router, tags=["API v2"])

# Mount metrics endpoint
metrics_app = get_metrics_app()
app.mount("/metrics", metrics_app)


# Middleware for trace_id propagation
@app.middleware("http")
async def trace_id_middleware(request: Request, call_next):
    """
    Propagate trace_id from request headers
    Per FR-010: trace_id propagation
    """
    # Get trace_id from header or generate from current span
    trace_id = request.headers.get("X-Trace-ID") or get_current_trace_id()

    # Add to request state for access in route handlers
    request.state.trace_id = trace_id

    # Process request
    response = await call_next(request)

    # Add trace_id to response headers
    if trace_id:
        response.headers["X-Trace-ID"] = trace_id

    return response


@app.on_event("startup")
async def startup_event():
    """Service startup initialization"""
    global service_registry

    logger.info(f"Starting {SERVICE_NAME} v{SERVICE_VERSION}")

    # Register with Consul for service discovery
    try:
        service_registry = register_service(
            service_name=SERVICE_NAME,
            service_port=SERVICE_PORT,
            version=SERVICE_VERSION,
            environment=config.get("SERVICE_ENV", "development"),
            enable_prometheus_discovery=True
        )
        logger.info(f"Service registered with Consul for Prometheus discovery")
    except Exception as e:
        logger.warning(f"Failed to register with Consul: {e}")
        service_registry = None

    # Set service health to healthy
    set_service_health(SERVICE_NAME, healthy=True)

    logger.info(f"{SERVICE_NAME} started successfully on port {SERVICE_PORT}")


@app.on_event("shutdown")
async def shutdown_event():
    """Service shutdown cleanup"""
    logger.info(f"Shutting down {SERVICE_NAME}")

    # Set service health to unhealthy
    set_service_health(SERVICE_NAME, healthy=False)

    # Deregister from Consul
    if service_registry:
        try:
            service_registry.deregister()
            logger.info("Service deregistered from Consul")
        except Exception as e:
            logger.error(f"Failed to deregister from Consul: {e}")

    # Close database connections
    if db_manager:
        db_manager.close()

    logger.info(f"{SERVICE_NAME} shutdown complete")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint - API version discovery"""
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "status": "running",
        "api_versions": ["v1", "v2"],
        "endpoints": {
            "v1_stories": "/v1/stories",
            "v2_stories": "/v2/stories",
            "v2_search": "/v2/stories/search",
            "health": "/health",
            "ready": "/ready",
            "metrics": "/metrics",
            "docs": "/docs"
        },
        "breaking_changes_v2": [
            "StoryList uses 'data' instead of 'stories'",
            "Story uses 'body' instead of 'content'",
            "Added pagination metadata",
            "Added story search endpoint"
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=SERVICE_PORT,
        reload=True,
        log_level=config.get("LOG_LEVEL", "info").lower()
    )
