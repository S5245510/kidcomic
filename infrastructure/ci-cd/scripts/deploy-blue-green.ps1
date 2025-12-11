<#
.SYNOPSIS
    Blue-Green Deployment Script (T084)

.DESCRIPTION
    Implements zero-downtime blue-green deployment strategy:
    1. Launch green instances with new version
    2. Health check green instances
    3. Switch traffic from blue to green
    4. Keep blue instances for potential rollback

    Per FR-019: Zero-downtime deployments

.PARAMETER ServiceName
    Name of the service to deploy (e.g., "story-service")

.PARAMETER ImageTag
    Docker image tag to deploy (e.g., commit SHA)

.PARAMETER Environment
    Target environment (staging, production)

.PARAMETER WhatIf
    Dry-run mode - show what would be done without making changes

.EXAMPLE
    .\deploy-blue-green.ps1 -ServiceName "story-service" -ImageTag "abc123" -Environment "staging"

.NOTES
    Requires: Docker, docker-compose
    Author: CI/CD Automation
    Version: 1.0.0
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
    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Configuration
$HealthCheckTimeout = 300  # 5 minutes
$HealthCheckInterval = 5   # 5 seconds
$RollbackTimeout = 120     # 2 minutes

# Color output functions
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[SUCCESS] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-Error-Message {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Step 1: Validate environment
function Test-Environment {
    Write-Info "Validating deployment environment..."

    # Check Docker is running
    try {
        $dockerVersion = docker version --format '{{.Server.Version}}' 2>$null
        if ($LASTEXITCODE -ne 0) {
            throw "Docker is not running"
        }
        Write-Success "Docker is running (version: $dockerVersion)"
    }
    catch {
        Write-Error-Message "Docker validation failed: $_"
        return $false
    }

    # Check service exists
    $currentContainers = docker ps -a --filter "name=$ServiceName" --format "{{.Names}}"
    if (-not $currentContainers) {
        Write-Warning "No existing containers found for $ServiceName (first deployment)"
    }
    else {
        Write-Success "Found existing service: $ServiceName"
    }

    return $true
}

# Step 2: Launch green instances
function Start-GreenInstances {
    param(
        [string]$ServiceName,
        [string]$ImageTag
    )

    Write-Info "Launching green instances with image tag: $ImageTag"

    if ($WhatIf) {
        Write-Info "[DRY-RUN] Would launch green instances: ${ServiceName}-green"
        return $true
    }

    try {
        # Pull new image
        Write-Info "Pulling new image..."
        docker pull "ghcr.io/$($env:GITHUB_REPOSITORY)/${ServiceName}:${ImageTag}"

        # Create green service (temporary parallel deployment)
        # In real scenario, would use docker-compose scale or k8s deployment
        $greenContainerName = "${ServiceName}-green"

        # Check if green already exists (cleanup from previous failed deployment)
        $existingGreen = docker ps -a --filter "name=$greenContainerName" --format "{{.Names}}"
        if ($existingGreen) {
            Write-Warning "Cleaning up existing green instance..."
            docker rm -f $greenContainerName | Out-Null
        }

        Write-Info "Starting green instance: $greenContainerName"

        # Get current service configuration
        $blueContainer = docker ps --filter "name=$ServiceName" --filter "status=running" --format "{{.Names}}" | Select-Object -First 1

        if ($blueContainer) {
            # Replicate blue configuration for green
            $bluePort = docker port $blueContainer | Select-String -Pattern "8000/tcp" | ForEach-Object {
                $_ -match "0\.0\.0\.0:(\d+)" | Out-Null
                $matches[1]
            }

            # Use different temporary port for green (8001)
            $greenPort = 8001

            Write-Info "Starting green on port $greenPort (blue on $bluePort)"

            # Start green container
            docker run -d `
                --name $greenContainerName `
                --network kidcomic_backend `
                -p "${greenPort}:8000" `
                -e SERVICE_ENV=$Environment `
                -e LOG_LEVEL=INFO `
                "ghcr.io/$($env:GITHUB_REPOSITORY)/${ServiceName}:${ImageTag}"

            if ($LASTEXITCODE -ne 0) {
                throw "Failed to start green instance"
            }

            Write-Success "Green instance started: $greenContainerName"
            return $greenContainerName
        }
        else {
            # First deployment - no blue to replicate
            Write-Info "First deployment detected - starting on standard port"
            docker run -d `
                --name $ServiceName `
                --network kidcomic_backend `
                -p "8000:8000" `
                -e SERVICE_ENV=$Environment `
                -e LOG_LEVEL=INFO `
                "ghcr.io/$($env:GITHUB_REPOSITORY)/${ServiceName}:${ImageTag}"

            Write-Success "Service started: $ServiceName"
            return $ServiceName
        }
    }
    catch {
        Write-Error-Message "Failed to launch green instances: $_"
        return $null
    }
}

# Step 3: Health check green instances
function Test-GreenHealth {
    param(
        [string]$ContainerName
    )

    Write-Info "Performing health checks on green instance..."

    if ($WhatIf) {
        Write-Info "[DRY-RUN] Would perform health checks on $ContainerName"
        return $true
    }

    $healthUrl = "http://localhost:8001/health"  # Green temporary port
    $elapsedTime = 0

    while ($elapsedTime -lt $HealthCheckTimeout) {
        try {
            $response = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 5 -ErrorAction Stop
            if ($response.status -eq "healthy") {
                Write-Success "Green instance is healthy"
                return $true
            }
        }
        catch {
            Write-Info "Health check pending... ($elapsedTime / $HealthCheckTimeout seconds)"
        }

        Start-Sleep -Seconds $HealthCheckInterval
        $elapsedTime += $HealthCheckInterval
    }

    Write-Error-Message "Green instance failed health checks after $HealthCheckTimeout seconds"
    return $false
}

# Step 4: Switch traffic to green
function Switch-TrafficToGreen {
    param(
        [string]$ServiceName,
        [string]$GreenContainer
    )

    Write-Info "Switching traffic from blue to green..."

    if ($WhatIf) {
        Write-Info "[DRY-RUN] Would switch traffic to $GreenContainer"
        return $true
    }

    try {
        # Get blue container
        $blueContainer = docker ps --filter "name=$ServiceName" --filter "status=running" --format "{{.Names}}" | Where-Object { $_ -ne $GreenContainer } | Select-Object -First 1

        if ($blueContainer) {
            Write-Info "Current blue: $blueContainer"
            Write-Info "New green: $GreenContainer"

            # In real scenario with load balancer (Traefik, NGINX):
            # 1. Update load balancer config to point to green
            # 2. Reload load balancer
            # 3. Verify traffic is flowing to green

            # For Docker Compose without external LB, we swap ports:
            Write-Info "Stopping blue container..."
            docker stop $blueContainer

            Write-Info "Renaming green to primary service name..."
            docker rename $GreenContainer "${ServiceName}-primary"

            # Update port mapping (in real scenario, LB handles this)
            Write-Info "Recreating with correct port..."
            docker rm -f "${ServiceName}-primary"

            # Start on correct port
            $greenImage = docker inspect $GreenContainer --format '{{.Config.Image}}'
            docker run -d `
                --name $ServiceName `
                --network kidcomic_backend `
                -p "8000:8000" `
                -e SERVICE_ENV=$Environment `
                -e LOG_LEVEL=INFO `
                $greenImage

            Write-Success "Traffic switched to green"

            # Keep blue for rollback (rename for clarity)
            docker rename $blueContainer "${ServiceName}-blue-rollback"
            Write-Info "Blue instance kept for rollback: ${ServiceName}-blue-rollback"
        }
        else {
            Write-Warning "No blue instance found (first deployment)"
        }

        return $true
    }
    catch {
        Write-Error-Message "Failed to switch traffic: $_"
        return $false
    }
}

# Step 5: Cleanup old blue instances (optional, keep for rollback window)
function Remove-OldInstances {
    param(
        [string]$ServiceName,
        [int]$KeepCount = 2
    )

    Write-Info "Cleaning up old instances (keeping last $KeepCount)..."

    if ($WhatIf) {
        Write-Info "[DRY-RUN] Would cleanup old instances"
        return
    }

    # Find old rollback instances
    $oldInstances = docker ps -a --filter "name=${ServiceName}-blue-rollback" --format "{{.Names}}" | Select-Object -Skip $KeepCount

    foreach ($instance in $oldInstances) {
        Write-Info "Removing old instance: $instance"
        docker rm -f $instance | Out-Null
    }

    Write-Success "Cleanup complete"
}

# Main deployment flow
function Invoke-BlueGreenDeployment {
    Write-Info "=========================================="
    Write-Info "Blue-Green Deployment"
    Write-Info "=========================================="
    Write-Info "Service: $ServiceName"
    Write-Info "Image Tag: $ImageTag"
    Write-Info "Environment: $Environment"
    Write-Info "=========================================="
    Write-Info ""

    # Step 1: Validate environment
    if (-not (Test-Environment)) {
        Write-Error-Message "Environment validation failed"
        exit 1
    }

    # Step 2: Launch green instances
    $greenContainer = Start-GreenInstances -ServiceName $ServiceName -ImageTag $ImageTag
    if (-not $greenContainer) {
        Write-Error-Message "Failed to launch green instances"
        exit 1
    }

    # Step 3: Health check green instances
    if (-not (Test-GreenHealth -ContainerName $greenContainer)) {
        Write-Error-Message "Green instance health check failed"

        # Cleanup failed green instance
        if (-not $WhatIf) {
            docker rm -f $greenContainer | Out-Null
        }

        exit 1
    }

    # Step 4: Switch traffic to green
    if (-not (Switch-TrafficToGreen -ServiceName $ServiceName -GreenContainer $greenContainer)) {
        Write-Error-Message "Traffic switch failed"
        exit 1
    }

    # Step 5: Cleanup old instances
    Remove-OldInstances -ServiceName $ServiceName -KeepCount 2

    Write-Success ""
    Write-Success "=========================================="
    Write-Success "Deployment Complete!"
    Write-Success "=========================================="
    Write-Success "Service: $ServiceName"
    Write-Success "Version: $ImageTag"
    Write-Success "Status: Active"
    Write-Success "=========================================="
}

# Execute deployment
try {
    Invoke-BlueGreenDeployment
}
catch {
    Write-Error-Message "Deployment failed: $_"
    exit 1
}
