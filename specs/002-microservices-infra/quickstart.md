# Quickstart: Microservices Infrastructure

**Purpose**: Get the complete microservices infrastructure running locally in under 30 minutes

**Prerequisites**:
- Windows PC with Docker Desktop installed
- PowerShell 5.1+ or PowerShell Core
- Git for Windows
- 8GB+ RAM, 20GB+ free disk space

---

## Quick Start (5 Minutes)

```powershell
# Clone repository
git clone https://github.com/your-org/kidcomic.git
cd kidcomic

# Start full infrastructure stack
docker-compose up -d

# Verify all services running
docker-compose ps

# Open Grafana dashboard
Start-Process "http://localhost:3000"  # Default credentials: admin/admin

# Test API Gateway
curl http://localhost/health
```

**You now have**:
- ✅ API Gateway (Traefik) on port 80
- ✅ 5 Microservices (Story, Payment, Photo, User, Content)
- ✅ Observability Stack (Prometheus, Grafana, Loki, Tempo)
- ✅ Service Discovery (Consul)
- ✅ PostgreSQL databases for each service

---

## Step-by-Step Setup

### 1. Install Prerequisites

#### Docker Desktop for Windows

```powershell
# Install via winget
winget install Docker.DockerDesktop

# Or download from https://www.docker.com/products/docker-desktop
```

**Configure Docker Desktop**:
1. Open Docker Desktop → Settings
2. **Resources → WSL Integration**: Enable WSL 2
3. **Resources → Advanced**: Allocate 6GB RAM minimum
4. **Kubernetes**: Enable Kubernetes (optional, for production-like testing)
5. Apply & Restart

#### Python 3.11 (for service development)

```powershell
# Install Python 3.11
winget install Python.Python.3.11

# Verify installation
python --version  # Should show 3.11.x
```

#### Other Tools

```powershell
# Install Chocolatey package manager (if not already installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install utilities
choco install kubernetes-helm k9s k6 curl jq -y
```

---

### 2. Project Structure Setup

