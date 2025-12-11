# MVP Deployment Walkthrough

**Ready to Deploy**: ✅ All files created and ready
**Estimated Time**: 10 minutes
**Your Role**: Run the commands below

---

## 🚀 Deployment Steps

### Step 1: Open PowerShell

1. Press `Win + X`
2. Select "Windows PowerShell" or "Terminal"
3. Navigate to project directory:

```powershell
cd D:\kidcomic
```

### Step 2: Run Deployment Script

**Option A: Full Automated Deployment (Recommended)**

```powershell
.\deploy-and-validate.ps1
```

**Option B: Quick Start (Faster, No Validation)**

```powershell
.\quick-start.ps1
```

---

## 📊 What You'll See

### Expected Output (deploy-and-validate.ps1)

```
=== Step 1: Pre-Deployment Checks ===
Checking Docker...
✓ Docker installed: Docker version 24.0.6, build ed223bc
✓ Docker daemon is running
Checking port availability...
✓ All required ports are available
Checking disk space...
✓ Disk space: 45.23 GB free

=== Step 2: Environment Setup ===
Creating .env from .env.example...
✓ Created .env file

=== Step 3: Deploying Services ===
Stopping existing services...
✓ Stopped existing services
Pulling Docker images...
[+] Pulling...
Building Story Service image...
[+] Building...
Starting services...
[+] Running 11/11
✓ Services started

Waiting for services to be healthy (60 seconds)...

=== Step 4: Verifying Service Health ===
Checking service status...
✓ traefik-1 is running
✓ traefik-2 is running
✓ story-service is running
✓ story-db is running
✓ consul is running
✓ prometheus is running
✓ grafana is running
✓ loki is running
✓ tempo is running
✓ All 11 services are healthy

Testing service endpoints...
✓ Traefik Dashboard accessible (http://localhost:8080)
✓ Consul UI accessible (http://localhost:8500)
✓ Prometheus accessible (http://localhost:9090)
✓ Grafana accessible (http://localhost:3000)
✓ Story Service accessible (http://localhost:8000)

Testing API Gateway routing...
✓ Story Service accessible via Gateway (http://localhost/stories/)
✓ Story Service returned 3 stories

=== Step 5: Running Validation Tests (T044-T047) ===

T044: Running Contract Tests...
Running: pytest test_gateway_routing.py -v
test_gateway_routing.py::TestGatewayRoutingContract::test_traefik_config_exists PASSED
test_gateway_routing.py::TestGatewayRoutingContract::test_story_service_route_exists PASSED
...
✓ T044: Contract tests PASSED (or PARTIAL - expected)

T045: Running End-to-End Tests...
Running: pytest test_gateway_e2e.py -v
test_gateway_e2e.py::TestGatewayE2E::test_gateway_is_accessible PASSED
test_gateway_e2e.py::TestGatewayE2E::test_route_to_story_service_health PASSED
test_gateway_e2e.py::TestGatewayE2E::test_route_to_story_service_list PASSED
...
✓ T045: E2E tests PASSED

T046: Running Load Tests...
⚠ k6 not installed. Skipping load tests.
Install k6: https://k6.io/docs/getting-started/installation/

T047: Verifying Error Handling...
✓ 404 error handling works correctly
✓ Story not found error handling works correctly
✓ T047: Error handling verification PASSED

=== Step 6: Generating Validation Report ===
✓ Validation report saved to: VALIDATION_RESULTS_2025-12-05_14-30-00.md

========================================
         VALIDATION SUMMARY
========================================
Total Tests:   25
Passed:        23
Failed:        0
Warnings:      1
Skipped:       1
Duration:      347.52 seconds
========================================

========================================
         DEPLOYMENT COMPLETE
========================================

📊 Dashboards:
   • Traefik:    http://localhost:8080/dashboard/
   • Grafana:    http://localhost:3000 (admin/admin)
   • Prometheus: http://localhost:9090
   • Consul:     http://localhost:8500

🔍 Test API:
   curl http://localhost/stories/

📝 Full Report:
   VALIDATION_RESULTS_2025-12-05_14-30-00.md

📖 Documentation:
   • Deployment: MVP_DEPLOYMENT_GUIDE.md
   • Summary:    MVP_IMPLEMENTATION_SUMMARY.md
   • Runbook:    infrastructure/ci-cd/runbooks/gateway-failover.md

========================================
```

---

## ✅ Verification Checklist

After deployment completes, verify:

### 1. All Services Running

```powershell
docker-compose ps
```

**Expected**: All services show "Up" or "Up (healthy)"

### 2. API Gateway Works

```powershell
curl http://localhost/stories/
```

**Expected**: JSON response with 3 stories

```json
{
  "stories": [
    {
      "id": 1,
      "title": "The Brave Little Turtle",
      "content": "Once upon a time...",
      "age_range": "3-5",
      "moral_lesson": "Courage comes in all sizes"
    },
    ...
  ],
  "total": 3
}
```

### 3. Dashboards Accessible

```powershell
# Open all dashboards
Start-Process "http://localhost:8080/dashboard/"  # Traefik
Start-Process "http://localhost:3000"             # Grafana
Start-Process "http://localhost:8500"             # Consul
Start-Process "http://localhost:9090"             # Prometheus
```

