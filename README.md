# StoryMe Microservices Infrastructure MVP

**Version**: v0.1.0
**Status**: Production Ready (90%)
**Last Updated**: 2025-12-06

---

## 🎯 Quick Start (5 Minutes)

```powershell
# Option 1: Automated deployment with validation
.\deploy-and-validate.ps1

# Option 2: Quick start without validation
.\quick-start.ps1

# Option 3: Manual deployment
Copy-Item .env.example .env
docker-compose up -d
```

**Access your services**:
- **API Gateway**: http://localhost/stories/
- **Traefik Dashboard**: http://localhost:8080/dashboard/
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Consul**: http://localhost:8500

---

## 📋 What's Included

### Services Deployed (11 containers)

```
✅ API Gateway (Traefik v3)
   • 2 instances for HA
   • Auto-discovery & routing
   • Metrics & tracing

✅ Story Service
   • FastAPI + Python 3.11
   • Full observability
   • PostgreSQL database

✅ Service Discovery (Consul)
   • Automatic service registration
   • Health checks with auto-deregistration
   • Dynamic service discovery

✅ Observability Stack
   • Prometheus (metrics)
   • Grafana (dashboards)
   • Loki (logs)
   • Tempo (traces)
```

### Features

- ✅ **High Availability**: 2 gateway instances with automatic failover
- ✅ **Observability**: Complete logging, metrics, and tracing
- ✅ **Dynamic Service Discovery**: Consul-based auto-registration & Prometheus SD
- ✅ **Auto-Scaling**: Kubernetes HPA configuration (2-10 instances)
- ✅ **Health Monitoring**: Prometheus alerts with 16+ rules
- ✅ **Security Middleware**: Rate limiting, CORS, security headers
- ✅ **Production Ready**: Runbooks, troubleshooting, rollback procedures

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| **[MVP_DEPLOYMENT_GUIDE.md](MVP_DEPLOYMENT_GUIDE.md)** | Complete deployment instructions with troubleshooting |
| **[MVP_IMPLEMENTATION_SUMMARY.md](MVP_IMPLEMENTATION_SUMMARY.md)** | Technical implementation details |
| **[PHASE3_COMPLETE.md](PHASE3_COMPLETE.md)** | Phase 3: Infrastructure setup |
| **[PHASE_4_VALIDATION_REPORT.md](PHASE_4_VALIDATION_REPORT.md)** | Phase 4: System validation results |
| **[PHASE_5_OBSERVABILITY_STATUS.md](PHASE_5_OBSERVABILITY_STATUS.md)** | Phase 5: Traefik middleware & Grafana |
| **[PHASE_6_COMPLETE.md](PHASE_6_COMPLETE.md)** | Phase 6: Metrics & alerts configuration |
| **[PHASE_8_COMPLETE.md](PHASE_8_COMPLETE.md)** | Phase 8: Consul service discovery |
| **[gateway-failover.md](infrastructure/ci-cd/runbooks/gateway-failover.md)** | Operations runbook for incident response |

---

## 🛠️ Prerequisites

### Required

- **Docker Desktop** 20.10+
  - Download: https://www.docker.com/products/docker-desktop
  - RAM: 8GB minimum (16GB recommended)
  - Disk: 10GB free space

### Optional (for testing)

