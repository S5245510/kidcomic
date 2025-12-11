"""
Health Check Endpoints
Per T037 [US1]: Liveness and readiness checks per FR-034
"""

from fastapi import APIRouter, Response, status
from typing import Dict, Any
import sys
import os

# Add shared libraries to path
#sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', 'shared'))

from lib_config.health_checks import create_liveness_check, create_readiness_check
from lib_config.database import get_database_manager

router = APIRouter()

# Initialize health checks
liveness = create_liveness_check()
readiness = create_readiness_check()

# Global database manager (will be initialized by main.py)
db_manager = None


def initialize_health_checks(database_manager):
    """
    Initialize health checks with dependencies

    Args:
        database_manager: Database manager instance
    """
    global db_manager
    db_manager = database_manager

    # Add readiness checks
    readiness.add_check(
        "database",
        lambda: db_manager.check_health() if db_manager else False
    )


@router.get("/health")
async def health() -> Dict[str, Any]:
    """
    Liveness probe - checks if service should be restarted

    Returns 200 if service is alive (process running, not deadlocked)
    Returns 503 if service should be restarted

    Per FR-034: Liveness check
    """
    result = liveness.check_all()

    if result["status"] == "healthy":
        return result
    else:
        return Response(
            content=result,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@router.get("/ready")
async def ready() -> Dict[str, Any]:
    """
    Readiness probe - checks if service can handle traffic

    Returns 200 if service is ready to accept requests
    Returns 503 if service is not ready (dependencies unavailable)

    Per FR-034: Readiness check
    """
    result = readiness.check_all()

    if result["status"] == "healthy":
        return result
    else:
        return Response(
            content=result,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )


@router.get("/healthz")
async def healthz() -> Dict[str, str]:
    """
    Kubernetes-style health check (alias for /health)
    """
    result = liveness.check_all()
    if result["status"] == "healthy":
        return {"status": "ok"}
    else:
        return Response(
            content={"status": "unhealthy"},
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE
        )
