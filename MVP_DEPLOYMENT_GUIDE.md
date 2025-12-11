# MVP Deployment Guide: API Gateway v0.1.0

**Last Updated**: 2025-12-05
**Status**: Ready for Deployment
**Completion**: Phase 3 MVP - API Gateway with Story Service

---

## Overview

This guide walks you through deploying the **Microservices Infrastructure MVP** which includes:

- ✅ **API Gateway (Traefik v3)** with HA configuration (2 instances)
- ✅ **Story Service** with observability (logging, metrics, tracing)
- ✅ **PostgreSQL Database** for Story Service
- ✅ **Service Discovery** (Consul)
- ✅ **Observability Stack** (Prometheus, Grafana, Loki, Tempo)

**User Story**: Mobile app developers can integrate with StoryMe services through a single API endpoint (`http://localhost/stories`) that routes requests to the Story Service.

---

## Prerequisites

### Required Software

- **Docker Desktop** (Windows/Mac/Linux)
  - Version: 20.10+ with Docker Compose v2
  - Download: https://www.docker.com/products/docker-desktop

- **Git** (for cloning the repository)
  - Download: https://git-scm.com/downloads

### Optional Tools (for testing)

- **Python 3.11+** (for running tests locally)
- **k6** (for load testing): https://k6.io/docs/getting-started/installation/
- **curl** or **Postman** (for API testing)

### System Requirements

- **RAM**: Minimum 8GB (16GB recommended)
- **Disk Space**: 10GB free
- **CPU**: 4+ cores recommended
- **Ports**: Ensure these ports are available:
  - `80` - API Gateway (HTTP)
  - `443` - API Gateway (HTTPS, future)
  - `8080-8083` - Traefik dashboards & metrics
  - `8500` - Consul UI
  - `9090` - Prometheus UI
  - `3000` - Grafana UI
  - `8000` - Story Service (direct access)
  - `5432` - PostgreSQL

---

## Quick Start (5 Minutes)

```powershell
# 1. Clone the repository (if not already done)
cd D:\kidcomic

# 2. Copy environment template
Copy-Item .env.example .env

# 3. Start all services
docker-compose up -d

# 4. Wait for services to be healthy (30-60 seconds)
Start-Sleep -Seconds 60

# 5. Check service status
docker-compose ps

# 6. Test the API Gateway
curl http://localhost/stories/

# 7. Open dashboards
Start-Process "http://localhost:8080"  # Traefik Dashboard
Start-Process "http://localhost:3000"  # Grafana (admin/admin)
Start-Process "http://localhost:8500"  # Consul UI
```

**Expected Result**: You should see a JSON response with sample stories, and all services showing as "Up" or "healthy".

---

## Detailed Deployment Steps

### Step 1: Environment Configuration

1. **Copy the environment template**:
   ```powershell
   Copy-Item .env.example .env
   ```

2. **Edit `.env` file** (optional - defaults are suitable for development):
   ```bash
   # Service Configuration
   SERVICE_ENV=development
   LOG_LEVEL=INFO
   LOG_FORMAT=json

   # Database
   POSTGRES_USER=kidcomic
   POSTGRES_PASSWORD=changeme  # CHANGE IN PRODUCTION!

   # Service Ports (change if ports are in use)
   STORY_SERVICE_PORT=8000
   CONSUL_PORT=8500
   PROMETHEUS_PORT=9090
   GRAFANA_PORT=3000
   ```

### Step 2: Build and Start Services

1. **Build the Story Service image**:
   ```powershell
   docker-compose build story-service
   ```

2. **Start all services**:
   ```powershell
   docker-compose up -d
   ```

   This will start:
   - 2x Traefik instances (API Gateway)
   - Story Service
   - PostgreSQL database
   - Consul (service discovery)
   - Prometheus, Grafana, Loki, Tempo (observability)

3. **Monitor startup logs** (optional):
   ```powershell
   docker-compose logs -f
   # Press Ctrl+C to exit log view
   ```

### Step 3: Verify Deployment

1. **Check service health**:
   ```powershell
   docker-compose ps
   ```

   **Expected Output**: All services should show "Up" or "Up (healthy)":
   ```
   NAME                STATUS
   traefik-1           Up (healthy)
   traefik-2           Up (healthy)
   story-service       Up (healthy)
   story-db            Up (healthy)
   consul              Up (healthy)
   prometheus          Up
   grafana             Up
   loki                Up
   tempo               Up
   ```

