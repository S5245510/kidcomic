<#
.SYNOPSIS
    Automated Rollback Script (T087)

.DESCRIPTION
    Automatically rolls back failed deployment:
    1. Identify previous stable version
    2. Stop failing new version
    3. Restore previous version
    4. Verify previous version is healthy
    5. Log rollback event

    Per FR-020: Automated rollback on deployment failure
    Target: Complete rollback within 2 minutes

.PARAMETER ServiceName
    Name of the service to rollback

.PARAMETER Environment
    Environment to rollback (staging, production)

.PARAMETER WhatIf
    Dry-run mode

.EXAMPLE
    .\auto-rollback.ps1 -ServiceName "story-service" -Environment "staging"
#>

[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceName,

    [Parameter(Mandatory=$true)]
    [ValidateSet("staging", "production")]
    [string]$Environment,

    [Parameter()]
    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Configuration
$RollbackTimeout = 120  # 2 minutes max
$HealthCheckTimeout = 60  # 1 minute for health verification

# Color output
function Write-Info { param([string]$Message); Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message); Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message); Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error-Message { param([string]$Message); Write-Host "[ERROR] $Message" -ForegroundColor Red }

function Get-PreviousVersion {
    param([string]$ServiceName)

    Write-Info "Identifying previous stable version..."

    if ($WhatIf) {
        Write-Info "[DRY-RUN] Would identify previous version"
        return "${ServiceName}-blue-rollback"
    }

    # Look for blue rollback container (from blue-green deployment)
    $blueContainer = docker ps -a --filter "name=${ServiceName}-blue-rollback" --format "{{.Names}}" | Select-Object -First 1

    if ($blueContainer) {
        Write-Success "Found previous version: $blueContainer"
        return $blueContainer
    }

    # Check deployment history
    $historyFile = "$PSScriptRoot/../deployment-history.json"
    if (Test-Path $historyFile) {
        $history = Get-Content $historyFile -Raw | ConvertFrom-Json
        $lastSuccess = $history | Where-Object {
            $_.service -eq $ServiceName -and
            $_.status -eq "success" -and
            $_.rollback -ne $true
        } | Select-Object -First 1

        if ($lastSuccess) {
            Write-Success "Found previous successful version: $($lastSuccess.version)"
            return $lastSuccess.version
        }
    }

    Write-Error-Message "Could not identify previous stable version"
    return $null
}

function Stop-CurrentVersion {
    param([string]$ServiceName)

    Write-Info "Stopping current (failing) version..."

    if ($WhatIf) {
        Write-Info "[DRY-RUN] Would stop current version of $ServiceName"
        return $true
    }

    try {
        # Stop current running instance
        $currentContainer = docker ps --filter "name=$ServiceName" --filter "status=running" --format "{{.Names}}" | Where-Object { $_ -notmatch "rollback" } | Select-Object -First 1

        if ($currentContainer) {
            Write-Info "Stopping: $currentContainer"
            docker stop $currentContainer | Out-Null

            Write-Info "Removing: $currentContainer"
            docker rm $currentContainer | Out-Null

            Write-Success "Current version stopped and removed"
            return $true
        }
        else {
            Write-Warning "No current version running"
            return $true
        }
    }
    catch {
        Write-Error-Message "Failed to stop current version: $_"
        return $false
    }
}

function Restore-PreviousVersion {
    param(
        [string]$PreviousContainer,
        [string]$ServiceName
    )

    Write-Info "Restoring previous version..."

    if ($WhatIf) {
        Write-Info "[DRY-RUN] Would restore $PreviousContainer as $ServiceName"
        return $true
    }

    try {
        # If previous container is stopped, restart it
        $containerState = docker inspect $PreviousContainer --format '{{.State.Status}}' 2>$null

        if ($containerState -eq "exited") {
            Write-Info "Starting previous container: $PreviousContainer"
            docker start $PreviousContainer | Out-Null

            # Rename to active service name
            Write-Info "Renaming to active service name..."
            docker rename $PreviousContainer "${ServiceName}-restored"

            # Recreate with correct configuration
            $previousImage = docker inspect "${ServiceName}-restored" --format '{{.Config.Image}}'

            docker stop "${ServiceName}-restored" | Out-Null
            docker rm "${ServiceName}-restored" | Out-Null

            docker run -d `
                --name $ServiceName `
                --network kidcomic_backend `
                -p "8000:8000" `
                -e SERVICE_ENV=$Environment `
                -e LOG_LEVEL=INFO `
                $previousImage

            Write-Success "Previous version restored: $ServiceName"
            return $true
        }
        elseif ($containerState -eq "running") {
            Write-Warning "Previous container already running: $PreviousContainer"

            # Just rename it
            docker rename $PreviousContainer $ServiceName

            Write-Success "Previous version activated: $ServiceName"
            return $true
        }
        else {
            Write-Error-Message "Previous container in unexpected state: $containerState"
            return $false
        }
    }
    catch {
        Write-Error-Message "Failed to restore previous version: $_"
        return $false
    }
}

