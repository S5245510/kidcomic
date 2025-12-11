# Technology Research: Microservices Infrastructure

**Date**: 2025-12-05
**Feature**: Microservices Infrastructure & Integration Strategy
**Context**: 5-10 microservices at launch, beginner team with basic skills, Windows development environment, production HA requirements

## 1. Backend Language/Version

**Decision**: **Python 3.11** for initial services, with Node.js as optional secondary language for specific use cases

**Rationale**:
- **Team Skill Level**: Python is beginner-friendly with clear syntax, extensive learning resources, and gentle learning curve
- **Constitution Compliance**: Python 3.11 is mandated in Constitution (Technical Standards section)
- **Windows Compatibility**: Excellent Windows support via official Python distributions, works seamlessly with Docker Desktop on Windows
- **Microservices Ecosystem**: Strong ecosystem with FastAPI (async, high-performance REST APIs), Flask (simple APIs), and robust libraries for observability (prometheus-client, opentelemetry)
- **Face-Swap Service**: Photo processing service requires Python for ML libraries (OpenCV, face-recognition, PIL)
- **Development Speed**: Faster prototyping and iteration compared to Go or Java, critical for beginner teams

**Alternatives Considered**:
- **Node.js (LTS v20)**: Excellent for real-time services, event-driven architectures, and async I/O. **Use case**: Could be used for gateway or real-time notification services if needed. Strong Windows support.
- **Go (v1.21+)**: Superior performance, small binaries, excellent concurrency. **Rejected**: Steeper learning curve for beginners, type system complexity, less forgiving error handling.
- **Polyglot Architecture**: Mixing languages adds operational complexity (multiple build tools, dependency managers, CI/CD pipelines). **Rejected** for MVP; can adopt incrementally as team matures.

**Skill Progression Path**:
- **Beginner (0-3 months)**: Python 3.11 with Flask for simple REST APIs, synchronous operations, basic error handling
- **Intermediate (3-6 months)**: FastAPI for async operations, Pydantic models for validation, dependency injection
- **Advanced (6-12 months)**: gRPC for service-to-service communication, event-driven patterns with message queues, performance optimization

**Windows Development Notes**:
- Install Python 3.11 via official Windows installer or winget: `winget install Python.Python.3.11`
- Use PowerShell for all scripts (already Constitution requirement)
- Virtual environments work natively: `python -m venv venv` and `venv\Scripts\activate.ps1`
- Docker Desktop for Windows handles containerization seamlessly

---

## 2. API Gateway

**Decision**: **Traefik v3** for development and initial production, with migration path to managed gateway (AWS API Gateway / Azure Application Gateway) for scale