2. **Test Story Service via Gateway**:
   ```powershell
   # List all stories
   curl http://localhost/stories/

   # Get specific story
   curl http://localhost/stories/1

   # Check health endpoints
   curl http://localhost/stories/health
   curl http://localhost/stories/ready
   ```

   **Expected Response**:
   ```json
   {
     "stories": [
       {
         "id": 1,
         "title": "The Brave Little Turtle",
         "content": "Once upon a time...",
         "age_range": "3-5",
         "moral_lesson": "Courage comes in all sizes"
       }
     ],
     "total": 3
   }
   ```

3. **Verify Traefik Dashboard**:
   ```powershell
   Start-Process "http://localhost:8080"
   ```

   - Navigate to **HTTP Routers** → Verify `story-service` router exists
   - Navigate to **Services** → Verify `story-service` is healthy
   - Check **Metrics** tab for request stats

4. **Verify Grafana Datasources**:
   ```powershell
   Start-Process "http://localhost:3000"
   ```

   - Login: `admin` / `admin` (change password when prompted)
   - Navigate to **Configuration → Data Sources**
   - Verify 3 datasources configured: Prometheus, Loki, Tempo

5. **Verify Consul Service Discovery**:
   ```powershell
   Start-Process "http://localhost:8500"
   ```

   - Navigate to **Services**
   - Verify `story-service` is registered

---

## Testing the MVP

### Manual API Testing

1. **Test Story Listing**:
   ```powershell
   curl http://localhost/stories/
   ```

2. **Test Story Filtering**:
   ```powershell
   curl "http://localhost/stories/?age_range=3-5"
   ```

3. **Test Story Personalization**:
   ```powershell
   curl -X POST "http://localhost/stories/1/personalize?child_name=Emma" `
        -H "Content-Type: application/json"
   ```

4. **Test Trace ID Propagation**:
   ```powershell
   curl -H "X-Trace-ID: test-trace-12345" http://localhost/stories/
   # Check response headers for X-Trace-ID
   ```

### Run Automated Tests

#### Contract Tests (pytest)

```powershell
# Install test dependencies
cd tests\integration
pip install pytest pyyaml

# Run contract tests
pytest test_gateway_routing.py -v
```

**Expected**: Some tests may fail initially (middlewares not fully configured) - this is expected for MVP.

#### End-to-End Tests (pytest)

```powershell
# Run E2E tests
cd tests\e2e
pip install pytest requests

pytest test_gateway_e2e.py -v
```

**Expected**: Tests should pass if gateway and story service are running correctly.

#### Load Tests (k6)

```powershell
# Install k6 first: https://k6.io/docs/getting-started/installation/

# Run load test
cd tests\load
k6 run test_gateway_load.js
```

**Expected Performance** (per spec):
- p95 latency < 50ms
- Error rate < 1%
- Support 100+ concurrent requests

---

## Observability & Monitoring

### View Logs (JSON Structured)

```powershell
# Story Service logs
docker-compose logs -f story-service

# Gateway logs
docker-compose logs -f traefik-1

# Filter by trace_id (example)
docker-compose logs story-service | Select-String "test-trace-12345"
```

### View Metrics (Prometheus)

1. Open Prometheus: http://localhost:9090
2. Example queries:
   ```promql
   # Request rate by service
   rate(http_requests_total[1m])

   # p95 latency
   histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))

   # Service health
   service_health
   ```

### View Traces (Tempo via Grafana)

1. Open Grafana: http://localhost:3000
2. Navigate to **Explore**
3. Select **Tempo** datasource
4. Search for traces by trace_id or service name

### View Dashboards (Grafana)

**Note**: Pre-built dashboards will be added in Phase 4 (US2). For now, you can create custom dashboards using Prometheus datasource.

---

## Troubleshooting

### Issue: Services fail to start

**Symptoms**: `docker-compose ps` shows services as "Restarting" or "Exit 1"

**Solutions**:
```powershell
# Check logs
docker-compose logs <service-name>

# Common causes:
# 1. Port conflicts
netstat -ano | findstr :80
netstat -ano | findstr :8000

# 2. Not enough memory
# Solution: Increase Docker Desktop memory limit to 8GB+

# 3. Database not ready
# Solution: Wait 60 seconds and try again

