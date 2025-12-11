<#
.SYNOPSIS
    Rolling Deployment Script (T085)

.DESCRIPTION
    Implements rolling deployment strategy:
    1. Update instances one at a time
    2. Health check after each instance update
    3. Continue only if health checks pass
    4. Maintain minimum available instances during update

    Per FR-019: Zero-downtime deployments (alternative to blue-green)

.PARAMETER ServiceName
    Name of the service to deploy

.PARAMETER ImageTag
    Docker image tag to deploy

.PARAMETER Environment
    Target environment (staging, production)

.PARAMETER TotalInstances
    Total number of service instances

.PARAMETER WhatIf
    Dry-run mode

.EXAMPLE
    .\deploy-rolling.ps1 -ServiceName "story-service" -ImageTag "abc123" -Environment "staging" -TotalInstances 3
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceName,

    [Parameter(Mandatory=$true)]
    [string]$ImageTag,

    [Parameter(Mandatory=$true)]
    [ValidateSet("staging", "production")]
    [string]$Environment,

    [Parameter()]
    [int]$TotalInstances = 3,

    [Parameter()]
    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Configuration
$HealthCheckTimeout = 60   # 1 minute per instance
$HealthCheckInterval = 5   # 5 seconds

# Color output
function Write-Info { param([string]$Message); Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message); Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message); Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error-Message { param([string]$Message); Write-Host "[ERROR] $Message" -ForegroundColor Red }

function Update-ServiceInstance {
    param(
        [string]$InstanceName,
        [string]$ImageTag
    )

    Write-Info "Updating instance: $InstanceName"

    if ($WhatIf) {
        Write-Info "[DRY-RUN] Would update $InstanceName to $ImageTag"
        return $true
    }

    try {
        # Stop old instance
        docker stop $InstanceName | Out-Null

        # Remove old container
        docker rm $InstanceName | Out-Null

        # Start new instance with updated image
        docker run -d `
            --name $InstanceName `
            --network kidcomic_backend `
            -e SERVICE_ENV=$Environment `
            "ghcr.io/$($env:GITHUB_REPOSITORY)/${ServiceName}:${ImageTag}"

        Write-Success "Instance updated: $InstanceName"
        return $true
    }
    catch {
        Write-Error-Message "Failed to update instance: $_"
        return $false
    }
}

function Test-InstanceHealth {
    param([string]$InstanceName)

    Write-Info "Health checking: $InstanceName"

    if ($WhatIf) {
        Write-Info "[DRY-RUN] Would health check $InstanceName"
        return $true
    }

    # Get instance port
    $port = docker port $InstanceName | Select-String -Pattern "8000/tcp" | ForEach-Object {
        $_ -match "0\.0\.0\.0:(\d+)" | Out-Null
        $matches[1]
    }

    $healthUrl = "http://localhost:${port}/health"
    $elapsedTime = 0

    while ($elapsedTime -lt $HealthCheckTimeout) {
        try {
            $response = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 3
            if ($response.status -eq "healthy") {
                Write-Success "Instance healthy: $InstanceName"
                return $true
            }
        }
        catch {
            Start-Sleep -Seconds $HealthCheckInterval
            $elapsedTime += $HealthCheckInterval
        }
    }

    Write-Error-Message "Instance failed health check: $InstanceName"
    return $false
}

# Main rolling deployment
Write-Info "=========================================="
Write-Info "Rolling Deployment"
Write-Info "Service: $ServiceName"
Write-Info "Image Tag: $ImageTag"
Write-Info "Total Instances: $TotalInstances"
Write-Info "=========================================="

for ($i = 1; $i -le $TotalInstances; $i++) {
    $instanceName = "${ServiceName}-${i}"

    Write-Info "Processing instance $i of $TotalInstances"

    # Update instance
    if (-not (Update-ServiceInstance -InstanceName $instanceName -ImageTag $ImageTag)) {
        Write-Error-Message "Failed to update $instanceName - aborting rollout"
        exit 1
    }

    # Health check
    if (-not (Test-InstanceHealth -InstanceName $instanceName)) {
        Write-Error-Message "Health check failed for $instanceName - aborting rollout"
        exit 1
    }

    Write-Success "Instance $i updated successfully"

    # Brief pause before next instance
    if ($i -lt $TotalInstances) {
        Write-Info "Waiting 10 seconds before next instance..."
        Start-Sleep -Seconds 10
    }
}

Write-Success "=========================================="
Write-Success "Rolling Deployment Complete!"
Write-Success "All $TotalInstances instances updated"
Write-Success "=========================================="