**Rationale**:
- **Beginner-Friendly**: Configuration via YAML files or Docker labels (no Lua scripting required like Kong/Nginx)
- **Automatic Service Discovery**: Native Docker and Kubernetes integration - Traefik automatically discovers services via labels/annotations
- **Built-in Features**: Load balancing, health checks, circuit breakers, automatic HTTPS (Let's Encrypt), middleware system (auth, rate limiting, retries)
- **High Availability**: Supports multi-instance deployment with shared state (via KV store or Kubernetes) - meets FR-033 to FR-036
- **Windows Local Development**: Excellent Docker Desktop support, simple docker-compose setup for local testing
- **Open Source**: Free with strong community, no licensing costs for small deployments
- **Dashboard**: Built-in web UI for monitoring routes, services, and health checks

**Alternatives Considered**:
- **Kong**: More powerful but complex setup (PostgreSQL/Cassandra required, plugin ecosystem requires Lua knowledge). Better for advanced teams or large scale (100+ services).
- **Nginx**: Mature and performant but requires manual configuration, limited dynamic service discovery, no built-in dashboard. Good for static configurations.
- **AWS API Gateway / Azure Application Gateway**: Fully managed, zero operational overhead, excellent scaling. **Migration path**: Start with Traefik for learning and flexibility, migrate to managed when team has 15+ services and budget allows.
- **Envoy**: Industry-standard (used by Istio, service meshes) but steep learning curve, complex YAML configs. Overkill for beginner team.

**Skill Progression Path**:
- **Level 1 (Beginner)**: Docker labels for routing (`traefik.http.routers.story-service.rule=Host('api.example.com') && PathPrefix('/stories')`), static file configuration
- **Level 2 (Intermediate)**: Middleware chains (auth → rate limit → circuit breaker), custom headers, dynamic configuration with Consul
- **Level 3 (Advanced)**: Kubernetes CRDs (IngressRoute), canary deployments, A/B testing, migration to Traefik Enterprise or managed cloud gateway

**High Availability Implementation**:
```yaml
# docker-compose.yml - Multi-instance Traefik with load balancing
version: '3.8'
services:
  traefik-1:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--api.dashboard=true"
    ports:
      - "80:80"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    healthcheck:
      test: ["CMD", "traefik", "healthcheck", "--ping"]
      interval: 10s
      timeout: 5s
      retries: 3

  traefik-2:
    image: traefik:v3.0
    # Same config as traefik-1 (second instance for HA)

  # External load balancer (HAProxy, cloud LB) distributes across traefik-1 and traefik-2
```

**Windows Development Notes**:
- Install via Docker: `docker pull traefik:v3.0`
- Local testing: Access dashboard at `http://localhost:8080` to see auto-discovered services
- Configuration files use Windows paths: `- "D:/kidcomic/traefik.yml:/etc/traefik/traefik.yml:ro"`

---

## 3. Observability Stack

**Decision**: **Prometheus + Grafana + Loki + Tempo** (full open-source stack) for MVP

**Rationale**:
- **Zero Licensing Costs**: Fully open-source, no per-seat or per-GB pricing surprises
- **Integrated Stack**: Grafana provides unified dashboard for metrics (Prometheus), logs (Loki), and traces (Tempo)
- **Industry Standard**: Prometheus is the de facto standard for cloud-native monitoring (CNCF graduated project)
- **30-Day Retention**: Easily configurable retention policies meet FR-013 requirement
- **Windows Compatible**: All components run in Docker containers on Windows
- **Learning Resources**: Extensive documentation, community support, Grafana University courses
- **Pull-Based Scraping**: Services expose `/metrics` endpoint, Prometheus scrapes them (simpler than push-based systems)

**Architecture**:
```
┌─────────────────────────────────────────────────┐
│ Grafana Dashboard (http://localhost:3000)       │
│  - Visualize metrics (Prometheus)               │
│  - View logs (Loki)                             │
│  - Trace requests (Tempo)                       │
└─────────────────────────────────────────────────┘
           ↓              ↓              ↓
   ┌──────────┐   ┌──────────┐   ┌──────────┐
   │Prometheus│   │   Loki   │   │  Tempo   │
   │(Metrics) │   │  (Logs)  │   │ (Traces) │
   └──────────┘   └──────────┘   └──────────┘
         ↑              ↑              ↑
         └──────────────┴──────────────┘
                  Services
        (story-service, payment-service, etc.)
```

**Alternatives Considered**:
- **ELK Stack (Elasticsearch, Logstash, Kibana)**: Powerful log search but resource-intensive (Elasticsearch requires 4GB+ RAM), complex setup, JVM dependency. Better for log-heavy workloads (100GB+/day).
- **Datadog**: Excellent managed SaaS with unified observability, but expensive ($15-31/host/month + $0.10/GB logs). Good for teams with budget and no ops expertise.
- **Cloud-Native (AWS CloudWatch, Azure Monitor)**: Tightly integrated with cloud services, automatic metrics for managed resources. **Use case**: Adopt if deploying to single cloud provider and willing to accept vendor lock-in.

**Skill Progression Path**:
- **Level 1**: Pre-built Grafana dashboards, simple PromQL queries (`rate(http_requests_total[5m])`), structured logging with JSON
- **Level 2**: Custom dashboards, alerting rules (PagerDuty integration), log queries with LogQL, distributed tracing with trace IDs
- **Level 3**: Advanced PromQL (recording rules, aggregations), service SLOs (Service Level Objectives), anomaly detection, long-term storage (Thanos, Cortex)

**Implementation for FR-009 to FR-017**:
```python
# Example: Python service with Prometheus metrics and structured logging
from prometheus_client import Counter, Histogram, start_http_server
import logging
import json
import uuid

# Metrics (FR-011)
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('http_request_duration_seconds', 'HTTP request latency', ['endpoint'])

# Structured logging (FR-010, FR-015)
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'  # JSON format
)

def process_request(request):
    trace_id = request.headers.get('X-Trace-ID', str(uuid.uuid4()))  # FR-010

    # Log with trace ID
    logging.info(json.dumps({
        'trace_id': trace_id,
        'service': 'story-service',
        'event': 'request_received',
        'method': request.method,
        'path': request.path,
        'user_id': request.user_id
    }))

    # Record metrics
    REQUEST_COUNT.labels(method=request.method, endpoint=request.path, status=200).inc()

    return {'trace_id': trace_id, 'data': 'response'}

# Expose metrics endpoint for Prometheus scraping
start_http_server(8000)  # Prometheus scrapes http://localhost:8000/metrics
```

**Windows Development Notes**:
- Docker Compose stack: `docker-compose up -d prometheus grafana loki tempo`
- Access Grafana at `http://localhost:3000` (default: admin/admin)
- Prometheus targets configured via `prometheus.yml` with Windows path mappings

---

## 4. CI/CD Platform

**Decision**: **GitHub Actions** (primary CI/CD platform)

**Rationale**:
- **Zero Additional Cost**: Free for public repos, 2000 minutes/month for private repos on free tier
- **Native Git Integration**: Triggers on commits, PRs, tags - no external webhook configuration
- **Windows Runner Support**: GitHub-hosted Windows runners available (windows-latest), meets Constitution Principle II
- **YAML Configuration**: Simple workflow syntax in `.github/workflows/`, version-controlled with code
- **Marketplace Ecosystem**: Pre-built actions for Docker, Kubernetes, cloud deployments, security scanning
- **Matrix Builds**: Test across multiple Python versions, platforms simultaneously
- **Secrets Management**: Built-in encrypted secrets for API keys, cloud credentials
- **Deployment Environments**: Support for dev/staging/prod with manual approval gates (FR-023)

**Alternatives Considered**:
- **GitLab CI**: Excellent built-in CI/CD with auto-scaling runners, but requires self-hosting or GitLab SaaS (additional platform). Good if already using GitLab.
- **Jenkins**: Maximum flexibility and customization, but requires dedicated server, complex setup, plugin management overhead. Overkill for small teams.
- **CircleCI**: Good performance, clean UI, but limited free tier (1000 credits/month ≈ 70 builds). Paid tiers ($30+/month) better suited for larger teams.

**Skill Progression Path**:
- **Level 1**: Simple workflow - checkout code, run tests, build Docker image
- **Level 2**: Multi-stage pipeline (lint → test → build → deploy), environment variables, matrix builds
- **Level 3**: Reusable workflows, composite actions, self-hosted runners, deployment to Kubernetes with Helm

**Example Workflow (FR-016 to FR-023)**:
```yaml
# .github/workflows/service-ci.yml
name: Story Service CI/CD

on:
  push:
    branches: [main, develop]
    paths:
      - 'services/story-service/**'
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: windows-latest  # Constitution Principle II
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r services/story-service/requirements.txt
          pip install pytest pytest-cov safety

      - name: Lint
        run: flake8 services/story-service/src

      - name: Security scan (FR-017)
        run: safety check --json

      - name: Unit tests (FR-017)
        run: pytest services/story-service/tests/unit --cov

      - name: Integration tests (FR-021)
        run: pytest services/story-service/tests/integration

      - name: Build Docker image
        run: docker build -t story-service:${{ github.sha }} services/story-service

  deploy:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: windows-latest
    steps:
      - name: Deploy to staging (FR-019, zero-downtime)
        run: |
          # Blue-green deployment or rolling update
          kubectl set image deployment/story-service story-service=story-service:${{ github.sha }}
          kubectl rollout status deployment/story-service

      - name: Smoke tests
        run: curl https://staging.api.example.com/health

      - name: Rollback on failure (FR-020)
        if: failure()
        run: kubectl rollout undo deployment/story-service
```

**Windows Development Notes**:
- Workflows tested locally with `act` (Windows-compatible GitHub Actions local runner)
- PowerShell scripts in workflows: `shell: pwsh`
- Docker builds use Docker Desktop for Windows

---

## 5. Service Registry & Discovery

**Decision**: **Docker DNS (development) + Consul (production)** with migration path to Kubernetes native discovery

**Rationale**:
- **Development Simplicity**: Docker Compose provides automatic DNS resolution (services communicate via service names like `http://story-service:8000`)
- **Production Scalability**: Consul provides health checks, service registration, and KV store for distributed config
- **Traefik Integration**: Traefik natively integrates with both Docker labels and Consul catalog
- **Windows Compatibility**: Consul runs as Docker container or Windows service
- **Migration Path**: Start with Docker DNS (zero config), add Consul for production, eventually migrate to Kubernetes Service Discovery

**Alternatives Considered**:
- **etcd**: Used by Kubernetes, strong consistency, but more complex setup and requires understanding Raft consensus. Better for Kubernetes-native deployments.
- **Kubernetes Native**: Best long-term solution but requires Kubernetes cluster (adds infrastructure complexity for beginners). Adopt when moving to K8s.
- **AWS Cloud Map / Azure Service Fabric**: Cloud-specific, vendor lock-in. Use if fully committed to single cloud provider.
- **Netflix Eureka**: Java-based, heavier weight, less active development since Spring Cloud Kubernetes emerged.

**Skill Progression Path**:
- **Level 1 (Docker Compose)**: Services discover via DNS names in `docker-compose.yml` networks
- **Level 2 (Consul)**: Manual service registration, health checks, KV store for feature flags
- **Level 3 (Kubernetes)**: Automatic service discovery via K8s Services, DNS-based discovery, service mesh (Istio/Linkerd)

**Implementation**:
```yaml
# docker-compose.yml - Development (Level 1)
version: '3.8'
services:
  story-service:
    image: story-service:latest
    networks:
      - backend

  payment-service:
    image: payment-service:latest
    networks:
      - backend
    environment:
      - STORY_SERVICE_URL=http://story-service:8000  # Docker DNS resolution

networks:
  backend:
```

```python
# Python service with Consul registration (Level 2)
import consul
import os

consul_client = consul.Consul(host='consul', port=8500)

# Register service on startup
consul_client.agent.service.register(
    name='story-service',
    service_id='story-service-1',
    address=os.getenv('SERVICE_HOST', 'localhost'),
    port=8000,
    check=consul.Check.http('http://localhost:8000/health', interval='10s')
)
```

**Windows Development Notes**:
- Docker Compose networks work identically on Windows
- Consul desktop app available for Windows: `choco install consul`
- Test service discovery: `docker exec story-service ping payment-service`

---

## 6. Configuration Management

**Decision**: **Environment Variables (12-Factor App) + Docker Secrets** for MVP, with migration to **HashiCorp Vault** for production secrets rotation

**Rationale**:
- **Simplicity**: Environment variables are universally supported, no additional infrastructure required
- **12-Factor App Compliance**: Industry-standard configuration pattern for cloud-native apps
- **Docker Integration**: Docker Compose and Kubernetes support env vars and secrets natively
- **Windows Compatibility**: PowerShell, Python, Node.js all read environment variables seamlessly
- **No Vendor Lock-in**: Works across all cloud providers and on-premises

**Alternatives Considered**:
- **HashiCorp Vault**: Best-in-class secret management with rotation, audit logs, dynamic secrets. **Use case**: Adopt in production when handling sensitive data (payment tokens, API keys). Overkill for MVP.
- **AWS Systems Manager Parameter Store**: Excellent if on AWS, free tier generous. Vendor lock-in.
- **Kubernetes ConfigMaps/Secrets**: Great for K8s deployments but requires Kubernetes cluster.
- **Azure Key Vault / GCP Secret Manager**: Cloud-specific, similar to AWS Parameter Store.

**Skill Progression Path**:
- **Level 1**: `.env` files for local development, environment variables in docker-compose
- **Level 2**: Docker secrets for sensitive values, separate configs for dev/staging/prod
- **Level 3**: HashiCorp Vault with automatic secret rotation, dynamic database credentials, audit logging

**Implementation**:
```bash
# .env file (development only - NEVER commit to git)
DATABASE_URL=postgresql://user:pass@localhost:5432/storydb
JWT_SECRET=dev-secret-key-change-in-prod
PHOTO_SERVICE_URL=http://photo-service:8001
```

```yaml
# docker-compose.yml
version: '3.8'
services:
  story-service:
    image: story-service:latest
    env_file:
      - .env  # Load environment variables
    secrets:
      - db_password  # Docker secrets for sensitive values

secrets:
  db_password:
    file: ./secrets/db_password.txt  # File not in git
```

```python
# Python service reading config
import os

DATABASE_URL = os.getenv('DATABASE_URL')
JWT_SECRET = os.getenv('JWT_SECRET')

# Read Docker secret
with open('/run/secrets/db_password', 'r') as f:
    DB_PASSWORD = f.read().strip()
```

**Windows Development Notes**:
- Create `.env` file in project root, ensure `.gitignore` includes `.env`
- PowerShell: `$env:DATABASE_URL = "postgresql://..."`
- Python reads env vars identically on Windows: `os.getenv('DATABASE_URL')`

---

## 7. Integration Testing Approach

**Decision**: **pytest + Testcontainers** (Python services) with Docker Compose for multi-service integration tests

**Rationale**:
- **Docker-Based Isolation**: Testcontainers spins up real databases, services in Docker containers for tests
- **Realistic Testing**: Tests run against actual PostgreSQL, Redis, message queues (not mocks)
- **Windows Compatible**: Testcontainers uses Docker Desktop on Windows
- **pytest Ecosystem**: Fixtures for setup/teardown, parametrized tests, coverage reporting
- **CI/CD Ready**: Works in GitHub Actions with Docker-in-Docker or Docker Desktop

**Alternatives Considered**:
- **Jest + Testcontainers (Node.js)**: Excellent for Node.js services, same benefits as pytest approach
- **Go + Docker SDK**: Native Docker control in Go tests, performant. Use if choosing Go as primary language.
- **Manual Docker Compose**: Simpler but requires manual container management, slower test iterations

**Skill Progression Path**:
- **Level 1**: Unit tests with mocks, simple integration tests with in-memory databases (SQLite)
- **Level 2**: Testcontainers for database integration tests, Docker Compose for multi-service tests
- **Level 3**: Contract testing (Pact), chaos engineering (toxiproxy), performance testing in CI

**Implementation (FR-029)**:
```python
# tests/integration/test_story_service_integration.py
import pytest
from testcontainers.postgres import PostgresContainer
from testcontainers.compose import DockerCompose
import requests

@pytest.fixture(scope="module")
def postgres_container():
    """Spin up real PostgreSQL for tests"""
    with PostgresContainer("postgres:15") as postgres:
        yield postgres

@pytest.fixture(scope="module")
def services():
    """Start story-service and dependencies with Docker Compose"""
    with DockerCompose(".", compose_file_name="docker-compose.test.yml") as compose:
        # Wait for services to be healthy
        compose.wait_for("http://localhost:8000/health")
        yield compose

def test_create_story_integration(services):
    """Test story creation with real database"""
    response = requests.post('http://localhost:8000/stories', json={
        'title': 'Test Story',
        'content': 'Once upon a time...'
    })

    assert response.status_code == 201
    story_id = response.json()['id']

    # Verify story persisted in database
    get_response = requests.get(f'http://localhost:8000/stories/{story_id}')
    assert get_response.status_code == 200
    assert get_response.json()['title'] == 'Test Story'

def test_story_service_to_photo_service_integration(services):
    """Test multi-service integration (FR-029, FR-030)"""
    # Create story with photo upload
    response = requests.post('http://localhost:8000/stories/with-photo', files={
        'photo': open('tests/fixtures/child_photo.jpg', 'rb')
    })

    assert response.status_code == 201
    # Verify photo-service processed the image
    story = response.json()
    assert story['face_swap_status'] == 'completed'
```

**Windows Development Notes**:
- Testcontainers requires Docker Desktop for Windows (WSL2 backend recommended)
- Tests run identically on Windows and Linux CI runners
- Use `pytest -v tests/integration` to run integration tests locally

---

## 8. Contract Testing

**Decision**: **Start with Level 1 (Manual Checklists)**, progress to **Level 2 (Automated Integration Tests)**, consider **Level 3 (Pact CDC)** only when team reaches intermediate skill level (6+ months)

**Rationale** (aligned with FR-030):
- **Beginner Team Reality**: Contract testing tools (Pact, Spring Cloud Contract) have steep learning curve - premature adoption slows development
- **Progressive Approach**: Manual checklists provide immediate value, build understanding before automation
- **Avoid Tool Overwhelm**: Focus on core microservices patterns first, add advanced tooling later
- **Cost-Benefit**: For 5-10 services, manual/automated integration tests may be more pragmatic than full CDC framework

**Alternatives Considered**:
- **Pact (Consumer-Driven Contracts)**: Industry-standard CDC tool, excellent for large microservices deployments (20+ services). **Adoption timeline**: After 6-12 months when team has 10+ services and strong testing culture.
- **Spring Cloud Contract**: Java-specific, great for Spring Boot microservices. Not applicable for Python stack.
- **OpenAPI Schema Validation**: Simpler than full CDC - validate requests/responses against OpenAPI specs. **Good intermediate step** between Level 2 and Level 3.

**Skill Progression Path (FR-030)**:

### Level 1: Manual Integration Testing Checklist (Beginner - Months 0-3)
```markdown
# Story Service v2.0 Deployment Checklist

## Payment Service Integration
- [ ] Story Service can call Payment Service `/subscriptions/check` endpoint
- [ ] Payment Service returns expected JSON structure: `{"user_id": "...", "tier": "free|subscriber"}`
- [ ] Story Service handles payment service timeout gracefully (fallback to free tier)
- [ ] Story Service handles payment service 500 errors with retry logic

## Photo Service Integration
- [ ] Story Service can upload photos to Photo Service `/process` endpoint
- [ ] Photo Service accepts multipart/form-data with JPEG/PNG files
- [ ] Photo Service returns face_swap_id for tracking processing status
- [ ] Story Service can poll `/status/{face_swap_id}` for completion

## API Gateway Routing
- [ ] Gateway routes `/stories/*` to Story Service instances
- [ ] Gateway load balances across 2+ Story Service instances
- [ ] Gateway returns 503 if all Story Service instances unhealthy
```

### Level 2: Automated Integration Test Suite (Intermediate - Months 3-6)
```python
# tests/integration/test_service_contracts.py
def test_payment_service_contract():
    """Verify Payment Service API contract"""
    response = requests.get('http://payment-service:8002/subscriptions/check', params={
        'user_id': 'test-user-123'
    })

    assert response.status_code == 200
    data = response.json()

    # Contract assertions
    assert 'user_id' in data
    assert 'tier' in data
    assert data['tier'] in ['free', 'subscriber']
    assert isinstance(data['subscribed_at'], str) or data['subscribed_at'] is None

def test_photo_service_contract():
    """Verify Photo Service API contract"""
    with open('tests/fixtures/sample_photo.jpg', 'rb') as photo:
        response = requests.post('http://photo-service:8001/process', files={
            'photo': photo
        })

    assert response.status_code == 202  # Accepted for async processing
    data = response.json()
    assert 'face_swap_id' in data
    assert re.match(r'^[a-f0-9\-]{36}$', data['face_swap_id'])  # UUID format
```

### Level 3: Consumer-Driven Contract Testing with Pact (Advanced - Months 6-12)
```python
# Story Service (Consumer) defines contract expectations
from pact import Consumer, Provider

pact = Consumer('story-service').has_pact_with(Provider('payment-service'))

# Define expected interaction
(pact
 .given('user test-user-123 is a subscriber')
 .upon_receiving('a request for subscription status')
 .with_request('get', '/subscriptions/check', query='user_id=test-user-123')
 .will_respond_with(200, body={
     'user_id': 'test-user-123',
     'tier': 'subscriber',
     'subscribed_at': '2025-12-05T10:00:00Z'
 }))

with pact:
    # Test consumer (Story Service) against mock provider
    result = story_service.check_user_subscription('test-user-123')
    assert result.tier == 'subscriber'

# Pact file generated, Payment Service team verifies they honor the contract
```

**Windows Development Notes**:
- Level 1 checklists stored in `docs/deployment-checklists/` markdown files
- Level 2 automated tests run in CI: `pytest tests/integration/test_service_contracts.py`
- Level 3 Pact requires Pact Broker (can run as Docker container on Windows)

**Recommendation**: **Start with Level 1 for MVP (next 3 months)**. Transition to Level 2 when team has 5+ services and solid CI/CD (months 3-6). Evaluate Level 3 (Pact) only if scaling beyond 10 services.

---

## 9. Load Testing

**Decision**: **k6** (primary load testing tool)

**Rationale**:
- **Developer-Friendly**: Tests written in JavaScript, easy to learn and maintain
- **Modern Metrics**: Built-in support for percentiles (p95, p99), trends, thresholds
- **Grafana Integration**: Native Prometheus exporter, visualize load test results in Grafana dashboards
- **Scenarios**: Complex load patterns (ramp-up, constant rate, stress testing) defined in code
- **Windows Compatible**: Single binary download, runs natively on Windows
- **CI/CD Ready**: Runs headless, integrates with GitHub Actions

**Alternatives Considered**:
- **Locust**: Python-based, great if team is Python-heavy. Swarm-based UI is nice but k6's scripting is more powerful.
- **JMeter**: Industry standard, powerful GUI, but XML configs are painful to version control, heavy Java dependency. Better for enterprises with existing JMeter expertise.
- **Gatling**: Scala-based, excellent reporting, but Scala learning curve for beginners. Good for JVM shops.

**Skill Progression Path**:
- **Level 1**: Simple load tests (constant VUs - virtual users, basic assertions)
- **Level 2**: Complex scenarios (ramp-up, spike testing, soak testing), custom metrics, thresholds
- **Level 3**: Distributed load testing (multiple k6 instances), real-time monitoring with Prometheus, chaos engineering integration

**Implementation**:
```javascript
// load-tests/story-service-load.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate } from 'k6/metrics';

// Custom metrics
let errorRate = new Rate('errors');

export let options = {
  stages: [
    { duration: '2m', target: 100 },   // Ramp up to 100 VUs over 2 minutes
    { duration: '5m', target: 100 },   // Stay at 100 VUs for 5 minutes
    { duration: '2m', target: 0 },     // Ramp down to 0 VUs
  ],
  thresholds: {
    'http_req_duration': ['p(95)<500'],  // 95% of requests under 500ms
    'errors': ['rate<0.1'],              // Error rate under 10%
  },
};

export default function () {
  // Test story listing endpoint
  let response = http.get('http://api.example.com/stories');

  let success = check(response, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  errorRate.add(!success);
  sleep(1);
}
```

**Running Load Tests**:
```bash
# Local load test
k6 run load-tests/story-service-load.js

# With Prometheus output (view in Grafana)
k6 run --out prometheus load-tests/story-service-load.js

# CI/CD integration (GitHub Actions)
k6 run --quiet --summary-export=results.json load-tests/story-service-load.js
```

**Windows Development Notes**:
- Install k6: `choco install k6` or download binary from k6.io
- Run from PowerShell: `k6 run .\load-tests\story-service-load.js`
- Output compatible with Windows console colors

---

## 10. Container Orchestration

**Decision**: **Docker Compose (local dev) + Kubernetes (production)** with migration path to managed Kubernetes (AKS/EKS/GKE)

**Rationale**:
- **Development Simplicity**: Docker Compose provides full local environment with single command (`docker-compose up`)
- **Production Requirements**: Kubernetes meets HA requirements (FR-033 to FR-036) - multi-instance deployments, health checks, auto-scaling, rolling updates
- **Industry Standard**: Kubernetes is the de facto orchestration platform, strong job market skill
- **Cloud Agnostic**: K8s manifests work across all clouds (AWS EKS, Azure AKS, GCP GKE, on-premises)
- **Windows Compatibility**: Docker Desktop includes local Kubernetes cluster for testing

**Alternatives Considered**:
- **Docker Swarm**: Simpler than Kubernetes but declining ecosystem, limited cloud support. Easier learning curve but dead-end skill.
- **AWS ECS (Elastic Container Service)**: Excellent AWS integration, simpler than K8s, but AWS-only (vendor lock-in).
- **Azure Container Apps**: Serverless container platform, very beginner-friendly, good for simple workloads. Limited control vs Kubernetes.
- **Google Cloud Run**: Fully managed, auto-scaling, pay-per-request. Great for stateless services but limited for complex microservices orchestration.

**Skill Progression Path**:
- **Level 1 (Docker Compose)**: Local development, `docker-compose.yml` with all services, volumes, networks
- **Level 2 (Kubernetes Basics)**: Deployments, Services, ConfigMaps, Secrets, basic kubectl commands
- **Level 3 (Production K8s)**: Helm charts, Ingress controllers (Traefik), Horizontal Pod Autoscaling, StatefulSets, monitoring with Prometheus Operator

**Architecture**:

### Development (Docker Compose)
```yaml
# docker-compose.yml
version: '3.8'
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"
      - "8080:8080"  # Dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro

  story-service:
    build: ./services/story-service
    labels:
      - "traefik.http.routers.story.rule=PathPrefix(`/stories`)"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/storydb
    depends_on:
      - db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 10s

  payment-service:
    build: ./services/payment-service
    labels:
      - "traefik.http.routers.payment.rule=PathPrefix(`/payments`)"

  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./infrastructure/observability/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"

volumes:
  postgres_data:
```

### Production (Kubernetes)
```yaml
# kubernetes/story-service-deployment.yml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: story-service
spec:
  replicas: 3  # HA requirement (FR-033)
  selector:
    matchLabels:
      app: story-service
  template:
    metadata:
      labels:
        app: story-service
    spec:
      containers:
      - name: story-service
        image: story-service:v1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-credentials
              key: url
        livenessProbe:  # FR-034 health checks
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 500m
            memory: 512Mi

---
apiVersion: v1
kind: Service
metadata:
  name: story-service
spec:
  selector:
    app: story-service
  ports:
  - port: 8000
    targetPort: 8000
  type: ClusterIP

---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler  # FR-036 auto-scaling
metadata:
  name: story-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: story-service
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

**Migration Timeline**:
1. **Months 0-2**: Docker Compose for all development and staging
2. **Month 3**: Deploy to managed Kubernetes (AKS/EKS/GKE) for production
3. **Months 4-6**: Migrate staging to Kubernetes, refine deployments
4. **Month 6+**: Full Kubernetes-based workflow with Helm charts

**Windows Development Notes**:
- Enable Kubernetes in Docker Desktop settings (Settings → Kubernetes → Enable)
- Local K8s cluster accessible via `kubectl` in PowerShell
- Test deployments locally: `kubectl apply -f kubernetes/`
- Helm install: `choco install kubernetes-helm`

---

## Summary of Recommendations

| Decision Area | Recommendation | Rationale |
|---------------|---------------|-----------|
| **Backend Language** | Python 3.11 | Constitution compliance, beginner-friendly, strong ecosystem |
| **API Gateway** | Traefik v3 | Easy setup, auto-discovery, built-in HA, Windows compatible |
| **Observability** | Prometheus + Grafana + Loki + Tempo | Open-source, integrated stack, zero licensing costs |
| **CI/CD** | GitHub Actions | Native git integration, free tier, Windows runners |
| **Service Discovery** | Docker DNS → Consul → K8s | Progressive complexity matching team skill growth |
| **Configuration** | Environment Variables + Docker Secrets | Simple, 12-factor compliant, migration to Vault later |
| **Integration Testing** | pytest + Testcontainers | Realistic tests with real dependencies |
| **Contract Testing** | Manual Checklists → Automated Tests → Pact | Beginner-friendly progression (FR-030) |
| **Load Testing** | k6 | JavaScript-based, modern metrics, Grafana integration |
| **Orchestration** | Docker Compose → Kubernetes | Local dev simplicity, production HA requirements |

**Next Steps**:
1. Update Technical Context in plan.md with concrete technology choices
2. Create data-model.md with key entities (API Gateway, Microservice, Request Trace, etc.)
3. Generate API contracts in /contracts/ directory
4. Write quickstart.md with complete setup instructions

**Skill Progression Timeline**:
- **Months 0-3**: Level 1 tools, manual processes, Docker Compose, basic monitoring
- **Months 3-6**: Level 2 automation, Consul, Kubernetes basics, advanced Grafana
- **Months 6-12**: Level 3 advanced features, contract testing, service mesh evaluation
