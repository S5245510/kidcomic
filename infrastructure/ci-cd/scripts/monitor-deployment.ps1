<#
.SYNOPSIS
    Deployment Health Monitoring Script (T086)

.DESCRIPTION
    Monitors service health after deployment:
    - Error rate threshold: <5%
    - Latency threshold: <500ms p95
    - Monitoring duration: configurable (default 10 minutes)

    Triggers rollback if thresholds exceeded

    Per FR-020: Monitor deployment health and trigger rollback

.PARAMETER ServiceName
    Name of the service to monitor

.PARAMETER DurationMinutes
    How long to monitor (default: 10 minutes)

.PARAMETER ErrorRateThreshold
    Maximum acceptable error rate percentage (default: 5%)

.PARAMETER LatencyThresholdMs
    Maximum acceptable p95 latency in milliseconds (default: 500ms)

.EXAMPLE
    .\monitor-deployment.ps1 -ServiceName "story-service" -DurationMinutes 10 -ErrorRateThreshold 5 -LatencyThresholdMs 500
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceName,

    [Parameter()]
    [int]$DurationMinutes = 10,

    [Parameter()]
    [double]$ErrorRateThreshold = 5.0,

    [Parameter()]
    [int]$LatencyThresholdMs = 500
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Configuration
$CheckInterval = 30  # Check metrics every 30 seconds
$PrometheusUrl = "http://localhost:9090"

# Color output
function Write-Info { param([string]$Message); Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message); Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message); Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error-Message { param([string]$Message); Write-Host "[ERROR] $Message" -ForegroundColor Red }

