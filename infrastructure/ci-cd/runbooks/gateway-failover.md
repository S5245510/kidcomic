# API Gateway Manual Failover Runbook

**Last Updated**: 2025-12-05
**Severity**: Critical
**Estimated Time**: 5-15 minutes
**Owner**: Platform Team

---

## Purpose

This runbook provides step-by-step procedures for handling API Gateway failures and performing manual failover when automatic recovery fails.

**When to use this runbook**:
- Alert: `GatewayInstancesLow` (< 2 healthy instances)
- Alert: `GatewayCompleteOutage` (all instances down)
- Gateway not responding to health checks
- Manual failover requested during maintenance

---

## Prerequisites

### Required Access
- [ ] SSH access to infrastructure hosts
- [ ] Docker command access (for Docker Compose deployments)
- [ ] kubectl access (for Kubernetes deployments)
- [ ] Prometheus/Grafana dashboard access

### Required Tools
- [ ] `docker` / `docker-compose` (for Docker deployments)
- [ ] `kubectl` (for Kubernetes deployments)
- [ ] `curl` (for testing endpoints)
- [ ] PowerShell or Bash terminal

---

## Quick Reference

### Health Check Endpoints

```bash
# Traefik health endpoint
curl http://localhost:8080/ping

# Traefik dashboard
http://localhost:8080/dashboard/

# Prometheus targets
http://localhost:9090/targets

# Gateway routing test
curl http://localhost/stories/health
```

### Key Metrics

```promql
# Number of healthy gateway instances
count(up{job="traefik"} == 1)

# Gateway request rate
sum(rate(traefik_service_requests_total[5m]))

# Gateway error rate
sum(rate(traefik_service_requests_total{code=~"5.."}[5m]))
/
sum(rate(traefik_service_requests_total[5m]))
```

---

## Incident Response Procedures

### Scenario 1: Single Gateway Instance Down (Warning)

**Symptoms**:
- Alert: `GatewayInstanceDown`
- Prometheus shows 1 of 2 instances down
- Requests still being served by healthy instance

**Impact**: LOW - HA maintained, service operational

**Procedure**:

#### Docker Compose

```powershell
# 1. Check which instance is down
docker-compose ps | Select-String "traefik"

# 2. Check logs for the down instance
docker-compose logs traefik-1  # or traefik-2

# 3. Attempt restart
docker-compose restart traefik-1

# 4. Wait 30 seconds for health check
Start-Sleep -Seconds 30

# 5. Verify instance is healthy
docker-compose ps traefik-1

# 6. Test routing
curl http://localhost/stories/health
```

#### Kubernetes

```bash
# 1. Check pod status
kubectl get pods -l app=traefik

# 2. Describe failing pod
kubectl describe pod <pod-name>

# 3. Check logs
kubectl logs <pod-name>

# 4. Delete pod (will be recreated by deployment)
kubectl delete pod <pod-name>

# 5. Verify new pod is running
kubectl get pods -l app=traefik -w
```

**Verification**:
- [ ] Both instances show "Up (healthy)"
- [ ] Prometheus target shows 2/2 up
- [ ] Test requests succeed

---

### Scenario 2: Multiple Gateway Instances Down (Critical)

**Symptoms**:
- Alert: `GatewayInstancesLow` (< 2 instances)
- Prometheus shows < 2 instances healthy
- Intermittent request failures

**Impact**: MEDIUM - HA compromised, single point of failure

**Procedure**:

#### Docker Compose

```powershell
# 1. Stop all gateway instances
docker-compose stop traefik-1 traefik-2

# 2. Check for port conflicts
netstat -ano | findstr :80
netstat -ano | findstr :443

# 3. Check Docker daemon
docker ps
docker system df

# 4. Start instances sequentially
docker-compose up -d traefik-1
Start-Sleep -Seconds 30
docker-compose up -d traefik-2

# 5. Verify both healthy
docker-compose ps | Select-String "traefik"

# 6. Test routing
curl http://localhost/stories/
```

