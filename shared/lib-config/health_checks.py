"""
Health Check Framework
Liveness and readiness probes per FR-034
"""

from typing import List, Callable, Dict, Any
from enum import Enum
import time


class HealthStatus(Enum):
    """Health check status"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class HealthCheck:
    """Base health check"""

    def __init__(self, name: str, check_fn: Callable[[], bool]):
        self.name = name
        self.check_fn = check_fn
        self.last_check_time: float = 0
        self.last_status: HealthStatus = HealthStatus.HEALTHY

    def check(self) -> Dict[str, Any]:
        """
        Run health check

        Returns:
            Health check result with status, timestamp, and details
        """
        start_time = time.time()
        try:
            is_healthy = self.check_fn()
            status = HealthStatus.HEALTHY if is_healthy else HealthStatus.UNHEALTHY
        except Exception as e:
            status = HealthStatus.UNHEALTHY
            return {
                "name": self.name,
                "status": status.value,
                "timestamp": time.time(),
                "duration_ms": (time.time() - start_time) * 1000,
                "error": str(e)
            }

        self.last_check_time = time.time()
        self.last_status = status

        return {
            "name": self.name,
            "status": status.value,
            "timestamp": self.last_check_time,
            "duration_ms": (self.last_check_time - start_time) * 1000
        }


class LivenessCheck:
    """
    Liveness probe - checks if service should be restarted

    Example checks:
    - Process is running
    - Not deadlocked
    - Core components initialized
    """

    def __init__(self):
        self.checks: List[HealthCheck] = []

    def add_check(self, name: str, check_fn: Callable[[], bool]) -> None:
        """Add a liveness check"""
        self.checks.append(HealthCheck(name, check_fn))

    def check_all(self) -> Dict[str, Any]:
        """
        Run all liveness checks

        Returns:
            Aggregated health status
        """
        if not self.checks:
            return {
                "status": HealthStatus.HEALTHY.value,
                "checks": [],
                "timestamp": time.time()
            }

        results = [check.check() for check in self.checks]
        all_healthy = all(r["status"] == HealthStatus.HEALTHY.value for r in results)

        return {
            "status": HealthStatus.HEALTHY.value if all_healthy else HealthStatus.UNHEALTHY.value,
            "checks": results,
            "timestamp": time.time()
        }


class ReadinessCheck:
    """
    Readiness probe - checks if service can handle traffic

    Example checks:
    - Database connection active
    - Required dependencies available
    - Warm-up completed
    """

    def __init__(self):
        self.checks: List[HealthCheck] = []

    def add_check(self, name: str, check_fn: Callable[[], bool]) -> None:
        """Add a readiness check"""
        self.checks.append(HealthCheck(name, check_fn))

    def check_all(self) -> Dict[str, Any]:
        """
        Run all readiness checks

        Returns:
            Aggregated readiness status
        """
        if not self.checks:
            return {
                "status": HealthStatus.HEALTHY.value,
                "checks": [],
                "timestamp": time.time()
            }

        results = [check.check() for check in self.checks]
        all_healthy = all(r["status"] == HealthStatus.HEALTHY.value for r in results)

        return {
            "status": HealthStatus.HEALTHY.value if all_healthy else HealthStatus.UNHEALTHY.value,
            "checks": results,
            "timestamp": time.time()
        }


# Convenience functions for FastAPI integration
def create_liveness_check() -> LivenessCheck:
    """Create a liveness check instance"""
    liveness = LivenessCheck()
    # Add default check - service is alive if this code executes
    liveness.add_check("process_alive", lambda: True)
    return liveness


def create_readiness_check() -> ReadinessCheck:
    """Create a readiness check instance"""
    return ReadinessCheck()