```powershell
# Create project directories
mkdir -p services/{api-gateway,story-service,payment-service,photo-service,user-service,content-service}
mkdir -p infrastructure/{observability,ci-cd,terraform,kubernetes}
mkdir -p shared/{lib-logging,lib-tracing,lib-config}
mkdir -p tests/{e2e,smoke}

# Create .env file
@"
# Service Configuration
SERVICE_ENV=development
LOG_LEVEL=INFO

# Database
POSTGRES_USER=kidcomic
POSTGRES_PASSWORD=dev-password-change-in-prod
POSTGRES_DB=storyme

# JWT Authentication
JWT_SECRET=dev-secret-key-change-in-prod-use-strong-random-value

# Service Ports
STORY_SERVICE_PORT=8000
PAYMENT_SERVICE_PORT=8002
PHOTO_SERVICE_PORT=8001
USER_SERVICE_PORT=8003
CONTENT_SERVICE_PORT=8004

# Observability
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
LOKI_PORT=3100
TEMPO_PORT=4317

# Service Discovery
CONSUL_PORT=8500
"@ | Out-File -FilePath .env -Encoding UTF8

# Add .env to .gitignore
Add-Content -Path .gitignore -Value "`n# Environment variables`n.env`n.env.*`n!.env.example"
```

---

### 3. Docker Compose Configuration

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  # API Gateway (Traefik v3)
  traefik:
    image: traefik:v3.0
    command:
      - "--api.dashboard=true"
      - "--api.insecure=true"  # Dev only
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--providers.consul.endpoints=consul:8500"
      - "--entrypoints.web.address=:80"
      - "--metrics.prometheus=true"
      - "--metrics.prometheus.addEntryPointsLabels=true"
      - "--accesslog=true"
    ports:
      - "80:80"      # HTTP
      - "8080:8080"  # Dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - backend
      - observability
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.dashboard.rule=Host(`traefik.localhost`)"
      - "traefik.http.routers.dashboard.service=api@internal"

  # Story Service
  story-service:
    build: ./services/story-service
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@story-db:5432/${POSTGRES_DB}_story
      - JWT_SECRET=${JWT_SECRET}
      - LOG_LEVEL=${LOG_LEVEL}
      - TRACE_ENDPOINT=http://tempo:4317
    networks:
      - backend
      - observability
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.story.rule=PathPrefix(`/stories`)"
      - "traefik.http.services.story.loadbalancer.server.port=8000"
      - "traefik.http.routers.story.middlewares=auth,rate-limit"
    depends_on:
      - story-db
      - consul

  story-db:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}_story
    volumes:
      - story-db-data:/var/lib/postgresql/data
    networks:
      - backend
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Payment Service
  payment-service:
    build: ./services/payment-service
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@payment-db:5432/${POSTGRES_DB}_payment
      - JWT_SECRET=${JWT_SECRET}
      - LOG_LEVEL=${LOG_LEVEL}
      - TRACE_ENDPOINT=http://tempo:4317
    networks:
      - backend
      - observability
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.payment.rule=PathPrefix(`/payments`)"
      - "traefik.http.services.payment.loadbalancer.server.port=8002"
      - "traefik.http.routers.payment.middlewares=auth,rate-limit"
    depends_on:
      - payment-db
      - consul

  payment-db:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}_payment
    volumes:
      - payment-db-data:/var/lib/postgresql/data
    networks:
      - backend

  # Photo Processing Service
  photo-service:
    build: ./services/photo-service
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@photo-db:5432/${POSTGRES_DB}_photo
      - JWT_SECRET=${JWT_SECRET}
      - LOG_LEVEL=${LOG_LEVEL}
      - TRACE_ENDPOINT=http://tempo:4317
    networks:
      - backend
      - observability
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.photo.rule=PathPrefix(`/photos`)"
      - "traefik.http.services.photo.loadbalancer.server.port=8001"
      - "traefik.http.routers.photo.middlewares=auth,rate-limit-strict"
    depends_on:
      - photo-db
      - consul

  photo-db:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}_photo
    volumes:
      - photo-db-data:/var/lib/postgresql/data
    networks:
      - backend

  # Service Discovery (Consul)
  consul:
    image: consul:latest
    command: agent -server -bootstrap-expect=1 -ui -client=0.0.0.0
    ports:
      - "8500:8500"  # HTTP API and UI
      - "8600:8600/udp"  # DNS
    volumes:
      - consul-data:/consul/data
    networks:
      - backend
      - observability

  # Observability Stack

  # Prometheus (Metrics)
  prometheus:
    image: prom/prometheus:latest
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=90d'
    volumes:
      - ./infrastructure/observability/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus-data:/prometheus
    ports:
      - "${PROMETHEUS_PORT}:9090"
    networks:
      - observability

  # Grafana (Dashboards)
  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - ./infrastructure/observability/grafana/dashboards:/etc/grafana/provisioning/dashboards
      - ./infrastructure/observability/grafana/datasources:/etc/grafana/provisioning/datasources
      - grafana-data:/var/lib/grafana
    ports:
      - "${GRAFANA_PORT}:3000"
    networks:
      - observability
    depends_on:
      - prometheus
      - loki
      - tempo

  # Loki (Logs)
  loki:
    image: grafana/loki:latest
    command: -config.file=/etc/loki/local-config.yaml
    ports:
      - "${LOKI_PORT}:3100"
    volumes:
      - loki-data:/loki
    networks:
      - observability

  # Tempo (Traces)
  tempo:
    image: grafana/tempo:latest
    command: [ "-config.file=/etc/tempo.yaml" ]
    volumes:
      - ./infrastructure/observability/tempo/tempo.yaml:/etc/tempo.yaml
      - tempo-data:/var/tempo
    ports:
      - "4317:4317"  # OTLP gRPC
      - "3200:3200"  # Tempo HTTP
    networks:
      - observability

networks:
  backend:
    driver: bridge
  observability:
    driver: bridge

volumes:
  story-db-data:
  payment-db-data:
  photo-db-data:
  consul-data:
  prometheus-data:
  grafana-data:
  loki-data:
  tempo-data:
```

---

### 4. Sample Service (Story Service)

