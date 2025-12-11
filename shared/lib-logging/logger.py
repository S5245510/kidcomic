"""
Structured Logging Library
Provides JSON-formatted logging with trace_id propagation per FR-009, FR-010, FR-015
"""

import logging
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter with trace_id support"""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO 8601 format (FR-010)
        log_record["timestamp"] = datetime.utcnow().isoformat() + "Z"

        # Add level
        log_record["level"] = record.levelname

        # Add service name from extra or default
        if not log_record.get("service"):
            log_record["service"] = getattr(record, "service", "unknown")

        # Add trace_id if available (FR-010)
        if hasattr(record, "trace_id"):
            log_record["trace_id"] = record.trace_id

        # Add span_id if available (distributed tracing)
        if hasattr(record, "span_id"):
            log_record["span_id"] = record.span_id

        # Ensure message is always present
        if not log_record.get("message"):
            log_record["message"] = record.getMessage()


def configure_logging(
    service_name: str,
    log_level: str = "INFO",
    log_format: str = "json"
) -> None:
    """
    Configure structured logging for a service

    Args:
        service_name: Name of the service (e.g., "story-service")
        log_level: Logging level (DEBUG, INFO, WARN, ERROR, CRITICAL)
        log_format: Format (json or text)
    """
    level = getattr(logging, log_level.upper(), logging.INFO)

    if log_format == "json":
        formatter = CustomJsonFormatter(
            fmt='%(timestamp)s %(level)s %(service)s %(trace_id)s %(message)s',
            rename_fields={"levelname": "level", "name": "logger"}
        )
    else:
        # Text format for local development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = []  # Remove existing handlers
    root_logger.addHandler(handler)

    # Set default service name for all log records
    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service = service_name
        return record

    logging.setLogRecordFactory(record_factory)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds trace_id and other contextual information
    to all log messages
    """

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        # Add extra fields from adapter's extra dict
        if "extra" not in kwargs:
            kwargs["extra"] = {}

        kwargs["extra"].update(self.extra)
        return msg, kwargs


def get_logger_with_trace(name: str, trace_id: Optional[str] = None, **extra_fields) -> LoggerAdapter:
    """
    Get a logger with trace_id and other contextual fields

    Args:
        name: Logger name
        trace_id: Trace ID for distributed tracing
        **extra_fields: Additional fields to include in all log messages

    Returns:
        LoggerAdapter with contextual fields

    Example:
        logger = get_logger_with_trace(__name__, trace_id="123-456", user_id="user-789")
        logger.info("Processing request", extra={"endpoint": "/stories/123"})
    """
    logger = logging.getLogger(name)
    extra = {"trace_id": trace_id or "no-trace-id", **extra_fields}
    return LoggerAdapter(logger, extra)
