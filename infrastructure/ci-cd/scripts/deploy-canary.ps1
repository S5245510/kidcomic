#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Canary deployment script for gradual rollout (10% → 50% → 100%)
    Per T109 [US4]: Implements FR-032 gradual rollout capability

.DESCRIPTION
    Deploys a new service version using canary deployment strategy:
    1. Deploy canary version to small percentage of traffic (10%)
    2. Monitor metrics (error rate, latency, health)
    3. Gradually increase traffic: 10% → 50% → 100%
    4. Automatic rollback if metrics degrade

.PARAMETER ServiceName
    Name of the service to deploy (e.g., "story-service")

.PARAMETER NewVersion
    New version tag to deploy (e.g., "v2.0.0")

.PARAMETER OldVersion
    Current stable version tag (e.g., "v1.0.0")

.PARAMETER Environment
    Target environment (staging, production)

.PARAMETER PrometheusUrl
    Prometheus URL for metrics queries (default: http://localhost:9090)

.PARAMETER SkipRollback
    Skip automatic rollback on failure (for testing)

.EXAMPLE
    .\deploy-canary.ps1 -ServiceName story-service -NewVersion v2.0.0 -OldVersion v1.0.0 -Environment staging

.EXAMPLE
    .\deploy-canary.ps1 -ServiceName story-service -NewVersion v2.0.0 -OldVersion v1.0.0 -Environment production -PrometheusUrl http://prometheus:9090
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceName,

    [Parameter(Mandatory=$true)]
    [string]$NewVersion,

    [Parameter(Mandatory=$true)]
    [string]$OldVersion,

    [Parameter(Mandatory=$false)]
    [ValidateSet("staging", "production")]
    [string]$Environment = "staging",

    [Parameter(Mandatory=$false)]
    [string]$PrometheusUrl = "http://localhost:9090",

    [Parameter(Mandatory=$false)]
    [switch]$SkipRollback
)

# Configuration
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

# Canary deployment stages
$CanaryStages = @(
    @{ Percentage = 10; Duration = 300; Description = "Initial canary (10% traffic)" },
    @{ Percentage = 50; Duration = 300; Description = "Medium rollout (50% traffic)" },
    @{ Percentage = 100; Duration = 0; Description = "Full rollout (100% traffic)" }
)

# Health check thresholds
$ErrorRateThreshold = 5.0  # 5% error rate
$LatencyP95Threshold = 500  # 500ms p95 latency
$HealthCheckInterval = 10  # Check metrics every 10 seconds
$FailedChecksBeforeRollback = 3  # Rollback after 3 consecutive failures