function Get-ServiceMetrics {
    param([string]$ServiceName)

    try {
        # Query Prometheus for error rate
        $errorRateQuery = "rate(http_requests_total{service=`"$ServiceName`",status=~`"5..`"}[5m]) / rate(http_requests_total{service=`"$ServiceName`"}[5m]) * 100"
        $errorRateUrl = "$PrometheusUrl/api/v1/query?query=$([uri]::EscapeDataString($errorRateQuery))"

        $errorRateResponse = Invoke-RestMethod -Uri $errorRateUrl -TimeoutSec 5
        $errorRate = if ($errorRateResponse.data.result.Count -gt 0) {
            [double]$errorRateResponse.data.result[0].value[1]
        } else { 0.0 }

        # Query Prometheus for p95 latency
        $latencyQuery = "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{service=`"$ServiceName`"}[5m])) * 1000"
        $latencyUrl = "$PrometheusUrl/api/v1/query?query=$([uri]::EscapeDataString($latencyQuery))"

        $latencyResponse = Invoke-RestMethod -Uri $latencyUrl -TimeoutSec 5
        $p95Latency = if ($latencyResponse.data.result.Count -gt 0) {
            [double]$latencyResponse.data.result[0].value[1]
        } else { 0.0 }

        return @{
            ErrorRate = $errorRate
            P95LatencyMs = $p95Latency
            Timestamp = Get-Date
        }
    }
    catch {
        Write-Warning "Could not fetch metrics from Prometheus: $_"
        return $null
    }
}

function Test-HealthThresholds {
    param(
        [hashtable]$Metrics,
        [double]$ErrorThreshold,
        [int]$LatencyThreshold
    )

    $healthy = $true
    $reasons = @()

    if ($Metrics.ErrorRate -gt $ErrorThreshold) {
        $healthy = $false
        $reasons += "Error rate ${Metrics.ErrorRate:F2}% exceeds threshold $ErrorThreshold%"
    }

    if ($Metrics.P95LatencyMs -gt $LatencyThreshold) {
        $healthy = $false
        $reasons += "P95 latency ${Metrics.P95LatencyMs:F2}ms exceeds threshold ${LatencyThreshold}ms"
    }

    return @{
        Healthy = $healthy
        Reasons = $reasons
    }
}

# Main monitoring loop
Write-Info "=========================================="
Write-Info "Deployment Health Monitoring"
Write-Info "=========================================="
Write-Info "Service: $ServiceName"
Write-Info "Duration: $DurationMinutes minutes"
Write-Info "Error Rate Threshold: $ErrorRateThreshold%"
Write-Info "Latency Threshold: ${LatencyThresholdMs}ms"
Write-Info "=========================================="
Write-Info ""

$endTime = (Get-Date).AddMinutes($DurationMinutes)
$checksPerformed = 0
$failedChecks = 0
$healthHistory = @()

while ((Get-Date) -lt $endTime) {
    $checksPerformed++
    $elapsed = [math]::Round((New-TimeSpan -Start (Get-Date) -End $endTime).TotalMinutes, 1)

    Write-Info "Check $checksPerformed (${elapsed} minutes remaining)..."

    # Get current metrics
    $metrics = Get-ServiceMetrics -ServiceName $ServiceName

    if ($metrics) {
        # Check thresholds
        $healthCheck = Test-HealthThresholds -Metrics $metrics -ErrorThreshold $ErrorRateThreshold -LatencyThreshold $LatencyThresholdMs

        # Display metrics
        Write-Host "  Error Rate: " -NoNewline
        if ($metrics.ErrorRate -gt $ErrorRateThreshold) {
            Write-Host "$($metrics.ErrorRate.ToString('F2'))%" -ForegroundColor Red
        } else {
            Write-Host "$($metrics.ErrorRate.ToString('F2'))%" -ForegroundColor Green
        }

        Write-Host "  P95 Latency: " -NoNewline
        if ($metrics.P95LatencyMs -gt $LatencyThresholdMs) {
            Write-Host "$($metrics.P95LatencyMs.ToString('F2'))ms" -ForegroundColor Red
        } else {
            Write-Host "$($metrics.P95LatencyMs.ToString('F2'))ms" -ForegroundColor Green
        }

        # Record health status
        $healthHistory += $healthCheck.Healthy

        # Check if deployment is unhealthy
        if (-not $healthCheck.Healthy) {
            $failedChecks++
            Write-Warning "Health check FAILED:"
            foreach ($reason in $healthCheck.Reasons) {
                Write-Warning "  - $reason"
            }

            # Trigger rollback if multiple consecutive failures
            if ($failedChecks -ge 3) {
                Write-Error-Message "=========================================="
                Write-Error-Message "CRITICAL: 3 consecutive health check failures"
                Write-Error-Message "Triggering automated rollback..."
                Write-Error-Message "=========================================="
                exit 1  # Exit with error to trigger rollback
            }
        }
        else {
            Write-Success "Health check PASSED"
            $failedChecks = 0  # Reset consecutive failures
        }
    }
    else {
        Write-Warning "Could not retrieve metrics (Prometheus may not be available)"
    }

    Write-Host ""

    # Wait before next check (unless this is the last iteration)
    if ((Get-Date) -lt $endTime.AddSeconds(-$CheckInterval)) {
        Start-Sleep -Seconds $CheckInterval
    }
}

# Final summary
$successRate = if ($healthHistory.Count -gt 0) {
    ($healthHistory | Where-Object { $_ }).Count / $healthHistory.Count * 100
} else { 0 }

Write-Info "=========================================="
Write-Info "Monitoring Complete"
Write-Info "=========================================="
Write-Info "Total Checks: $checksPerformed"
Write-Info "Success Rate: $($successRate.ToString('F1'))%"

if ($successRate -ge 95) {
    Write-Success "Deployment HEALTHY - Success rate: $($successRate.ToString('F1'))%"
    Write-Success "=========================================="
    exit 0
}
elseif ($successRate -ge 80) {
    Write-Warning "Deployment MARGINAL - Success rate: $($successRate.ToString('F1'))%"
    Write-Warning "Consider monitoring closely or rolling back"
    Write-Warning "=========================================="
    exit 0  # Don't trigger rollback, but warn
}
else {
    Write-Error-Message "Deployment UNHEALTHY - Success rate: $($successRate.ToString('F1'))%"
    Write-Error-Message "Triggering automated rollback..."
    Write-Error-Message "=========================================="
    exit 1  # Trigger rollback
}
