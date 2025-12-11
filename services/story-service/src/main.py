"""
Story Service Main Application
Per T036 [US1]: FastAPI app with /health, /ready, /stories endpoints
Per T038 [US1]: Integrated with observability libraries (logging, metrics, tracing)

Implements contracts/story-service-openapi.yml
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

# Configuration
SERVICE_NAME = "story-service"
SERVICE_VERSION = "v0.1.0"
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

# Mount metrics endpoint
metrics_app = get_metrics_app()
app.mount("/metrics", metrics_app)


# Data Models
class Story(BaseModel):
    """Story model"""
    id: int
    title: str
    content: str
    age_range: str = Field(..., description="Target age range (e.g., '3-5', '6-8')")
    moral_lesson: Optional[str] = None
    created_at: Optional[str] = None


class StoryList(BaseModel):
    """List of stories"""
    stories: List[Story]
    total: int


# In-memory story data (stub - will be replaced with database in Phase 2)
SAMPLE_STORIES = [
    Story(
        id=1,
        title="The Brave Little Turtle",
        content="Once upon a time, there was a brave little turtle who lived by the sea...",
        age_range="3-5",
        moral_lesson="Courage comes in all sizes",
        created_at="2024-01-01T00:00:00Z"
    ),
    Story(
        id=2,
        title="The Magic Paintbrush",
        content="In a small village, there lived a young artist who discovered a magic paintbrush...",
        age_range="6-8",
        moral_lesson="Use your talents to help others",
        created_at="2024-01-02T00:00:00Z"
    ),
    Story(
        id=3,
        title="The Friendly Dragon",
        content="High in the mountains lived a dragon who just wanted to make friends...",
        age_range="4-6",
        moral_lesson="Don't judge by appearances",
        created_at="2024-01-03T00:00:00Z"
    )
]


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


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "status": "running",
        "endpoints": {
            "stories": "/stories/",
            "story_detail": "/stories/{story_id}",
            "health": "/health",
            "ready": "/ready",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }


@app.get("/stories/", response_model=StoryList)
async def list_stories(
    request: Request,
    age_range: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List all stories

    Per contracts/story-service-openapi.yml: GET /stories/
    """
    trace_id = getattr(request.state, "trace_id", None)
    logger_ctx = get_logger_with_trace(__name__, trace_id=trace_id)

    logger_ctx.info(
        "Listing stories",
        extra={"age_range": age_range, "limit": limit, "offset": offset}
    )

    # Filter by age_range if provided
    stories = SAMPLE_STORIES
    if age_range:
        stories = [s for s in stories if s.age_range == age_range]

    # Apply pagination
    total = len(stories)
    stories = stories[offset:offset + limit]

    logger_ctx.info(f"Returning {len(stories)} stories (total: {total})")

    return StoryList(stories=stories, total=total)


@app.get("/stories/{story_id}", response_model=Story)
async def get_story(request: Request, story_id: int):
    """
    Get a specific story by ID

    Per contracts/story-service-openapi.yml: GET /stories/{story_id}
    """
    trace_id = getattr(request.state, "trace_id", None)
    logger_ctx = get_logger_with_trace(__name__, trace_id=trace_id)

    logger_ctx.info(f"Fetching story", extra={"story_id": story_id})

    # Find story
    story = next((s for s in SAMPLE_STORIES if s.id == story_id), None)

    if not story:
        logger_ctx.warning(f"Story not found", extra={"story_id": story_id})
        raise HTTPException(status_code=404, detail=f"Story {story_id} not found")

    logger_ctx.info(f"Story found", extra={"story_id": story_id, "title": story.title})

    return story


@app.post("/stories/{story_id}/personalize")
async def personalize_story(
    request: Request,
    story_id: int,
    child_name: str,
    child_photo_url: Optional[str] = None
):
    """
    Personalize a story with child's name and photo

    Per contracts/story-service-openapi.yml: POST /stories/{story_id}/personalize
    """
    trace_id = getattr(request.state, "trace_id", None)
    logger_ctx = get_logger_with_trace(__name__, trace_id=trace_id)

    logger_ctx.info(
        "Personalizing story",
        extra={"story_id": story_id, "child_name": child_name}
    )

    # Find story
    story = next((s for s in SAMPLE_STORIES if s.id == story_id), None)

    if not story:
        raise HTTPException(status_code=404, detail=f"Story {story_id} not found")

    # Personalize content (simple replacement for MVP)
    personalized_content = story.content.replace("little", child_name)

    logger_ctx.info(f"Story personalized successfully", extra={"story_id": story_id})

    return {
        "story_id": story_id,
        "title": story.title,
        "personalized_content": personalized_content,
        "child_name": child_name,
        "trace_id": trace_id
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