# Colors for output
function Write-Info-Message {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success-Message {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning-Message {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Write-Step {
    param([string]$Message)
    Write-Host "`n===================================" -ForegroundColor Magenta
    Write-Host $Message -ForegroundColor Magenta
    Write-Host "===================================`n" -ForegroundColor Magenta
}

# Check prerequisites
function Test-Prerequisites {
    Write-Step "Checking Prerequisites"

    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-Info-Message "Docker: $dockerVersion"
    } catch {
        Write-Error-Message "Docker is not installed or not in PATH"
        exit 1
    }

    # Check kubectl (if using Kubernetes)
    try {
        $kubectlVersion = kubectl version --client --short 2>$null
        Write-Info-Message "Kubectl: $kubectlVersion"
    } catch {
        Write-Warning-Message "Kubectl not found - assuming Docker Compose deployment"
    }

    # Verify Prometheus is accessible
    try {
        $response = Invoke-RestMethod -Uri "$PrometheusUrl/api/v1/status/config" -TimeoutSec 5
        if ($response.status -eq "success") {
            Write-Success-Message "Prometheus is accessible at $PrometheusUrl"
        }
    } catch {
        Write-Warning-Message "Prometheus not accessible at $PrometheusUrl - metrics monitoring disabled"
    }

    Write-Success-Message "Prerequisites check complete"
}

# Deploy canary version
function Deploy-CanaryVersion {
    param(
        [int]$TrafficPercentage
    )

    Write-Step "Deploying Canary Version ($TrafficPercentage% traffic)"

    $canaryContainerName = "${ServiceName}-canary"
    $canaryPort = 8100  # Different port for canary

    # Pull new version image
    Write-Info-Message "Pulling new version: $NewVersion"
    docker pull "ghcr.io/$($env:GITHUB_REPOSITORY)/${ServiceName}:${NewVersion}"

    # Stop existing canary container if running
    try {
        docker stop $canaryContainerName 2>$null
        docker rm $canaryContainerName 2>$null
    } catch {
        # Container doesn't exist, continue
    }

    # Start canary container
    Write-Info-Message "Starting canary container on port $canaryPort"
    docker run -d `
        --name $canaryContainerName `
        --network kidcomic_backend `
        -p "${canaryPort}:8000" `
        -e SERVICE_ENV=$Environment `
        -e SERVICE_VERSION=$NewVersion `
        "ghcr.io/$($env:GITHUB_REPOSITORY)/${ServiceName}:${NewVersion}"

    # Wait for health check
    Write-Info-Message "Waiting for canary to become healthy..."
    $healthCheckUrl = "http://localhost:${canaryPort}/health"
    $healthCheckTimeout = 120  # 2 minutes
    $elapsedTime = 0

    while ($elapsedTime -lt $healthCheckTimeout) {
        try {
            $response = Invoke-RestMethod -Uri $healthCheckUrl -TimeoutSec 5
            if ($response.status -eq "healthy") {
                Write-Success-Message "Canary is healthy"
                return $true
            }
        } catch {
            # Health check not ready yet
        }

        Start-Sleep -Seconds 5
        $elapsedTime += 5
    }

    Write-Error-Message "Canary failed health check after ${healthCheckTimeout}s"
    return $false
}

# Update traffic split in Traefik
function Update-TrafficSplit {
    param(
        [int]$CanaryPercentage
    )

    Write-Info-Message "Updating traffic split: ${CanaryPercentage}% to canary, $((100 - $CanaryPercentage))% to stable"

    $stableWeight = 100 - $CanaryPercentage
    $canaryWeight = $CanaryPercentage

    # Update Traefik dynamic configuration
    $dynamicConfig = @"
http:
  services:
    ${ServiceName}-weighted:
      weighted:
        services:
          - name: ${ServiceName}-stable
            weight: $stableWeight
          - name: ${ServiceName}-canary
            weight: $canaryWeight

    ${ServiceName}-stable:
      loadBalancer:
        servers:
          - url: "http://${ServiceName}:8000"

    ${ServiceName}-canary:
      loadBalancer:
        servers:
          - url: "http://${ServiceName}-canary:8000"

  routers:
    ${ServiceName}-router:
      rule: "PathPrefix(\`/v1/stories\`) || PathPrefix(\`/v2/stories\`)"
      service: ${ServiceName}-weighted
      entryPoints:
        - web
      middlewares:
        - standard-chain
"@

    # Write to Traefik dynamic config file
    $dynamicConfigPath = "services/api-gateway/dynamic-canary.yml"
    $dynamicConfig | Out-File -FilePath $dynamicConfigPath -Encoding utf8

    Write-Success-Message "Traffic split updated to ${CanaryPercentage}% canary"
}

# Query Prometheus metrics
function Get-ServiceMetrics {
    param(
        [string]$Version
    )

    $metrics = @{
        ErrorRate = 0.0
        LatencyP95 = 0.0
        RequestRate = 0.0
    }

    try {
        # Query error rate (percentage)
        $errorRateQuery = "rate(http_requests_total{service=`"$ServiceName`",version=`"$Version`",status=~`"5..`"}[5m]) / rate(http_requests_total{service=`"$ServiceName`",version=`"$Version`"}[5m]) * 100"
        $errorRateUrl = "$PrometheusUrl/api/v1/query?query=$([System.Web.HttpUtility]::UrlEncode($errorRateQuery))"
        $errorRateResponse = Invoke-RestMethod -Uri $errorRateUrl -TimeoutSec 5

        if ($errorRateResponse.data.result.Count -gt 0) {
            $metrics.ErrorRate = [double]$errorRateResponse.data.result[0].value[1]
        }

        # Query p95 latency (milliseconds)
        $latencyQuery = "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service=`"$ServiceName`",version=`"$Version`"}[5m])) * 1000"
        $latencyUrl = "$PrometheusUrl/api/v1/query?query=$([System.Web.HttpUtility]::UrlEncode($latencyQuery))"
        $latencyResponse = Invoke-RestMethod -Uri $latencyUrl -TimeoutSec 5

        if ($latencyResponse.data.result.Count -gt 0) {
            $metrics.LatencyP95 = [double]$latencyResponse.data.result[0].value[1]
        }

        # Query request rate
        $requestRateQuery = "rate(http_requests_total{service=`"$ServiceName`",version=`"$Version`"}[5m])"
        $requestRateUrl = "$PrometheusUrl/api/v1/query?query=$([System.Web.HttpUtility]::UrlEncode($requestRateQuery))"
        $requestRateResponse = Invoke-RestMethod -Uri $requestRateUrl -TimeoutSec 5

        if ($requestRateResponse.data.result.Count -gt 0) {
            $metrics.RequestRate = [double]$requestRateResponse.data.result[0].value[1]
        }

    } catch {
        Write-Warning-Message "Failed to query Prometheus metrics: $_"
    }

    return $metrics
}

