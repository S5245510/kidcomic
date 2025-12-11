# Observability Contract

**Purpose**: Defines requirements for all microservices to participate in unified observability stack (Prometheus, Grafana, Loki, Tempo)

**Version**: 1.0.0
**Last Updated**: 2025-12-05

---

## 1. Metrics Exposure (FR-011, FR-012)

All services MUST expose Prometheus metrics at `/metrics` endpoint.

### Required Metrics

**HTTP Request Metrics**:
```python
# Counter: Total HTTP requests by method, endpoint, status
http_requests_total{service="story-service", method="GET", endpoint="/stories", status="200"}

# Histogram: Request duration in seconds
http_request_duration_seconds{service="story-service", endpoint="/stories"}

# Gauge: Active requests currently being processed
http_requests_in_flight{service="story-service"}
```

**Service Health Metrics**:
```python
# Gauge: Service health status (1 = healthy, 0 = unhealthy)
service_health{service="story-service"}

# Counter: Service errors by type
service_errors_total{service="story-service", error_type="database", severity="critical"}

# Gauge: Service dependencies health
service_dependency_health{service="story-service", dependency="payment-service"}
```

**Business Metrics** (service-specific):
```python
# Example for Story Service
stories_created_total{service="story-service", tier="free|subscriber"}
stories_viewed_total{service="story-service", personalized="true|false"}
personalization_requests_total{service="story-service", status="success|failed"}
```

### Metric Naming Conventions

- Use snake_case for metric names
- Include service name as label: `{service="service-name"}`
- Counter metrics end with `_total`
- Histogram/Summary metrics end with unit (`_seconds`, `_bytes`)
- Gauge metrics describe current state

### Python Implementation

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['service', 'method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['service', 'endpoint'],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 5.0)  # Customize for your SLOs
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_in_flight',
    'Active HTTP requests',
    ['service']
)

# Expose metrics endpoint
start_http_server(9090)  # Prometheus scrapes http://service:9090/metrics
```

---

## 2. Structured Logging (FR-009, FR-010, FR-015)

All services MUST emit structured logs in JSON format to stdout/stderr.

### Required Log Fields

```json
{
  "timestamp": "2025-12-05T10:00:00.123Z",  // ISO 8601 format, UTC
  "level": "INFO",                          // DEBUG, INFO, WARN, ERROR, CRITICAL
  "service": "story-service",               // Service name
  "trace_id": "550e8400-e29b-41d4-...",    // Request trace ID (FR-010)
  "span_id": "6ba7b810-9dad-11d1-...",     // Span ID for distributed tracing
  "message": "Story fetched successfully",  // Human-readable message
  "user_id": "user-456",                    // Contextual data
  "story_id": 123,
  "duration_ms": 45,
  "endpoint": "/stories/123",
  "method": "GET",
  "status_code": 200
}
```

### Python Implementation

```python
import logging
import json
import uuid
from pythonjsonlogger import jsonlogger

# Configure JSON logging
logger = logging.getLogger()
logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    fmt='%(timestamp)s %(level)s %(service)s %(trace_id)s %(message)s'
)
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.setLevel(logging.INFO)

# Log with context
def process_request(request):
    trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4()))

    logger.info(
        "Story fetched successfully",
        extra={
            'service': 'story-service',
            'trace_id': trace_id,
            'user_id': request.user_id,
            'story_id': request.params['id'],
            'duration_ms': 45,
            'endpoint': request.path,
            'method': request.method,
            'status_code': 200
        }
    )
```

### Log Levels

- **DEBUG**: Detailed diagnostic information (disabled in production by default)
- **INFO**: General informational messages (request received, action completed)
- **WARN**: Warning messages (degraded performance, fallback triggered)
- **ERROR**: Error messages that don't crash the service (failed external API call, validation error)
- **CRITICAL**: Critical errors that may require immediate action (database connection lost)

---

## 3. Distributed Tracing (FR-010, FR-014)

All services MUST propagate trace context and emit trace spans.

### Trace Context Propagation

Services MUST:
1. Accept `X-Trace-ID` header from incoming requests
2. Generate new trace ID if header not present (`uuid.uuid4()`)
3. Propagate trace ID to all downstream service calls
4. Include trace ID in logs and error responses

### HTTP Header Contract

```http
X-Trace-ID: 550e8400-e29b-41d4-a716-446655440000
X-Span-ID: 6ba7b810-9dad-11d1-80b4-00c04fd430c8
X-Parent-Span-ID: 7c9e6679-7425-40de-944b-e07fc1f90ae7
```

### Python Implementation with OpenTelemetry

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Export to Tempo via OTLP
otlp_exporter = OTLPSpanExporter(endpoint="http://tempo:4317", insecure=True)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Create spans
def fetch_story(story_id):
    with tracer.start_as_current_span("fetch_story") as span:
        span.set_attribute("story_id", story_id)
        span.set_attribute("service", "story-service")

        # Call database
        with tracer.start_as_current_span("database_query"):
            result = db.query(f"SELECT * FROM stories WHERE id = {story_id}")

        span.set_attribute("rows_returned", len(result))
        return result
```

---

## 4. Health Check Endpoints (FR-034, FR-037)

All services MUST expose health check endpoints for readiness and liveness probes.

### `/health` - Liveness Probe

Returns 200 if service process is running, 503 if crashed or unresponsive.

```http
GET /health HTTP/1.1

HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "healthy",
  "version": "v2.0.0",
  "uptime_seconds": 3600
}
```

### `/ready` - Readiness Probe

Returns 200 if service can handle requests, 503 if dependencies unavailable.