function Test-RestoredHealth {
    param([string]$ServiceName)

    Write-Info "Verifying restored version health..."

    if ($WhatIf) {
        Write-Info "[DRY-RUN] Would verify health of restored $ServiceName"
        return $true
    }

    $healthUrl = "http://localhost:8000/health"
    $elapsedTime = 0

    while ($elapsedTime -lt $HealthCheckTimeout) {
        try {
            $response = Invoke-RestMethod -Uri $healthUrl -TimeoutSec 5
            if ($response.status -eq "healthy") {
                Write-Success "Restored version is healthy"
                return $true
            }
        }
        catch {
            Write-Info "Waiting for service to become healthy... ($elapsedTime / $HealthCheckTimeout seconds)"
            Start-Sleep -Seconds 5
            $elapsedTime += 5
        }
    }

    Write-Error-Message "Restored version failed health check"
    return $false
}

function Write-RollbackLog {
    param(
        [string]$ServiceName,
        [string]$PreviousVersion,
        [bool]$Success
    )

    Write-Info "Logging rollback event..."

    if ($WhatIf) {
        Write-Info "[DRY-RUN] Would log rollback event"
        return
    }

    # Use log-deployment script to record rollback
    $logScript = "$PSScriptRoot/log-deployment.ps1"

    if (Test-Path $logScript) {
        & $logScript `
            -ServiceName $ServiceName `
            -Version $PreviousVersion `
            -Status $(if ($Success) { "success" } else { "failed" }) `
            -Environment $Environment `
            -IsRollback
    }
    else {
        Write-Warning "Deployment logging script not found: $logScript"
    }
}

# Main rollback flow
$startTime = Get-Date

Write-Error-Message "=========================================="
Write-Error-Message "AUTOMATED ROLLBACK INITIATED"
Write-Error-Message "=========================================="
Write-Info "Service: $ServiceName"
Write-Info "Environment: $Environment"
Write-Info "Time: $startTime"
Write-Error-Message "=========================================="
Write-Host ""

try {
    # Step 1: Identify previous stable version
    $previousVersion = Get-PreviousVersion -ServiceName $ServiceName
    if (-not $previousVersion) {
        Write-Error-Message "Cannot rollback: No previous version found"
        exit 1
    }

    # Step 2: Stop current failing version
    if (-not (Stop-CurrentVersion -ServiceName $ServiceName)) {
        Write-Error-Message "Failed to stop current version"
        exit 1
    }

    # Step 3: Restore previous version
    if (-not (Restore-PreviousVersion -PreviousContainer $previousVersion -ServiceName $ServiceName)) {
        Write-Error-Message "Failed to restore previous version"
        exit 1
    }

    # Step 4: Verify health
    if (-not (Test-RestoredHealth -ServiceName $ServiceName)) {
        Write-Error-Message "Restored version is not healthy"
        exit 1
    }

    # Step 5: Log successful rollback
    Write-RollbackLog -ServiceName $ServiceName -PreviousVersion $previousVersion -Success $true

    # Calculate elapsed time
    $elapsedTime = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)

    Write-Success ""
    Write-Success "=========================================="
    Write-Success "ROLLBACK COMPLETE"
    Write-Success "=========================================="
    Write-Success "Service: $ServiceName"
    Write-Success "Restored Version: $previousVersion"
    Write-Success "Time Elapsed: ${elapsedTime}s"
    Write-Success "Status: Service Healthy"
    Write-Success "=========================================="

    # Verify we met the 2-minute target
    if ($elapsedTime -gt $RollbackTimeout) {
        Write-Warning "Rollback exceeded target time (${RollbackTimeout}s)"
    }
    else {
        Write-Success "Rollback completed within target time"
    }

    exit 0
}
catch {
    Write-Error-Message "Rollback failed: $_"

    # Log failed rollback
    Write-RollbackLog -ServiceName $ServiceName -PreviousVersion $previousVersion -Success $false

    exit 1
}