# Monitor canary health
function Test-CanaryHealth {
    param(
        [int]$DurationSeconds
    )

    Write-Info-Message "Monitoring canary health for ${DurationSeconds}s..."

    $endTime = (Get-Date).AddSeconds($DurationSeconds)
    $failedChecks = 0

    while ((Get-Date) -lt $endTime) {
        # Get canary metrics
        $canaryMetrics = Get-ServiceMetrics -Version $NewVersion

        Write-Host "  Error Rate: $($canaryMetrics.ErrorRate.ToString('F2'))% | P95 Latency: $($canaryMetrics.LatencyP95.ToString('F0'))ms | Request Rate: $($canaryMetrics.RequestRate.ToString('F2'))/s" -ForegroundColor Gray

        # Check thresholds
        $healthOk = $true

        if ($canaryMetrics.ErrorRate -gt $ErrorRateThreshold) {
            Write-Warning-Message "Error rate ($($canaryMetrics.ErrorRate.ToString('F2'))%) exceeds threshold ($ErrorRateThreshold%)"
            $healthOk = $false
        }

        if ($canaryMetrics.LatencyP95 -gt $LatencyP95Threshold) {
            Write-Warning-Message "P95 latency ($($canaryMetrics.LatencyP95.ToString('F0'))ms) exceeds threshold ($LatencyP95Threshold ms)"
            $healthOk = $false
        }

        if (-not $healthOk) {
            $failedChecks++
            Write-Warning-Message "Failed health check $failedChecks/$FailedChecksBeforeRollback"

            if ($failedChecks -ge $FailedChecksBeforeRollback) {
                Write-Error-Message "Canary failed $FailedChecksBeforeRollback consecutive health checks"
                return $false
            }
        } else {
            # Reset failed checks counter on success
            $failedChecks = 0
        }

        Start-Sleep -Seconds $HealthCheckInterval
    }

    Write-Success-Message "Canary health check passed"
    return $true
}

# Rollback to stable version
function Invoke-Rollback {
    Write-Step "Rolling Back to Stable Version"

    Write-Info-Message "Setting traffic to 100% stable version ($OldVersion)"
    Update-TrafficSplit -CanaryPercentage 0

    Write-Info-Message "Stopping canary container"
    docker stop "${ServiceName}-canary" 2>$null
    docker rm "${ServiceName}-canary" 2>$null

    Write-Success-Message "Rollback complete - stable version serving 100% traffic"
}

# Complete rollout
function Complete-Rollout {
    Write-Step "Completing Rollout"

    Write-Info-Message "Promoting canary to stable"

    # Tag canary as new stable
    docker tag "ghcr.io/$($env:GITHUB_REPOSITORY)/${ServiceName}:${NewVersion}" "${ServiceName}:stable"

    # Update stable service to use new version
    docker stop "${ServiceName}" 2>$null
    docker rm "${ServiceName}" 2>$null

    docker run -d `
        --name "${ServiceName}" `
        --network kidcomic_backend `
        -p "8000:8000" `
        -e SERVICE_ENV=$Environment `
        -e SERVICE_VERSION=$NewVersion `
        "ghcr.io/$($env:GITHUB_REPOSITORY)/${ServiceName}:${NewVersion}"

    # Stop canary
    docker stop "${ServiceName}-canary" 2>$null
    docker rm "${ServiceName}-canary" 2>$null

    # Reset traffic split to 100% stable
    Update-TrafficSplit -CanaryPercentage 0

    Write-Success-Message "Rollout complete - new version ($NewVersion) is now stable"
}

# Main deployment flow
function Start-CanaryDeployment {
    Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
    Write-Host "║          CANARY DEPLOYMENT - GRADUAL ROLLOUT              ║" -ForegroundColor Cyan
    Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Cyan

    Write-Info-Message "Service: $ServiceName"
    Write-Info-Message "Old Version: $OldVersion"
    Write-Info-Message "New Version: $NewVersion"
    Write-Info-Message "Environment: $Environment"
    Write-Info-Message "Prometheus: $PrometheusUrl"

    # Check prerequisites
    Test-Prerequisites

    # Deploy canary
    $deployed = Deploy-CanaryVersion -TrafficPercentage 10
    if (-not $deployed) {
        Write-Error-Message "Canary deployment failed - health check did not pass"
        exit 1
    }

    # Gradual rollout stages
    foreach ($stage in $CanaryStages) {
        Write-Step "Stage: $($stage.Description)"

        # Update traffic split
        Update-TrafficSplit -CanaryPercentage $stage.Percentage

        # Monitor health (skip for 100% stage)
        if ($stage.Duration -gt 0) {
            $healthy = Test-CanaryHealth -DurationSeconds $stage.Duration

            if (-not $healthy -and -not $SkipRollback) {
                Write-Error-Message "Canary health check failed at $($stage.Percentage)% traffic"
                Invoke-Rollback
                exit 1
            }
        }

        Write-Success-Message "Stage complete: $($stage.Description)"
    }

    # Complete rollout
    Complete-Rollout

    Write-Host "`n╔════════════════════════════════════════════════════════════╗" -ForegroundColor Green
    Write-Host "║            CANARY DEPLOYMENT SUCCESSFUL                    ║" -ForegroundColor Green
    Write-Host "╚════════════════════════════════════════════════════════════╝`n" -ForegroundColor Green

    Write-Info-Message "Deployment Summary:"
    Write-Info-Message "  - Service: $ServiceName"
    Write-Info-Message "  - Version: $OldVersion → $NewVersion"
    Write-Info-Message "  - Environment: $Environment"
    Write-Info-Message "  - Status: COMPLETE"
}

# Execute deployment
Start-CanaryDeployment