#### Kubernetes

```bash
# 1. Check deployment status
kubectl get deployment traefik-gateway

# 2. Scale down to 0 (clean restart)
kubectl scale deployment traefik-gateway --replicas=0

# 3. Wait for pods to terminate
kubectl get pods -l app=traefik -w

# 4. Scale back to 2
kubectl scale deployment traefik-gateway --replicas=2

# 5. Verify pods are running
kubectl get pods -l app=traefik
```

**Verification**:
- [ ] 2 or more instances healthy
- [ ] Prometheus shows 2+ targets up
- [ ] Load test passes
- [ ] Alert cleared

---

### Scenario 3: Complete Gateway Outage (Emergency)

**Symptoms**:
- Alert: `GatewayCompleteOutage`
- All instances down
- All API requests failing
- Mobile app cannot access services

**Impact**: CRITICAL - Complete service outage

**Emergency Procedure**:

#### Step 1: Immediate Assessment (2 minutes)

```powershell
# Check if this is a network issue
ping localhost

# Check Docker daemon
docker ps

# Check system resources
docker stats --no-stream

# Check disk space
Get-PSDrive C
```

#### Step 2: Emergency Restart (5 minutes)

```powershell
# Docker Compose - Full reset
docker-compose down
docker-compose up -d consul  # Start service discovery first
Start-Sleep -Seconds 30
docker-compose up -d traefik-1 traefik-2
Start-Sleep -Seconds 60

# Verify services
docker-compose ps
```

```bash
# Kubernetes - Emergency scale-up
kubectl scale deployment traefik-gateway --replicas=0
kubectl scale deployment traefik-gateway --replicas=3  # Extra instance for safety

# Force recreate if needed
kubectl rollout restart deployment traefik-gateway
```

#### Step 3: Verify Recovery (3 minutes)

```powershell
# 1. Check health endpoints
curl http://localhost:8080/ping
curl http://localhost/stories/health

# 2. Run smoke test
Invoke-WebRequest http://localhost/stories/ | Select-Object StatusCode

# 3. Check Prometheus
curl http://localhost:9090/api/v1/query?query=up{job="traefik"}

# 4. Monitor error logs
docker-compose logs -f --tail=50 traefik-1
```

**Verification**:
- [ ] All instances healthy
- [ ] Health checks passing
- [ ] Requests succeeding
- [ ] Error rate < 1%
- [ ] Alert cleared

---

### Scenario 4: Gateway Unresponsive (High Latency)

**Symptoms**:
- Alert: `GatewayHighLatency`
- Requests timing out
- p95 latency > 50ms

**Impact**: MEDIUM - Service degraded

**Procedure**:

```powershell
# 1. Check CPU/memory usage
docker stats traefik-1 traefik-2 --no-stream

# 2. Check backend service health
curl http://localhost:8000/health  # Story service direct

# 3. Check Consul service discovery
curl http://localhost:8500/v1/catalog/services

# 4. Scale up instances (temporary relief)
# Docker Compose: Start additional instance manually
docker run -d --name traefik-3 \
  --network kidcomic_backend \
  -v $(pwd)/services/api-gateway/traefik.yml:/etc/traefik/traefik.yml \
  traefik:v3.0

# Kubernetes: Scale up
kubectl scale deployment traefik-gateway --replicas=4
```

**Verification**:
- [ ] Latency returns to < 50ms
- [ ] CPU usage < 70%
- [ ] Alert cleared

---

## Rollback Procedures

### Rollback Docker Compose Deployment

```powershell
# 1. Stop current version
docker-compose down

# 2. Restore previous docker-compose.yml
git checkout HEAD~1 docker-compose.yml

# 3. Pull previous images
docker-compose pull traefik

# 4. Start with previous version
docker-compose up -d

# 5. Verify
docker-compose ps
curl http://localhost/stories/health
```

### Rollback Kubernetes Deployment

