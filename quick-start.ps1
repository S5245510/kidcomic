# Quick Start Script - Deploy MVP in 5 Minutes
# Usage: .\quick-start.ps1

Write-Host "`n🚀 StoryMe Microservices MVP - Quick Start" -ForegroundColor Cyan
Write-Host "=========================================`n" -ForegroundColor Cyan

# Step 1: Create .env
Write-Host "Step 1: Setting up environment..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item .env.example .env
    Write-Host "✓ Created .env file" -ForegroundColor Green
} else {
    Write-Host "✓ .env file already exists" -ForegroundColor Green
}

# Step 2: Start services
Write-Host "`nStep 2: Starting services..." -ForegroundColor Yellow
Write-Host "(This may take a few minutes for first-time setup)"
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Services started successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to start services" -ForegroundColor Red
    Write-Host "Run: docker-compose logs" -ForegroundColor Yellow
    exit 1
}

# Step 3: Wait for health checks
Write-Host "`nStep 3: Waiting for services to be healthy..." -ForegroundColor Yellow
Write-Host "Waiting 60 seconds..."
Start-Sleep -Seconds 60

# Step 4: Verify deployment
Write-Host "`nStep 4: Verifying deployment..." -ForegroundColor Yellow

$allHealthy = $true

# Check docker-compose
Write-Host "Checking service status..."
$services = docker-compose ps --format json | ConvertFrom-Json
$runningCount = ($services | Where-Object { $_.State -eq "running" -or $_.State -match "Up" }).Count
$totalCount = $services.Count

if ($runningCount -eq $totalCount) {
    Write-Host "✓ All $totalCount services are running" -ForegroundColor Green
} else {
    Write-Host "⚠ Only $runningCount of $totalCount services are running" -ForegroundColor Yellow
    $allHealthy = $false
}

# Test gateway
Write-Host "Testing API Gateway..."
try {
    $response = Invoke-WebRequest -Uri "http://localhost/stories/" -TimeoutSec 10 -UseBasicParsing
    $data = $response.Content | ConvertFrom-Json
    Write-Host "✓ Gateway is responding - $($data.total) stories available" -ForegroundColor Green
} catch {
    Write-Host "✗ Gateway is not responding" -ForegroundColor Red
    $allHealthy = $false
}

# Final status
Write-Host "`n==========================================" -ForegroundColor Cyan
if ($allHealthy) {
    Write-Host "✅ DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "🌐 Access your services:" -ForegroundColor Yellow
    Write-Host "   • API:        http://localhost/stories/"
    Write-Host "   • Traefik:    http://localhost:8080/dashboard/"
    Write-Host "   • Grafana:    http://localhost:3000 (admin/admin)"
    Write-Host "   • Prometheus: http://localhost:9090"
    Write-Host "   • Consul:     http://localhost:8500"
    Write-Host ""
    Write-Host "🧪 Run full validation:" -ForegroundColor Yellow
    Write-Host "   .\deploy-and-validate.ps1 -SkipDeploy"
    Write-Host ""
    Write-Host "📖 Documentation:" -ForegroundColor Yellow
    Write-Host "   MVP_DEPLOYMENT_GUIDE.md"
    Write-Host ""
} else {
    Write-Host "⚠️  DEPLOYMENT COMPLETED WITH WARNINGS" -ForegroundColor Yellow
    Write-Host "==========================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Some services may need more time to start."
    Write-Host "Wait 2 minutes and run: docker-compose ps"
    Write-Host ""
    Write-Host "📖 Troubleshooting:" -ForegroundColor Yellow
    Write-Host "   MVP_DEPLOYMENT_GUIDE.md (Troubleshooting section)"
    Write-Host ""
}
Write-Host "=========================================`n" -ForegroundColor Cyan