- **Python 3.11+** - For running test suites
- **k6** - For load testing (https://k6.io/)
- **curl** or **Postman** - For API testing

---

## 🚀 Deployment Options

### Option 1: Automated Deployment (Recommended)

```powershell
# Full deployment with validation (takes ~5-10 minutes)
.\deploy-and-validate.ps1

# Skip deployment (use existing services)
.\deploy-and-validate.ps1 -SkipDeploy

# Skip tests (deploy only)
.\deploy-and-validate.ps1 -SkipTests

# Verbose output
.\deploy-and-validate.ps1 -Verbose
```

**What it does**:
- ✅ Pre-deployment checks (Docker, ports, disk space)
- ✅ Environment setup (.env creation)
- ✅ Service deployment (docker-compose up)
- ✅ Health verification (all 11 services)
- ✅ Validation tests (T044-T047)
- ✅ Generates validation report

### Option 2: Quick Start

```powershell
# Minimal deployment (no validation)
.\quick-start.ps1
```

**What it does**:
- ✅ Environment setup
- ✅ Service deployment
- ✅ Basic health check
- ⏭️ Skips detailed validation

### Option 3: Manual Deployment

```powershell
# 1. Setup environment
Copy-Item .env.example .env

# 2. Start services
docker-compose up -d

# 3. Wait for healthy state
Start-Sleep -Seconds 60

# 4. Verify
docker-compose ps
curl http://localhost/stories/
```

---

## 🧪 Testing

### Run All Tests

```powershell
# Full test suite (requires deployment)
.\deploy-and-validate.ps1 -SkipDeploy
```

### Run Individual Tests

```powershell
# Contract tests (T044)
cd tests\integration
python -m pytest test_gateway_routing.py -v

# End-to-end tests (T045)
cd tests\e2e
python -m pytest test_gateway_e2e.py -v

# Load tests (T046) - requires k6
cd tests\load
k6 run test_gateway_load.js
```

---

## 📊 Monitoring & Dashboards

### Access Dashboards

```powershell
# Open all dashboards
Start-Process "http://localhost:8080"  # Traefik
Start-Process "http://localhost:3000"  # Grafana
Start-Process "http://localhost:8500"  # Consul
Start-Process "http://localhost:9090"  # Prometheus
```

### Prometheus Queries

```promql
# Number of healthy gateway instances
count(up{job="traefik"} == 1)

# Number of healthy microservices (Consul SD)
count(up{job="microservices"} == 1)

# Gateway request rate
sum(rate(traefik_service_requests_total[5m]))

# Microservice request rate
sum(rate(http_requests_total{job="microservices"}[5m])) by (service)

# Gateway p95 latency
histogram_quantile(0.95, rate(traefik_service_request_duration_seconds_bucket[5m]))

# Service health
service_health

# Services registered in Consul
count(consul_catalog_services)
```

### View Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f story-service
docker-compose logs -f traefik-1

# Filter by trace ID
docker-compose logs story-service | Select-String "test-trace-123"
```

---

## 🆘 Troubleshooting

### Services Not Starting

```powershell
# Check Docker daemon
docker ps

# Check logs
docker-compose logs

# Reset and retry
docker-compose down -v
docker-compose up -d
```

### Port Conflicts

```powershell
# Check which ports are in use
netstat -ano | findstr :80
netstat -ano | findstr :8000

# Change ports in .env file
# GATEWAY_PORT=8080
# STORY_SERVICE_PORT=8001
```

### Cannot Access Gateway

```powershell
# Test direct service access
curl http://localhost:8000/stories/

# If works, check Traefik routing
docker-compose logs traefik-1

# Check Traefik dashboard
Start-Process "http://localhost:8080/dashboard/"
```

**Full troubleshooting guide**: [MVP_DEPLOYMENT_GUIDE.md - Troubleshooting](MVP_DEPLOYMENT_GUIDE.md#troubleshooting)

---

## 🔄 Maintenance Commands

```powershell
# Stop services (keep data)
docker-compose down

# Stop and remove data
docker-compose down -v

# Restart specific service
docker-compose restart story-service

# View service status
docker-compose ps

# Scale gateway instances
docker-compose up -d --scale traefik-1=3

# Update service
docker-compose pull story-service
docker-compose up -d story-service
```

---

## 📁 Project Structure

```
D:\kidcomic/
├── 📄 README.md                          # This file
├── 📄 docker-compose.yml                 # Service orchestration
├── 📄 .env.example                       # Environment template
├── 📄 quick-start.ps1                    # Quick deployment script
├── 📄 deploy-and-validate.ps1            # Full deployment + validation
├── 📁 services/
│   ├── api-gateway/                      # Traefik configuration
│   │   ├── traefik.yml
│   │   └── middlewares/                  # Auth, rate-limit, etc.
│   └── story-service/                    # Sample microservice
│       ├── Dockerfile
│       ├── requirements.txt
│       └── src/
│           ├── main.py                   # FastAPI application
│           └── health.py                 # Health checks
├── 📁 shared/
│   ├── lib-logging/                      # Logging library
│   ├── lib-tracing/                      # Tracing library
│   └── lib-config/                       # Config library
├── 📁 infrastructure/
│   ├── observability/
│   │   ├── prometheus/
│   │   │   ├── prometheus.yml
│   │   │   └── alerts/gateway-health.yml # Alert rules
│   │   ├── grafana/
│   │   ├── loki/
│   │   └── tempo/
│   ├── kubernetes/
│   │   └── gateway-hpa.yml               # Auto-scaling config
│   └── ci-cd/
│       └── runbooks/
│           └── gateway-failover.md       # Operations runbook
├── 📁 tests/
│   ├── integration/                      # Contract tests
│   ├── e2e/                              # End-to-end tests
│   └── load/                             # Load tests (k6)
└── 📁 specs/
    └── 002-microservices-infra/
        ├── spec.md                       # Full specification
        ├── plan.md                       # Implementation plan
        └── tasks.md                      # Task breakdown
```

---

## 🎯 API Endpoints

### Story Service (via Gateway)

```bash
# List all stories
curl http://localhost/stories/

# Get specific story
curl http://localhost/stories/1

# Personalize story
curl -X POST "http://localhost/stories/1/personalize?child_name=Emma"

# Health check (direct access, not via gateway)
curl http://localhost:8000/health

# Readiness check (direct access, not via gateway)
curl http://localhost:8000/ready

# Metrics (with trailing slash)
curl http://localhost:8000/metrics/
```

### Traefik Gateway

```bash
# Health check
curl http://localhost:8080/ping

# Dashboard
http://localhost:8080/dashboard/

# Metrics
curl http://localhost:8082/metrics
```

---

## 🔐 Security Notes

### Development vs Production

This MVP is configured for **development use**. For production:

- [ ] Change default passwords in `.env`
- [ ] Enable HTTPS with TLS certificates
- [ ] Configure JWT authentication (middleware ready)
- [ ] Use Docker secrets for sensitive data
- [ ] Enable rate limiting for public endpoints
- [ ] Review and harden security headers
- [ ] Set up firewall rules
- [ ] Enable log encryption

**Security checklist**: [MVP_DEPLOYMENT_GUIDE.md - Production Readiness](MVP_DEPLOYMENT_GUIDE.md#production-readiness)

---

## 🚦 Status

| Component | Status | Notes |
|-----------|--------|-------|
| **API Gateway** | ✅ Production Ready | HA configured, 2 instances, middleware active |
| **Story Service** | ✅ Production Ready | Full observability, Consul registered |
| **Observability** | ✅ Production Ready | Logs, metrics, traces, Grafana dashboards |
| **Service Discovery** | ✅ Production Ready | Consul with auto-registration & health checks |
| **Prometheus SD** | ✅ Production Ready | Dynamic service discovery via Consul |
| **Auto-Scaling** | ✅ Configuration Ready | K8s HPA configured (2-10 instances) |
| **Monitoring** | ✅ Alerts Configured | 16+ Prometheus alert rules |
| **E2E Tests** | ✅ 100% Pass Rate | 8/8 tests passing |
| **Documentation** | ✅ Complete | 8 phases documented, runbooks ready |

---

## 📞 Support

- **Deployment Issues**: See [MVP_DEPLOYMENT_GUIDE.md](MVP_DEPLOYMENT_GUIDE.md)
- **Operations**: See [gateway-failover.md](infrastructure/ci-cd/runbooks/gateway-failover.md)
- **Architecture**: See [MVP_IMPLEMENTATION_SUMMARY.md](MVP_IMPLEMENTATION_SUMMARY.md)

---

## 🗺️ Roadmap

### ✅ Phase 1-3: Infrastructure Foundation - Complete
- ✅ Docker Compose orchestration
- ✅ Traefik v3 API Gateway (HA with 2 instances)
- ✅ Consul service registry
- ✅ Observability stack (Prometheus, Grafana, Loki, Tempo)
- ✅ Story Service MVP with PostgreSQL

### ✅ Phase 4: System Validation - Complete
- ✅ Comprehensive health checks (9/9 services)
- ✅ E2E test suite (100% pass rate)
- ✅ Performance baseline validation
- ✅ Production readiness assessment

### ✅ Phase 5: Traefik Middleware - Complete
- ✅ Fixed Traefik v3 middleware loading
- ✅ Security headers middleware
- ✅ Rate limiting & CORS
- ✅ Grafana dashboard integration

### ✅ Phase 6: Metrics & Alerts - Complete
- ✅ Story Service metrics export
- ✅ 16+ Prometheus alert rules
- ✅ Service health monitoring
- ✅ Infrastructure alerts

### ✅ Phase 7: E2E Test Refinement - Complete
- ✅ Fixed API contract mismatches
- ✅ Security headers validation
- ✅ Performance baseline updates
- ✅ 100% test pass rate achieved

### ✅ Phase 8: Dynamic Service Discovery - Complete
- ✅ Full Consul service registration
- ✅ Prometheus Consul service discovery
- ✅ Automatic health check integration
- ✅ Zero-config metrics scraping

### 🎉 MVP Complete: 90% Production Ready

**All Core Features Implemented**:
- ✅ High availability API gateway
- ✅ Dynamic service discovery
- ✅ Complete observability stack
- ✅ Automated monitoring & alerting
- ✅ Security middleware
- ✅ Comprehensive testing

### ⏳ Future Enhancements
- TLS/HTTPS configuration
- Authentication & authorization
- CI/CD pipeline automation
- Additional microservices (User, Payment, Photo, Content)

---

## 📜 License

Copyright © 2025 StoryMe. All rights reserved.

---

**Version**: v0.1.0
**Last Updated**: 2025-12-06
**Status**: 90% Production Ready - All 8 Phases Complete
**Maintainer**: Platform Team

