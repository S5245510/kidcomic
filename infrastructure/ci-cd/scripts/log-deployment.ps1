<#
.SYNOPSIS
    Deployment History Logger (T088)

.DESCRIPTION
    Logs deployment events to deployment-history.json:
    - Service name
    - Version deployed
    - Commit SHA
    - Timestamp
    - Status (success/failed)
    - Whether this was a rollback
    - Environment (staging/production)
    - Deployed by (user/automation)

    Per FR-022: Track deployment history for audit and rollback

.PARAMETER ServiceName
    Name of the service deployed

.PARAMETER Version
    Version or commit SHA deployed

.PARAMETER Status
    Deployment status (success, failed)

.PARAMETER Environment
    Target environment

.PARAMETER IsRollback
    Whether this was a rollback deployment

.PARAMETER DeployedBy
    Who/what triggered the deployment

.EXAMPLE
    .\log-deployment.ps1 -ServiceName "story-service" -Version "abc123" -Status "success" -Environment "staging"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceName,

    [Parameter(Mandatory=$true)]
    [string]$Version,

    [Parameter(Mandatory=$true)]
    [ValidateSet("success", "failed", "in_progress")]
    [string]$Status,

    [Parameter(Mandatory=$true)]
    [ValidateSet("staging", "production", "development")]
    [string]$Environment,

    [Parameter()]
    [switch]$IsRollback,

    [Parameter()]
    [string]$DeployedBy = "automation"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Configuration
$HistoryFile = "$PSScriptRoot/../deployment-history.json"
$MaxHistoryEntries = 100  # Keep last 100 deployments

# Color output
function Write-Info { param([string]$Message); Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message); Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Error-Message { param([string]$Message); Write-Host "[ERROR] $Message" -ForegroundColor Red }

function Get-DeploymentHistory {
    if (Test-Path $HistoryFile) {
        try {
            $content = Get-Content $HistoryFile -Raw | ConvertFrom-Json
            return @($content)  # Ensure array
        }
        catch {
            Write-Error-Message "Failed to parse deployment history: $_"
            return @()
        }
    }
    else {
        Write-Info "Creating new deployment history file"
        return @()
    }
}

function Add-DeploymentEntry {
    param(
        [array]$History,
        [hashtable]$Entry
    )

    # Add new entry at the beginning (most recent first)
    $updatedHistory = @($Entry) + $History

    # Trim to max entries
    if ($updatedHistory.Count -gt $MaxHistoryEntries) {
        $updatedHistory = $updatedHistory[0..($MaxHistoryEntries - 1)]
    }

    return $updatedHistory
}

function Save-DeploymentHistory {
    param([array]$History)

    try {
        # Ensure directory exists
        $historyDir = Split-Path $HistoryFile -Parent
        if (-not (Test-Path $historyDir)) {
            New-Item -Path $historyDir -ItemType Directory -Force | Out-Null
        }

        # Save as pretty-printed JSON
        $History | ConvertTo-Json -Depth 10 | Out-File $HistoryFile -Encoding UTF8

        Write-Success "Deployment logged to $HistoryFile"
    }
    catch {
        Write-Error-Message "Failed to save deployment history: $_"
        throw
    }
}

# Main logging
Write-Info "=========================================="
Write-Info "Logging Deployment Event"
Write-Info "=========================================="

try {
    # Get current history
    $history = Get-DeploymentHistory

    # Create new entry
    $entry = [ordered]@{
        id = [guid]::NewGuid().ToString()
        service = $ServiceName
        version = $Version
        timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        status = $Status
        environment = $Environment
        rollback = $IsRollback.IsPresent
        deployed_by = $DeployedBy
        commit_sha = $Version
    }

    # Add Git information if available
    try {
        $gitBranch = git rev-parse --abbrev-ref HEAD 2>$null
        $gitCommit = git rev-parse --short HEAD 2>$null

        if ($gitBranch) { $entry.git_branch = $gitBranch }
        if ($gitCommit) { $entry.git_commit = $gitCommit }
    }
    catch {
        # Git not available or not in repo - skip
    }

    # Display entry
    Write-Info "Service:     $ServiceName"
    Write-Info "Version:     $Version"
    Write-Info "Status:      $Status"
    Write-Info "Environment: $Environment"
    Write-Info "Rollback:    $($IsRollback.IsPresent)"
    Write-Info "Deployed By: $DeployedBy"
    Write-Info "Timestamp:   $($entry.timestamp)"

    # Add entry and save
    $updatedHistory = Add-DeploymentEntry -History $history -Entry $entry
    Save-DeploymentHistory -History $updatedHistory

    Write-Success ""
    Write-Success "Deployment event logged successfully"
    Write-Success "Total history entries: $($updatedHistory.Count)"
    Write-Success "=========================================="

    exit 0
}
catch {
    Write-Error-Message "Failed to log deployment: $_"
    exit 1
}
