# Port Configuration Guide

## Overview

This document explains the port configuration for the KidComic microservices infrastructure and how to resolve port conflicts.

## Port Conflict Resolution

Docker Compose automatically reassigns ports when they're already in use on your host system. The following ports have been reassigned to avoid conflicts:

### Current Port Mappings

| Service | Default Port | Actual Port | Reason |
|---------|-------------|-------------|---------|
| **Grafana** | 3000 | **3001** | Port 3000 in use by `open-webui` |
| **PostgreSQL** | 5432 | **5433** | Port 5432 likely in use by local PostgreSQL |
| **Traefik Dashboard** | 8080 | **8088** | Port conflict detected |
| **Traefik Dashboard (Instance 2)** | 8081 | **8089** | Sequential reassignment |
| **Consul UI** | 8500 | **8500** | Port available |
| **Prometheus** | 9090 | **9090** | Port available |
| **Loki** | 3100 | **3100** | Port available |
| **Tempo** | 4317 | **4317** | Port available |
| **Story Service** | 8000 | **8000** | Port available |

## Configuration Files

### .env File

The `.env` file contains all port configurations. Docker Compose and deployment scripts read from this file:

```bash
# API Gateway (Traefik)
TRAEFIK_HTTP_PORT=80
TRAEFIK_DASHBOARD_PORT=8088
TRAEFIK_DASHBOARD_2_PORT=8089
TRAEFIK_METRICS_PORT=8082
TRAEFIK_METRICS_2_PORT=8083

# Observability Stack
PROMETHEUS_PORT=9090
GRAFANA_PORT=3001
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=admin
LOKI_PORT=3100
TEMPO_PORT=4317
TEMPO_HTTP_PORT=3200

# Database Configuration
STORY_DB_PORT=5433

# Service Discovery (Consul)
CONSUL_PORT=8500
```

## How Port Configuration Works

### Inter-Container Communication (Internal)

Services inside Docker communicate using **container names** and **internal ports**:

```yaml
# Story Service connects to database
POSTGRES_HOST=story-db    # Container name (not localhost)
POSTGRES_PORT=5432        # Internal port (always 5432 inside Docker)
```

**These internal ports NEVER change**, regardless of host port conflicts.

### Host-to-Container Communication (External)

Accessing services from your host machine requires the **exposed/reassigned ports**:

```bash
# Correct: Using reassigned port
http://localhost:3001/api/health        # Grafana

# Incorrect: Using default port (will fail)
http://localhost:3000/api/health        # Won't work - port reassigned!
```

## Service Access URLs

Use these URLs to access services from your host:

### Observability Stack
- **Grafana Dashboard**: http://localhost:3001 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Consul UI**: http://localhost:8500/ui
- **Traefik Dashboard**: http://localhost:8088/dashboard/
- **Traefik Dashboard (Instance 2)**: http://localhost:8089/dashboard/

### Application Services
- **API Gateway**: http://localhost:80
- **Story Service (Direct)**: http://localhost:8000/health
- **Story Service (via Gateway)**: http://localhost/stories/

### Database Access
- **PostgreSQL**: localhost:5433
  ```bash
  psql -h localhost -p 5433 -U kidcomic -d story_db
  ```

## Resolving Port Conflicts

If you encounter port conflicts during deployment:

### Option 1: Stop Conflicting Services

```bash
# Find what's using the port
netstat -ano | findstr ":3000"

# Stop the conflicting container
docker stop open-webui

# Or stop a Windows service using the port
Stop-Service -Name "PostgreSQL"
```

### Option 2: Update Port Assignments

1. Edit `.env` file to use different ports:
   ```bash
   GRAFANA_PORT=3002
   STORY_DB_PORT=5434
   ```

2. Restart services:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Option 3: Accept Automatic Reassignment

Docker Compose will automatically reassign ports. Just update your `.env` file to match the assigned ports (check with `docker-compose ps`).

## Verification

### Check Current Port Mappings

```powershell
# View all container port mappings
docker-compose ps

# Check specific service
docker port kidcomic-grafana-1
```

### Check What's Using a Port

```powershell
# Windows
netstat -ano | findstr ":3000"

# Get process details
Get-Process -Id <PID>
```

### Update .env After Deployment

If Docker reassigns ports automatically:

1. Check actual ports:
   ```bash
   docker-compose ps
   ```

2. Update `.env` to match:
   ```bash
   GRAFANA_PORT=<actual-port>
   ```

3. Re-run validation:
   ```bash
   .\deploy-and-validate.ps1
   ```

## Backend Code Implications

### No Changes Needed for Inter-Service Communication

Backend services use environment variables and container names:

```python
# shared/lib-config/src/database.py
host = os.getenv("POSTGRES_HOST", "localhost")  # Gets "story-db" in Docker
port = int(os.getenv("POSTGRES_PORT", "5432"))  # Always 5432 inside Docker
```

### Changes Needed for External Tests

Test files now read from environment:

```python
# tests/e2e/test_gateway_e2e.py
def gateway_url():
    port = os.getenv("TRAEFIK_HTTP_PORT", "80")
    return f"http://localhost:{port}"
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs for port conflicts
docker-compose logs <service-name>

# Look for "address already in use"
```

### Tests Fail with Connection Refused

1. Verify service is running:
   ```bash
   docker-compose ps
   ```

2. Check port mapping:
   ```bash
   docker port kidcomic-<service>-1
   ```

3. Update `.env` with correct ports

### Dashboard Not Accessible

```bash
# Verify Traefik is running
docker-compose logs traefik-1

# Check port mapping
echo $env:TRAEFIK_DASHBOARD_PORT  # Should be 8088

# Access using correct port
http://localhost:8088/dashboard/
```

## Best Practices

1. **Always use environment variables** for port configuration
2. **Never hardcode ports** in application code
3. **Check `.env` file** before deployment
4. **Verify port mappings** after `docker-compose up`
5. **Update documentation** if ports change
6. **Use container names** for inter-service communication

## Related Files

- `.env` - Port configuration
- `docker-compose.yml` - Service definitions with port mappings
- `deploy-and-validate.ps1` - Deployment script (reads from .env)
- `tests/e2e/test_gateway_e2e.py` - E2E tests (reads from .env)

---

**Last Updated**: 2025-12-06
**Port Configuration Version**: 1.0