**Expected**: All dashboards load successfully

### 4. Health Checks Pass

```powershell
# Test health endpoints
curl http://localhost/stories/health
curl http://localhost/stories/ready
curl http://localhost:8080/ping
```

**Expected**: All return 200 OK

---

## 🎬 Demo Your MVP

Once deployed, demonstrate:

### Demo 1: API Gateway Routing

```powershell
# List all stories
curl http://localhost/stories/

# Get specific story
curl http://localhost/stories/1

# Personalize story
curl -X POST "http://localhost/stories/1/personalize?child_name=Emma"
```

### Demo 2: High Availability

```powershell
# Show 2 gateway instances
docker-compose ps | Select-String "traefik"

# Stop primary instance
docker-compose stop traefik-1

# Requests still work!
curl http://localhost/stories/

# Restart instance
docker-compose up -d traefik-1
```

### Demo 3: Observability

1. **Open Traefik Dashboard**: http://localhost:8080/dashboard/
   - Show 2 router rules
   - Show service health
   - Show request metrics

2. **Open Grafana**: http://localhost:3000
   - Login: admin/admin
   - Navigate to Data Sources
   - Show Prometheus, Loki, Tempo configured

3. **Open Prometheus**: http://localhost:9090
   - Navigate to Status → Targets
   - Show all services being scraped
   - Run query: `up{job="traefik"}`

4. **View Logs**:
   ```powershell
   # Show JSON structured logs
   docker-compose logs story-service | Select-String "trace_id"
   ```

### Demo 4: Trace ID Propagation

```powershell
# Send request with trace ID
curl -H "X-Trace-ID: demo-trace-12345" http://localhost/stories/ -I

# Check response headers
# Should see: X-Trace-ID: demo-trace-12345

# Find in logs
docker-compose logs story-service | Select-String "demo-trace-12345"
```

---

## 🐛 Troubleshooting

### Issue: Script Execution Policy Error

**Error**:
```
.\deploy-and-validate.ps1 : File cannot be loaded because running scripts is disabled
```

**Solution**:
```powershell
# Run PowerShell as Administrator and execute:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then try again:
.\deploy-and-validate.ps1
```

### Issue: Port 80 Already in Use

**Error**:
```
Error: Port 80 is already in use
```

**Solution**:
```powershell
# Check what's using port 80
netstat -ano | findstr :80

# Option 1: Stop the process
# Option 2: Change gateway port in .env
# GATEWAY_PORT=8080

# Then restart
docker-compose down
docker-compose up -d
```

### Issue: Docker Daemon Not Running

**Error**:
```
Cannot connect to Docker daemon
```

**Solution**:
1. Open Docker Desktop
2. Wait for Docker to start (whale icon in system tray)
3. Run script again

### Issue: Services Not Healthy

**Check logs**:
```powershell
# View all logs
docker-compose logs

# View specific service
docker-compose logs story-service
docker-compose logs traefik-1

# Follow logs in real-time
docker-compose logs -f story-service
```

**Common fixes**:
```powershell
# Restart specific service
docker-compose restart story-service

# Full reset
docker-compose down -v
docker-compose up -d
```

### Issue: Cannot Access Dashboards

**Wait longer**:
```powershell
# Services may need more time
Start-Sleep -Seconds 60

# Then check again
curl http://localhost:8080/ping
```

**Check service status**:
```powershell
docker-compose ps grafana
docker-compose logs grafana
```

---

## 📊 Validation Results

After deployment, you'll have a detailed report:

**Location**: `VALIDATION_RESULTS_<timestamp>.md`

**Contents**:
- ✅ Pre-deployment checks
- ✅ Service health status
- ✅ Endpoint accessibility
- ✅ Test results (T044-T047)
- ✅ Performance metrics
- ✅ Next steps recommendations

---

## 🎯 Success Criteria

Your MVP is successfully deployed when:

- [x] All 11 services running
- [x] API Gateway responds: `curl http://localhost/stories/`
- [x] Traefik dashboard accessible: http://localhost:8080
- [x] Grafana accessible: http://localhost:3000
- [x] Prometheus shows targets: http://localhost:9090/targets
- [x] E2E tests pass (T045)
- [x] Error handling works (T047)

**Optional** (requires k6 installed):
- [ ] Load tests pass (T046)

---

## 📞 Need Help?

If deployment fails:

1. **Check Prerequisites**:
   - Docker Desktop running?
   - Ports available?
   - Enough disk space?

2. **Review Logs**:
   ```powershell
   docker-compose logs
   ```

3. **Consult Documentation**:
   - MVP_DEPLOYMENT_GUIDE.md (Troubleshooting section)
   - gateway-failover.md (Operations runbook)

4. **Reset and Retry**:
   ```powershell
   docker-compose down -v
   .\deploy-and-validate.ps1
   ```

---

## 🚀 You're Ready!

**Run this command now**:

```powershell
cd D:\kidcomic
.\deploy-and-validate.ps1
```

The script will take care of everything and report back with results.

**Estimated Time**: 10 minutes
**Expected Outcome**: ✅ All services deployed and validated

---

**Good luck with your deployment!** 🎉

