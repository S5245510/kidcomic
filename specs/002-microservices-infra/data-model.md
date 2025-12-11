# Data Model: Microservices Infrastructure

**Date**: 2025-12-05
**Feature**: Microservices Infrastructure & Integration Strategy
**Source**: Extracted from [spec.md](./spec.md) Key Entities section

## Core Entities

### 1. API Gateway

**Purpose**: Single entry point for all client requests, responsible for routing, authentication, rate limiting, and error handling.

**Attributes**:
```python
class APIGateway:
    gateway_id: str                    # Unique identifier for gateway instance
    instance_name: str                 # Instance name (traefik-1, traefik-2, etc.)
    listen_address: str                # IP:Port (e.g., "0.0.0.0:80")
    status: GatewayStatus              # Enum: HEALTHY, DEGRADED, UNHEALTHY
    routing_rules: List[RoutingRule]   # Configured routes to services
    health_check_interval: int         # Seconds between health checks
    created_at: datetime
    last_health_check: datetime
```

**Relationships**:
- Has many `RoutingRule` (1:N)
- Routes to many `Microservice` (N:M via routing rules)
- Monitored by `HealthMetrics` (1:N)

**Validation Rules** (from FR-001 to FR-008, FR-033 to FR-036):
- `gateway_id` must be unique across all instances
- `status` transitions: HEALTHY ↔ DEGRADED ↔ UNHEALTHY (no direct HEALTHY → UNHEALTHY)
- `health_check_interval` must be between 5-60 seconds
- Must have minimum 2 instances for production (FR-033)
- Load balancer must distribute traffic across healthy instances only (FR-034)

**State Transitions**:
```
INITIALIZING → HEALTHY
HEALTHY → DEGRADED (partial failures, elevated latency)
DEGRADED → HEALTHY (recovery)
DEGRADED → UNHEALTHY (complete failure)
UNHEALTHY → HEALTHY (restart, recovery)
```

---

### 2. Routing Rule

**Purpose**: Maps incoming request paths to backend microservices.

**Attributes**:
```python
class RoutingRule:
    rule_id: str                       # Unique identifier
    gateway_id: str                    # Foreign key to API Gateway
    path_pattern: str                  # URL pattern (e.g., "/stories/*", "/payments/*")
    http_method: str                   # GET, POST, PUT, DELETE, PATCH, or "*" (all)
    target_service_name: str           # Service to route to (e.g., "story-service")
    target_port: int                   # Service port (e.g., 8000)
    priority: int                      # Rule priority (higher = evaluated first)
    middleware_chain: List[str]        # ["auth", "rate-limit", "circuit-breaker"]
    created_at: datetime
    updated_at: datetime
```

**Relationships**:
- Belongs to `APIGateway` (N:1)
- Routes to `Microservice` (N:1)

**Validation Rules** (from FR-001, FR-002, FR-007, FR-008):
- `path_pattern` must be valid regex or glob pattern
- `http_method` must be valid HTTP method or "*"
- `target_service_name` must match registered service name
- `priority` must be unique within gateway (no duplicate priorities)
- `middleware_chain` order matters (auth before rate-limit before circuit-breaker)

**Example**:
```yaml
rule_id: "rule-stories-001"
path_pattern: "/stories/*"
http_method: "*"
target_service_name: "story-service"
target_port: 8000
priority: 100
middleware_chain: ["auth", "rate-limit"]
```

---

### 3. Microservice

**Purpose**: Independent, deployable unit of business logic with its own API, version, and deployment lifecycle.

**Attributes**:
```python
class Microservice:
    service_id: str                    # Unique identifier
    service_name: str                  # Logical name (e.g., "story-service")
    version: str                       # Semantic version (e.g., "v2.1.0")
    instance_id: str                   # Specific instance ID (story-service-pod-1)
    host: str                          # IP or hostname
    port: int                          # Service port
    status: ServiceStatus              # Enum: STARTING, HEALTHY, UNHEALTHY, DRAINING, STOPPED
    health_endpoint: str               # URL path for health checks (e.g., "/health")
    ready_endpoint: str                # URL path for readiness checks (e.g., "/ready")
    api_contract_url: str              # OpenAPI spec URL
    dependencies: List[str]            # Service names this service depends on
    deployed_at: datetime
    last_health_check: datetime
```

**Relationships**:
- Exposes `ServiceContract` (1:1)
- Produces `HealthMetrics` (1:N)
- Generates `RequestTrace` records (1:N)
- Has many deployment `DeploymentPipeline` runs (1:N)

