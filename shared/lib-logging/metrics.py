"""
Prometheus Metrics Library
Provides standardized metrics for all microservices per FR-011, FR-012
"""

from prometheus_client import Counter, Histogram, Gauge, make_asgi_app
from typing import List


# Standard HTTP metrics that all services should export

REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['service', 'method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['service', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0)  # Customized for API services
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_in_flight',
    'Active HTTP requests currently being processed',
    ['service']
)

SERVICE_HEALTH = Gauge(
    'service_health',
    'Service health status (1=healthy, 0=unhealthy)',
    ['service']
)

SERVICE_ERRORS = Counter(
    'service_errors_total',
    'Total service errors by type',
    ['service', 'error_type', 'severity']
)

DEPENDENCY_HEALTH = Gauge(
    'service_dependency_health',
    'Service dependency health status (1=healthy, 0=unhealthy)',
    ['service', 'dependency']
)


def get_metrics_app():
    """
    Get ASGI app for exposing Prometheus metrics at /metrics endpoint

    Returns:
        ASGI app that serves metrics in Prometheus format

    Example:
        app = FastAPI()
        metrics_app = get_metrics_app()
        app.mount("/metrics", metrics_app)
    """
    return make_asgi_app()


class MetricsMiddleware:
    """
    Middleware for automatically tracking HTTP metrics

    Example:
        from fastapi import FastAPI
        app = FastAPI()
        app.add_middleware(MetricsMiddleware, service_name="story-service")
    """

    def __init__(self, app, service_name: str):
        self.app = app
        self.service_name = service_name

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        # Track active requests
        ACTIVE_REQUESTS.labels(service=self.service_name).inc()

        import time
        start_time = time.time()

        # Track response status
        status_code = 500  # Default to error if something goes wrong

        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            # Record metrics
            duration = time.time() - start_time
            method = scope["method"]
            path = scope["path"]

            REQUEST_COUNT.labels(
                service=self.service_name,
                method=method,
                endpoint=path,
                status=status_code
            ).inc()

            REQUEST_LATENCY.labels(
                service=self.service_name,
                endpoint=path
            ).observe(duration)

            ACTIVE_REQUESTS.labels(service=self.service_name).dec()


def record_error(service_name: str, error_type: str, severity: str = "error"):
    """
    Record a service error

    Args:
        service_name: Name of the service
        error_type: Type of error (e.g., "database", "api", "validation")
        severity: Severity level (e.g., "warning", "error", "critical")
    """
    SERVICE_ERRORS.labels(
        service=service_name,
        error_type=error_type,
        severity=severity
    ).inc()


def set_service_health(service_name: str, healthy: bool):
    """
    Set service health status

    Args:
        service_name: Name of the service
        healthy: True if healthy, False if unhealthy
    """
    SERVICE_HEALTH.labels(service=service_name).set(1 if healthy else 0)


def set_dependency_health(service_name: str, dependency: str, healthy: bool):
    """
    Set dependency health status

    Args:
        service_name: Name of the service
        dependency: Name of the dependency (e.g., "database", "payment-service")
        healthy: True if healthy, False if unhealthy
    """
    DEPENDENCY_HEALTH.labels(
        service=service_name,
        dependency=dependency
    ).set(1 if healthy else 0)