Create `services/story-service/Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Expose ports
EXPOSE 8000 9090

# Health check
HEALTHCHECK --interval=10s --timeout=2s --start-period=30s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `services/story-service/requirements.txt`:

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
asyncpg==0.29.0
pydantic==2.5.0
pydantic-settings==2.1.0
prometheus-client==0.19.0
opentelemetry-api==1.21.0
opentelemetry-sdk==1.21.0
opentelemetry-exporter-otlp==1.21.0
python-jose[cryptography]==3.3.0
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.1
```

Create `services/story-service/src/main.py`:

```python
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram, make_asgi_app
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
import logging
import uuid
import time
import os

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='{"timestamp":"%(asctime)s","level":"%(levelname)s","service":"story-service","message":"%(message)s"}'
)
logger = logging.getLogger(__name__)

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

otlp_exporter = OTLPSpanExporter(
    endpoint=os.getenv("TRACE_ENDPOINT", "http://tempo:4317"),
    insecure=True
)
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# Configure metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['service', 'method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['service', 'endpoint']
)

# Create FastAPI app
app = FastAPI(title="Story Service", version="v2.0.0")

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

# Middleware for tracing and metrics
@app.middleware("http")
async def add_observability(request, call_next):
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    start_time = time.time()

    with tracer.start_as_current_span(f"{request.method} {request.url.path}") as span:
        span.set_attribute("service", "story-service")
        span.set_attribute("trace_id", trace_id)
        span.set_attribute("http.method", request.method)
        span.set_attribute("http.url", str(request.url))

        response = await call_next(request)

        duration = time.time() - start_time
        REQUEST_COUNT.labels(
            service="story-service",
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        REQUEST_LATENCY.labels(
            service="story-service",
            endpoint=request.url.path
        ).observe(duration)

        span.set_attribute("http.status_code", response.status_code)
        span.set_attribute("duration_ms", duration * 1000)

        response.headers["X-Trace-ID"] = trace_id
        return response

# Health endpoints
@app.get("/health")
async def health():
    """Liveness probe"""
    return {"status": "healthy", "version": "v2.0.0"}

@app.get("/ready")
async def ready():
    """Readiness probe"""
    # Check dependencies (database, other services)
    return {
        "status": "ready",
        "dependencies": {
            "database": "ok",
            "payment-service": "ok"
        }
    }

# API endpoints
@app.get("/stories")
async def list_stories(
    user_id: str = None,
    page: int = 1,
    limit: int = 20,
    x_trace_id: str = Header(None)
):
    """List stories with pagination"""
    trace_id = x_trace_id or str(uuid.uuid4())

    logger.info(
        f"Listing stories - trace_id:{trace_id} user_id:{user_id} page:{page} limit:{limit}"
    )

    # Mock data (replace with actual database query)
    stories = [
        {
            "id": "story-1",
            "title": "The Magical Forest",
            "content": "Once upon a time...",
            "tier": "free"
        },
        {
            "id": "story-2",
            "title": "Space Adventure",
            "content": "In a galaxy far away...",
            "tier": "subscriber"
        }
    ]

    return {
        "stories": stories,
        "pagination": {
            "current_page": page,
            "total_pages": 1,
            "total_items": len(stories),
            "items_per_page": limit
        }
    }

@app.get("/stories/{story_id}")
async def get_story(
    story_id: str,
    user_id: str = None,
    x_trace_id: str = Header(None)
):
    """Get single story by ID"""
    trace_id = x_trace_id or str(uuid.uuid4())

    logger.info(
        f"Fetching story - trace_id:{trace_id} story_id:{story_id} user_id:{user_id}"
    )

    # Mock data
    story = {
        "id": story_id,
        "title": "The Magical Forest",
        "content": "Once upon a time in a magical forest...",
        "illustration_urls": [
            "https://example.com/illustrations/forest-1.jpg"
        ],
        "tier": "free"
    }

    return story

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

### 5. Start Infrastructure

```powershell
# Build and start all services
docker-compose up -d --build

# Watch logs
docker-compose logs -f