**Validation Rules** (from FR-016 to FR-032):
- `service_name` must be unique within environment (dev/staging/prod)
- `version` must follow semantic versioning (MAJOR.MINOR.PATCH)
- `health_endpoint` must return HTTP 200 when healthy, 503 when unhealthy
- `api_contract_url` must resolve to valid OpenAPI 3.x or GraphQL schema
- Breaking changes require MAJOR version bump (FR-025)

**State Transitions**:
```
STARTING → HEALTHY (health check passes)
STARTING → UNHEALTHY (health check fails)
HEALTHY → DRAINING (graceful shutdown initiated)
HEALTHY → UNHEALTHY (health check fails)
DRAINING → STOPPED (all connections drained)
UNHEALTHY → HEALTHY (recovery)
UNHEALTHY → STOPPED (forced termination)
```

---

### 4. Service Contract

**Purpose**: Formal API definition (endpoints, request/response formats, error codes) and service dependencies.

**Attributes**:
```python
class ServiceContract:
    contract_id: str                   # Unique identifier
    service_name: str                  # Service this contract describes
    version: str                       # Contract version (matches service version)
    contract_type: str                 # "REST", "GraphQL", "gRPC"
    schema_url: str                    # OpenAPI/GraphQL schema location
    endpoints: List[Endpoint]          # API endpoints defined
    dependencies: List[Dependency]     # Services this contract depends on
    breaking_changes: List[str]        # List of breaking changes from previous version
    created_at: datetime
    deprecated_at: datetime | None     # When this contract version was deprecated
```

**Nested Structures**:
```python
class Endpoint:
    path: str                          # "/stories/{id}"
    method: str                        # "GET", "POST", etc.
    request_schema: dict               # JSON schema for request body
    response_schema: dict              # JSON schema for response body
    error_codes: List[int]             # Possible HTTP status codes

class Dependency:
    service_name: str                  # "payment-service"
    version_range: str                 # ">=v2.0.0, <v3.0.0" (semver range)
    endpoints_used: List[str]          # ["/subscriptions/check"]
```

**Relationships**:
- Belongs to `Microservice` (1:1)
- Referenced by `DeploymentPipeline` for compatibility checks (N:M)

**Validation Rules** (from FR-024, FR-025, FR-027, FR-030):
- `version` must match service semantic version
- `schema_url` must be accessible and valid JSON/YAML
- Breaking changes require MAJOR version increment
- Contract tests must validate compatibility with dependencies before deployment

---

### 5. Request Trace

**Purpose**: Record of a single user request's journey through multiple services with timing, errors, and correlation.

**Attributes**:
```python
class RequestTrace:
    trace_id: str                      # Unique trace identifier (UUID v4)
    parent_span_id: str | None         # Parent span for nested calls
    service_name: str                  # Service that handled this span
    operation_name: str                # Operation performed (e.g., "GET /stories/123")
    start_time: datetime               # When span started
    end_time: datetime                 # When span ended
    duration_ms: float                 # Calculated duration in milliseconds
    status_code: int                   # HTTP status code (200, 404, 500, etc.)
    error_message: str | None          # Error details if failed
    tags: dict                         # Additional metadata (user_id, endpoint, etc.)
    logs: List[LogEntry]               # Structured logs within this span
```

**Nested Structures**:
```python
class LogEntry:
    timestamp: datetime
    level: str                         # "DEBUG", "INFO", "WARN", "ERROR"
    message: str
    context: dict                      # Additional key-value context
```

**Relationships**:
- Belongs to `Microservice` (many traces per service)
- Has parent `RequestTrace` for nested calls (self-referential, N:1)
- Stored in distributed tracing system (Tempo/Jaeger)

**Validation Rules** (from FR-009 to FR-015):
- `trace_id` must be propagated across all service calls via HTTP header `X-Trace-ID`
- `duration_ms` must be positive and match `end_time - start_time`
- Traces must be retained for minimum 30 days (FR-013)
- All log entries must include trace_id for correlation (FR-010)

**Example**:
```json
{
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "parent_span_id": null,
  "service_name": "api-gateway",
  "operation_name": "GET /stories/123",
  "start_time": "2025-12-05T10:00:00.000Z",
  "end_time": "2025-12-05T10:00:00.250Z",
  "duration_ms": 250,
  "status_code": 200,
  "tags": {
    "user_id": "user-456",
    "http.method": "GET",
    "http.url": "/stories/123"
  },
  "logs": [
    {
      "timestamp": "2025-12-05T10:00:00.100Z",
      "level": "INFO",
      "message": "Routing request to story-service",
      "context": {"target_host": "story-service:8000"}
    }
  ]
}
```