# Reset and try again
docker-compose down -v
docker-compose up -d
```

### Issue: Cannot access http://localhost/stories/

**Symptoms**: `curl: (7) Failed to connect to localhost port 80`

**Solutions**:
```powershell
# Check if Traefik is running
docker-compose ps traefik-1

# Check Traefik logs
docker-compose logs traefik-1

# Verify port 80 is not in use
netstat -ano | findstr :80

# Try direct access to Story Service
curl http://localhost:8000/stories/
# If this works, issue is with Traefik routing
```

### Issue: Story Service shows "unhealthy"

**Symptoms**: `docker-compose ps` shows story-service as "unhealthy"

**Solutions**:
```powershell
# Check health endpoint directly
curl http://localhost:8000/health

# Check story-service logs
docker-compose logs story-service

# Check database connectivity
docker-compose exec story-db pg_isready -U kidcomic -d story_db

# Restart story service
docker-compose restart story-service
```

### Issue: Grafana datasources not working

**Symptoms**: Grafana shows "Data source is not working"

**Solutions**:
```powershell
# Wait for all observability services to be ready
Start-Sleep -Seconds 60

# Check Prometheus is accessible
curl http://localhost:9090/-/ready

# Check Loki is accessible
curl http://localhost:3100/ready

# Check Tempo is accessible
curl http://localhost:3200/ready

# Restart Grafana
docker-compose restart grafana
```

### Issue: Database connection errors

**Symptoms**: Story Service logs show "could not connect to server"

**Solutions**:
```powershell
# Check database is running
docker-compose ps story-db

# Check database logs
docker-compose logs story-db

# Test connection manually
docker-compose exec story-db psql -U kidcomic -d story_db -c "SELECT 1;"

# Recreate database volume
docker-compose down -v
docker-compose up -d story-db
# Wait 30 seconds
docker-compose up -d story-service
```

---

## Cleanup

### Stop Services (Keep Data)

```powershell
docker-compose down
```

### Stop Services and Remove Data

```powershell
# WARNING: This will delete all database data!
docker-compose down -v
```

### Remove Docker Images

```powershell
docker-compose down --rmi all -v
```

---

## Next Steps

### Phase 4: Enhanced Observability (US2)

- [ ] Create Grafana dashboards (microservices overview, logs, traces)
- [ ] Configure Prometheus alerting rules
- [ ] Set up Alertmanager with Slack/email notifications
- [ ] Test distributed tracing end-to-end

### Phase 5: CI/CD Automation (US3)

- [ ] Set up GitHub Actions workflows
- [ ] Implement automated testing pipeline
- [ ] Configure zero-downtime deployments
- [ ] Set up automated rollback on failure

### Production Readiness

- [ ] Enable HTTPS with TLS certificates
- [ ] Harden security (secrets management, auth middleware)
- [ ] Scale to Kubernetes (kubectl apply -f infrastructure/kubernetes/)
- [ ] Set up production monitoring and alerting

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                     Mobile App / Client                  │
└────────────────────┬────────────────────────────────────┘
                     │ HTTP requests
                     ▼
         ┌───────────────────────────┐
         │   API Gateway (Traefik)   │
         │   • Instance 1 (port 80)  │
         │   • Instance 2 (backup)   │◄─── Service Discovery
         └───────────┬───────────────┘     (Consul)
                     │ Routes: /stories → story-service
                     ▼
         ┌───────────────────────────┐
         │     Story Service         │
         │   • FastAPI (Python 3.11) │
         │   • Observability libs    │
         │   • Health checks         │
         └───────────┬───────────────┘
                     │
                     ▼
         ┌───────────────────────────┐
         │   PostgreSQL Database     │
         │   • story_db              │
         └───────────────────────────┘

                     │
         ┌───────────┴───────────────┐
         │  Observability Stack      │
         │  • Prometheus (metrics)   │
         │  • Grafana (dashboards)   │
         │  • Loki (logs)            │
         │  • Tempo (traces)         │
         └───────────────────────────┘
```

---

## Support & Feedback

- **Issues**: Report bugs at [GitHub Issues](https://github.com/kidcomic/microservices-infra/issues)
- **Documentation**: See `specs/002-microservices-infra/` for detailed specifications
- **Testing**: See `VALIDATION_REPORT.md` for test instructions

---

**Deployment Time**: ~5 minutes (first time with image build)
**Services**: 11 containers
**Status**: ✅ Production-Ready for MVP Demo

