"""
Distributed Tracing Library
OpenTelemetry with Tempo exporter per FR-010, FR-014
"""

import os
from typing import Optional
from contextlib import contextmanager

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor


_tracer_provider: Optional[TracerProvider] = None
_configured = False


def configure_tracing(
    service_name: str,
    service_version: str = "v0.0.1",
    trace_endpoint: Optional[str] = None,
    enabled: bool = True
) -> TracerProvider:
    """
    Configure distributed tracing with OpenTelemetry and Tempo

    Args:
        service_name: Name of the service
        service_version: Version of the service
        trace_endpoint: Tempo OTLP endpoint (default: http://tempo:4317)
        enabled: Enable/disable tracing

    Returns:
        Configured TracerProvider
    """
    global _tracer_provider, _configured

    if _configured:
        return _tracer_provider

    if not enabled:
        # Use no-op tracer if disabled
        _tracer_provider = trace.get_tracer_provider()
        _configured = True
        return _tracer_provider

    # Create resource with service information
    resource = Resource.create({
        "service.name": service_name,
        "service.version": service_version,
        "deployment.environment": os.getenv("SERVICE_ENV", "development"),
    })

    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)

    # Configure OTLP exporter to Tempo
    endpoint = trace_endpoint or os.getenv("TRACE_ENDPOINT", "http://tempo:4317")
    otlp_exporter = OTLPSpanExporter(endpoint=endpoint, insecure=True)

    # Add batch span processor for performance
    span_processor = BatchSpanProcessor(otlp_exporter)
    _tracer_provider.add_span_processor(span_processor)

    # Set as global tracer provider
    trace.set_tracer_provider(_tracer_provider)

    _configured = True
    return _tracer_provider


def get_tracer(name: str = __name__) -> trace.Tracer:
    """
    Get a tracer instance

    Args:
        name: Tracer name (typically __name__)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)


@contextmanager
def trace_context(operation_name: str, **attributes):
    """
    Context manager for creating a trace span

    Args:
        operation_name: Name of the operation
        **attributes: Additional span attributes

    Example:
        with trace_context("fetch_story", story_id=123, user_id="user-456"):
            # ... operation code ...
            pass
    """
    tracer = get_tracer()
    with tracer.start_as_current_span(operation_name) as span:
        # Add attributes
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield span


def instrument_fastapi(app):
    """
    Instrument FastAPI app with automatic tracing

    Args:
        app: FastAPI application instance
    """
    FastAPIInstrumentor.instrument_app(app)


def get_current_trace_id() -> Optional[str]:
    """
    Get the current trace ID from active span

    Returns:
        Trace ID as hex string or None if no active span
    """
    current_span = trace.get_current_span()
    if current_span and current_span.get_span_context().is_valid:
        return format(current_span.get_span_context().trace_id, "032x")
    return None


def get_current_span_id() -> Optional[str]:
    """
    Get the current span ID from active span

    Returns:
        Span ID as hex string or None if no active span
    """
    current_span = trace.get_current_span()
    if current_span and current_span.get_span_context().is_valid:
        return format(current_span.get_span_context().span_id, "016x")
    return None