# Check service health
docker-compose ps
```

**Expected Output**:
```
NAME                  STATUS              PORTS
traefik               Up (healthy)        80->80, 8080->8080
story-service         Up (healthy)        8000
payment-service       Up (healthy)        8002
photo-service         Up (healthy)        8001
consul                Up                  8500->8500
prometheus            Up                  9090->9090
grafana               Up                  3000->3000
loki                  Up                  3100->3100
tempo                 Up                  4317->4317
```

---

### 6. Test API Gateway Routing

```powershell
# Test health endpoints
curl http://localhost/health  # Should hit API Gateway

# List stories (routed through Traefik to story-service)
curl http://localhost/stories

# Get specific story
curl http://localhost/stories/story-1

# View Traefik dashboard
Start-Process "http://localhost:8080"
```

---

### 7. Access Observability Dashboards

#### Grafana (http://localhost:3000)

**Default credentials**: admin/admin

**Pre-configured dashboards**:
1. **Microservices Overview**: Request rates, error rates, latencies
2. **Service Dependencies**: Dependency health and call graphs
3. **Logs Explorer**: Search logs by service, trace_id, user_id
4. **Distributed Traces**: View request flows through services

#### Prometheus (http://localhost:9090)

**Sample queries**:
```promql
# Request rate per service
rate(http_requests_total[5m])

# P95 latency
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

# Error rate
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m])
```

#### Consul (http://localhost:8500)

View registered services, health checks, and key-value store.

---

### 8. Run Load Tests

```powershell
# Create load test script
@"
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '30s', target: 50 },
    { duration: '1m', target: 50 },
    { duration: '30s', target: 0 },
  ],
};

export default function () {
  let response = http.get('http://localhost/stories');
  check(response, {
    'status is 200': (r) => r.status === 200,
  });
  sleep(1);
}
"@ | Out-File -FilePath load-test.js -Encoding UTF8

# Run load test
k6 run load-test.js

# Watch metrics in Grafana during test
```

---

### 9. View Distributed Traces

1. Generate some requests:
```powershell
1..10 | ForEach-Object {
    curl http://localhost/stories/story-$_
    Start-Sleep -Milliseconds 100
}
```

2. Open Grafana → Explore → Select "Tempo" datasource
3. Search for recent traces
4. Click on a trace to see the request flow:
   ```
   api-gateway (50ms)
     └─ story-service (180ms)
         └─ database (100ms)
   ```

---

### 10. Cleanup

```powershell
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Remove images
docker-compose down --rmi all
```

---

## Next Steps

1. **Deploy to Kubernetes**: See [kubernetes/README.md](../../infrastructure/kubernetes/README.md)
2. **Setup CI/CD**: See [ci-cd/README.md](../../infrastructure/ci-cd/README.md)
3. **Production Checklist**: See [production-checklist.md](./production-checklist.md)
4. **Service Development**: See [service-development-guide.md](./service-development-guide.md)

---

## Troubleshooting

### Services won't start

```powershell
# Check Docker is running
docker ps

# Check logs for specific service
docker-compose logs story-service

# Restart single service
docker-compose restart story-service
```

### Port conflicts

```powershell
# Check what's using port 80
netstat -ano | findstr :80

# Change ports in .env file
$env:TRAEFIK_HTTP_PORT = "8081"
docker-compose up -d
```

### Database connection errors

```powershell
# Ensure databases are healthy
docker-compose ps | Select-String "db"

# Reset database
docker-compose down -v
docker-compose up -d story-db
# Wait 10 seconds for DB to initialize
Start-Sleep -Seconds 10
docker-compose up -d story-service
```

### Metrics not showing in Grafana

1. Check Prometheus targets: http://localhost:9090/targets
2. Verify all services show as "UP"
3. Check Grafana datasource configuration: Configuration → Data Sources → Prometheus

---

## Windows-Specific Notes

- Use PowerShell (not CMD) for all commands
- File paths use backslashes: `services\story-service\` (but `/` works in Docker configs)
- Docker Desktop must use WSL 2 backend for best performance
- Hyper-V must be enabled: `Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All`
- If experiencing slow Docker builds, move project to WSL filesystem: `\\wsl$\Ubuntu\home\user\kidcomic`