```bash
# 1. Check rollout history
kubectl rollout history deployment traefik-gateway

# 2. Rollback to previous version
kubectl rollout undo deployment traefik-gateway

# 3. Check rollout status
kubectl rollout status deployment traefik-gateway

# 4. Verify
kubectl get pods -l app=traefik
curl http://traefik-gateway/stories/health
```

---

## Post-Incident Actions

### Immediate (Within 1 hour)

- [ ] Document incident timeline in `incidents/<date>-gateway-outage.md`
- [ ] Update stakeholders via status page / Slack
- [ ] Collect logs and metrics for investigation
  ```powershell
  # Collect logs
  docker-compose logs traefik-1 > logs/traefik-1-$(Get-Date -Format "yyyy-MM-dd-HH-mm").log
  docker-compose logs traefik-2 > logs/traefik-2-$(Get-Date -Format "yyyy-MM-dd-HH-mm").log

  # Export Prometheus data
  curl "http://localhost:9090/api/v1/query_range?query=up{job='traefik'}&start=<start_time>&end=<end_time>" > metrics.json
  ```

### Short-term (Within 24 hours)

- [ ] Root cause analysis meeting
- [ ] Update monitoring/alerting if needed
- [ ] Test failover procedures
- [ ] Update this runbook with lessons learned

### Long-term (Within 1 week)

- [ ] Post-mortem document
- [ ] Implement preventive measures
- [ ] Update disaster recovery plan
- [ ] Training session for team

---

## Escalation Path

### Level 1: On-Call Engineer
- **Action**: Follow this runbook
- **Escalate if**: Cannot resolve within 15 minutes

### Level 2: Platform Team Lead
- **Contact**: Slack @platform-lead
- **Escalate if**: Complete outage > 15 minutes

### Level 3: CTO / Engineering Director
- **Contact**: Phone (critical incidents only)
- **Escalate if**: Outage > 30 minutes or customer-facing

---

## Common Issues & Solutions

### Issue: Port 80 already in use

```powershell
# Find process using port 80
netstat -ano | findstr :80

# Kill process (if safe)
Stop-Process -Id <PID> -Force

# Or change gateway port in .env
# GATEWAY_PORT=8080
```

### Issue: Docker daemon not responding

```powershell
# Restart Docker Desktop
Restart-Service Docker

# Or restart Docker Desktop application
```

### Issue: Configuration syntax error

```powershell
# Validate Traefik configuration
docker run --rm -v $(pwd)/services/api-gateway/traefik.yml:/traefik.yml traefik:v3.0 traefik --configFile=/traefik.yml --validate
```

### Issue: Backend services unreachable

```powershell
# Check network connectivity
docker-compose exec traefik-1 ping story-service
docker-compose exec traefik-1 curl http://story-service:8000/health

# Restart backend service
docker-compose restart story-service
```

---

## Testing Failover

### Chaos Engineering Test

```powershell
# Test 1: Kill primary instance
docker-compose stop traefik-1

# Verify requests still work
for($i=0; $i -lt 10; $i++) {
    curl http://localhost/stories/health
    Start-Sleep -Seconds 1
}

# Restart
docker-compose up -d traefik-1

# Test 2: Network partition simulation
docker network disconnect kidcomic_backend traefik-1
Start-Sleep -Seconds 30
docker network connect kidcomic_backend traefik-1
```

---

## Related Documents

- [Gateway Architecture](../../../specs/002-microservices-infra/plan.md)
- [Monitoring Guide](../../../docs/monitoring.md)
- [Incident Response Plan](../../../docs/incident-response.md)
- [Prometheus Alerts](../../observability/prometheus/alerts/gateway-health.yml)

---

## Runbook Maintenance

**Review Frequency**: Quarterly
**Last Review**: 2025-12-05
**Next Review**: 2026-03-05
**Owner**: Platform Team

**Change Log**:
- 2025-12-05: Initial version (T043)