---

### 6. Deployment Pipeline

**Purpose**: Automated workflow for building, testing, and deploying services to production with rollback capability.

**Attributes**:
```python
class DeploymentPipeline:
    pipeline_id: str                   # Unique identifier
    service_name: str                  # Service being deployed
    version: str                       # Version being deployed
    commit_sha: str                    # Git commit SHA
    triggered_by: str                  # User or automation that triggered pipeline
    status: PipelineStatus             # Enum: PENDING, RUNNING, SUCCESS, FAILED, ROLLED_BACK
    stages: List[PipelineStage]        # Stages in pipeline (test, build, deploy)
    started_at: datetime
    completed_at: datetime | None
    deployment_type: str               # "blue-green", "rolling", "canary"
    rollback_to_version: str | None    # Previous version for rollback
```

**Nested Structures**:
```python
class PipelineStage:
    stage_name: str                    # "lint", "unit-test", "integration-test", "build", "deploy"
    status: StageStatus                # PENDING, RUNNING, SUCCESS, FAILED, SKIPPED
    started_at: datetime
    completed_at: datetime | None
    logs_url: str                      # URL to stage logs
    artifacts: List[str]               # Docker image tags, test reports
```

**Relationships**:
- Deploys `Microservice` version (N:1)
- Validates against `ServiceContract` (compatibility checks)
- Generates `HealthMetrics` post-deployment

**Validation Rules** (from FR-016 to FR-023):
- Pipeline must run unit tests, integration tests, security scans before deploy (FR-017)
- Failed tests must block deployment (FR-018)
- Deployment must verify zero-downtime (health checks during rollout) (FR-019)
- Rollback must complete within 2 minutes (FR-020 - specification says "within 2 minutes" but updated to "quickly")
- Compatibility checks must validate dependencies before deploy (FR-021)

**State Transitions**:
```
PENDING → RUNNING (pipeline starts)
RUNNING → SUCCESS (all stages pass)
RUNNING → FAILED (any stage fails)
SUCCESS → ROLLED_BACK (post-deployment issues detected)
FAILED → PENDING (retry triggered)
```

---

### 7. Health Metrics

**Purpose**: Real-time measurements of service performance for monitoring, alerting, and routing decisions.

**Attributes**:
```python
class HealthMetrics:
    metric_id: str                     # Unique identifier
    service_name: str                  # Service or gateway being monitored
    instance_id: str                   # Specific instance
    timestamp: datetime                # When metric was recorded
    error_rate: float                  # Errors per second (0.0 - 1.0)
    request_rate: float                # Requests per second
    response_time_p50: float           # 50th percentile response time (ms)
    response_time_p95: float           # 95th percentile response time (ms)
    response_time_p99: float           # 99th percentile response time (ms)
    cpu_usage_percent: float           # CPU utilization (0-100)
    memory_usage_mb: float             # Memory usage in MB
    active_connections: int            # Current active connections
```

**Relationships**:
- Belongs to `Microservice` or `APIGateway` (N:1)
- Triggers alerts when thresholds exceeded (N:M with Alert rules)

**Validation Rules** (from FR-011, FR-012, FR-037):
- Metrics must be scraped/collected at least every 15 seconds
- `error_rate` threshold alert: >5% for 2 minutes triggers alert (FR-012)
- `response_time_p95` threshold: >500ms for 5 minutes triggers investigation
- Gateway health metrics must include instance count, error rates, health check status (FR-037)

**Example Prometheus Query**:
```promql
# Calculate error rate over 5 minutes
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

---

## Entity Relationship Diagram

```
┌─────────────────┐         ┌─────────────────┐
│  API Gateway    │◄───────►│  Routing Rule   │
│  (2+ instances) │   1:N   └─────────────────┘
└─────────────────┘                 │
        │                           │ N:1
        │ routes to                 ▼
        │                   ┌─────────────────┐
        └──────────────────►│  Microservice   │
                            │  (5-10 services)│
                            └─────────────────┘
                                    │
            ┌───────────────────────┼───────────────────────┐
            │                       │                       │
            │ 1:1                   │ 1:N                   │ 1:N
            ▼                       ▼                       ▼
    ┌─────────────────┐     ┌─────────────────┐   ┌─────────────────┐
    │ServiceContract  │     │  Request Trace  │   │ Health Metrics  │
    │ (API definition)│     │  (distributed)  │   │  (time-series)  │
    └─────────────────┘     └─────────────────┘   └─────────────────┘
            │
            │ validates
            ▼
    ┌─────────────────┐
    │Deployment       │
    │Pipeline         │
    │ (CI/CD)         │
    └─────────────────┘