```http
GET /ready HTTP/1.1

HTTP/1.1 200 OK
Content-Type: application/json

{
  "status": "ready",
  "dependencies": {
    "database": "ok",
    "payment-service": "ok",
    "photo-service": "ok"
  }
}
```

**Unhealthy Response**:
```http
HTTP/1.1 503 Service Unavailable
Content-Type: application/json

{
  "status": "not_ready",
  "dependencies": {
    "database": "ok",
    "payment-service": "timeout",  // Dependency failed
    "photo-service": "ok"
  },
  "error": "payment-service unavailable"
}
```

---

## 5. Error Logging and Alerting (FR-012, FR-037)

Services MUST log all errors with full context and trigger alerts on threshold breaches.

### Error Logging Format

```json
{
  "timestamp": "2025-12-05T10:00:00.123Z",
  "level": "ERROR",
  "service": "story-service",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Database query failed",
  "error_type": "DatabaseError",
  "error_message": "Connection timeout after 5 seconds",
  "stack_trace": "Traceback (most recent call last):\n  File...",
  "user_id": "user-456",
  "endpoint": "/stories/123",
  "retry_count": 2,
  "recovery_action": "Retrying with exponential backoff"
}
```

### Alert Thresholds (FR-012)

Prometheus alerts trigger when:

**High Error Rate**:
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
  for: 2m
  annotations:
    summary: "Service {{ $labels.service }} has >5% error rate"
```

**High Latency**:
```yaml
- alert: HighLatency
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 0.5
  for: 5m
  annotations:
    summary: "Service {{ $labels.service }} p95 latency >500ms"
```

**Service Down**:
```yaml
- alert: ServiceDown
  expr: up{job="story-service"} == 0
  for: 1m
  annotations:
    summary: "Service {{ $labels.service }} is down"
```

---

## 6. Service Registry Integration (Production)

Services MUST register with Consul on startup and deregister on shutdown.

### Consul Registration (Python)

```python
import consul
import os
import atexit

consul_client = consul.Consul(host='consul', port=8500)

def register_service():
    service_name = os.getenv('SERVICE_NAME', 'story-service')
    service_id = f"{service_name}-{os.getenv('HOSTNAME')}"
    service_port = int(os.getenv('SERVICE_PORT', 8000))

    consul_client.agent.service.register(
        name=service_name,
        service_id=service_id,
        address=os.getenv('SERVICE_HOST', 'localhost'),
        port=service_port,
        tags=[f"version:{os.getenv('SERVICE_VERSION', 'unknown')}"],
        check=consul.Check.http(
            url=f"http://localhost:{service_port}/health",
            interval='10s',
            timeout='2s',
            deregister='30s'  # Auto-deregister if unhealthy for 30s
        )
    )

def deregister_service():
    service_id = f"{os.getenv('SERVICE_NAME')}-{os.getenv('HOSTNAME')}"
    consul_client.agent.service.deregister(service_id)

# Register on startup
register_service()

# Deregister on shutdown
atexit.register(deregister_service)
```

---

## 7. Observability Configuration

### Environment Variables

All services MUST support these environment variables:

```bash
# Logging
LOG_LEVEL=INFO                           # DEBUG, INFO, WARN, ERROR, CRITICAL
LOG_FORMAT=json                          # json or text

# Metrics
METRICS_PORT=9090                        # Port for /metrics endpoint
METRICS_PATH=/metrics                    # Path for Prometheus scraping

# Tracing
TRACE_ENABLED=true                       # Enable distributed tracing
TRACE_EXPORTER=otlp                      # otlp, jaeger, zipkin
TRACE_ENDPOINT=http://tempo:4317         # Trace collector endpoint

# Service Registry
CONSUL_HOST=consul                       # Consul host
CONSUL_PORT=8500                         # Consul port
SERVICE_NAME=story-service               # Service name for registration
SERVICE_VERSION=v2.0.0                   # Service version
```

---

## 8. Prometheus Scrape Configuration

Prometheus scrapes all services at `/metrics` endpoint every 15 seconds.

### prometheus.yml

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Scrape services via Consul service discovery
  - job_name: 'microservices'
    consul_sd_configs:
      - server: 'consul:8500'
    relabel_configs:
      - source_labels: [__meta_consul_service]
        target_label: service
      - source_labels: [__meta_consul_tags]
        regex: ',version:([^,]+),'
        target_label: version
```

---

## 9. Grafana Dashboards

Standard Grafana dashboards MUST be deployed for all services:

### Service Overview Dashboard

- Request rate (requests/second)
- Error rate (percentage)
- Response time (p50, p95, p99)
- Active connections
- CPU and memory usage

### Service Dependency Dashboard

- Dependency health status
- Dependency call latency
- Dependency error rates
- Circuit breaker states

### Log Explorer Dashboard

- Recent error logs
- Search by trace_id, user_id, service
- Log volume by service and level

---

## 10. Retention Policies (FR-013)

- **Metrics**: 90 days (aggregated), 30 days (raw)
- **Logs**: 30 days minimum
- **Traces**: 30 days minimum

Configure in respective storage backends:
- Prometheus: `--storage.tsdb.retention.time=90d`
- Loki: `retention_period: 720h` (30 days)
- Tempo: `retention_duration: 720h` (30 days)

---

## Compliance Checklist

Services are compliant if they:

- [x] Expose `/metrics` endpoint with standard HTTP metrics
- [x] Emit structured JSON logs to stdout
- [x] Propagate `X-Trace-ID` header to all downstream calls
- [x] Emit distributed trace spans via OpenTelemetry
- [x] Expose `/health` (liveness) and `/ready` (readiness) endpoints
- [x] Log all errors with trace_id, stack traces, and context
- [x] Register with Consul on startup (production)
- [x] Support observability environment variables
- [x] Include service name and version in all metrics/logs/traces