```

---

## Data Flow Examples

### 1. User Request Flow (User Story 1 - FR-001 to FR-004)

```
1. Mobile App → API Gateway (traefik-1)
   GET /stories/123
   Headers: Authorization: Bearer <token>

2. API Gateway → Authentication Middleware
   Validates JWT token, extracts user_id

3. API Gateway → Routing Rule Matcher
   Matches "/stories/*" → story-service:8000

4. API Gateway → Story Service (instance 1 or 2, load balanced)
   GET http://story-service:8000/stories/123
   Headers: X-Trace-ID: <uuid>, X-User-ID: <user_id>

5. Story Service → Database
   SELECT * FROM stories WHERE id = 123

6. Story Service → API Gateway
   200 OK, JSON: {"id": 123, "title": "...", "content": "..."}

7. API Gateway → Mobile App
   200 OK, JSON response (consistent format, FR-004)

8. Request Trace logged at each step with trace_id for debugging (FR-010)
```

### 2. Service Deployment Flow (User Story 3 - FR-016 to FR-023)

```
1. Developer commits code to story-service repo

2. GitHub Actions triggers Deployment Pipeline
   - Stage 1: Lint code (flake8, black)
   - Stage 2: Unit tests (pytest)
   - Stage 3: Integration tests (pytest + Testcontainers)
   - Stage 4: Security scan (safety, Trivy)
   - Stage 5: Contract validation (check API contract compatibility)

3. Pipeline builds Docker image
   story-service:v2.1.0

4. Pipeline deploys to staging with blue-green strategy
   - Launch new instances (green)
   - Run smoke tests against green environment
   - Switch traffic from blue to green
   - Keep blue running for rollback

5. Pipeline monitors Health Metrics for 10 minutes
   - Error rate < 5%
   - Response time p95 < 500ms

6. If metrics good: Mark deployment SUCCESS
   If metrics bad: Automatic rollback to v2.0.0 (FR-020)

7. Deployment history recorded in Pipeline entity
```

### 3. Distributed Tracing Flow (User Story 2 - FR-009 to FR-015)

```
1. User reports slow story loading

2. Operations team searches logs by user_id
   LogQL query: {service="*"} |= "user-456"

3. Logs return trace_id: "550e8400-..."

4. Team opens Grafana → Tempo → Search trace "550e8400-..."

5. Trace shows request path:
   ┌─────────────────────────────────────────────────────┐
   │ api-gateway          50ms    [==]                   │
   │   └─ story-service   180ms   [========]             │
   │       └─ photo-service 120ms [======]               │
   │           └─ database   100ms [====]  ← SLOW QUERY  │
   └─────────────────────────────────────────────────────┘
   Total: 250ms

6. Bottleneck identified: database query in photo-service took 100ms

7. Team optimizes query, redeploys photo-service via Pipeline
```

---

## Storage Implementation

### Time-Series Metrics (Prometheus)
```yaml
# Prometheus stores Health Metrics as time-series
http_requests_total{service="story-service", method="GET", status="200"} 1543
http_request_duration_seconds_bucket{service="story-service", le="0.1"} 856
```

### Log Aggregation (Loki)
```json
// Structured logs with trace_id for correlation
{
  "timestamp": "2025-12-05T10:00:00.000Z",
  "level": "INFO",
  "service": "story-service",
  "trace_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Story fetched successfully",
  "story_id": 123,
  "user_id": "user-456",
  "duration_ms": 45
}
```

### Distributed Tracing (Tempo)
- Stores Request Trace entities with parent-child relationships
- Indexed by trace_id for fast lookups
- Retention: 30 days (FR-013)

### Service Registry (Consul)
```json
{
  "service": {
    "name": "story-service",
    "id": "story-service-1",
    "address": "10.0.1.5",
    "port": 8000,
    "tags": ["v2.1.0", "production"],
    "meta": {
      "version": "v2.1.0",
      "api_contract": "http://story-service:8000/openapi.json"
    },
    "check": {
      "http": "http://10.0.1.5:8000/health",
      "interval": "10s"
    }
  }
}
```

---

## Notes

- All entities use UUIDs or composite keys for unique identification
- Timestamps use ISO 8601 format with UTC timezone
- Enum values (status fields) are uppercase strings
- Relationships enforce referential integrity via foreign keys or service discovery
- State transitions are unidirectional except for HEALTHY ↔ DEGRADED
- Metrics retention: 30 days for traces/logs (FR-013), 90+ days for aggregated metrics
