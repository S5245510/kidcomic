<#
.SYNOPSIS
    Semantic Versioning Validation Script (T100)

.DESCRIPTION
    Validates semantic versioning for service releases:
    - Parses version from git tags
    - Validates MAJOR.MINOR.PATCH format
    - Ensures version increments correctly
    - Checks version against previous releases

    Per FR-024: Semantic versioning enforcement

.PARAMETER Version
    Version string to validate (e.g., "v1.2.3" or "1.2.3")

.PARAMETER ServiceName
    Name of the service (default: extracted from current directory)

.PARAMETER CheckIncrement
    Verify version is properly incremented from previous version

.EXAMPLE
    .\validate-semver.ps1 -Version "v1.2.3"

.EXAMPLE
    .\validate-semver.ps1 -Version "2.0.0" -ServiceName "story-service" -CheckIncrement

.NOTES
    Semantic Versioning (SemVer) format: MAJOR.MINOR.PATCH
    - MAJOR: Breaking changes
    - MINOR: New features (backward compatible)
    - PATCH: Bug fixes (backward compatible)
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$Version,

    [Parameter()]
    [string]$ServiceName,

    [Parameter()]
    [switch]$CheckIncrement
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Color output
function Write-Info { param([string]$Message); Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message); Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message); Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error-Message { param([string]$Message); Write-Host "[ERROR] $Message" -ForegroundColor Red }

function Test-SemanticVersion {
    param([string]$VersionString)

    # Remove 'v' prefix if present
    $versionClean = $VersionString -replace '^v', ''

    # Semantic version regex: MAJOR.MINOR.PATCH with optional pre-release and build metadata
    # Examples: 1.0.0, 1.0.0-alpha, 1.0.0-alpha.1, 1.0.0+build123
    $semverPattern = '^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$'

    if ($versionClean -match $semverPattern) {
        return @{
            Valid = $true
            Major = [int]$matches[1]
            Minor = [int]$matches[2]
            Patch = [int]$matches[3]
            PreRelease = $matches[4]
            BuildMetadata = $matches[5]
            Original = $VersionString
            Clean = $versionClean
        }
    }
    else {
        return @{
            Valid = $false
            Original = $VersionString
        }
    }
}

function Get-PreviousVersion {
    param([string]$ServiceName)

    try {
        # Get all git tags for this service
        $tagPattern = if ($ServiceName) { "${ServiceName}-v*" } else { "v*" }

        $tags = git tag --list $tagPattern --sort=-version:refname 2>$null

        if ($tags) {
            # Get most recent tag
            $latestTag = $tags | Select-Object -First 1

            # Extract version from tag
            if ($ServiceName) {
                $versionStr = $latestTag -replace "^${ServiceName}-", ''
            }
            else {
                $versionStr = $latestTag
            }

            return $versionStr
        }
        else {
            return $null
        }
    }
    catch {
        return $null
    }
}

function Test-VersionIncrement {
    param(
        [hashtable]$OldVersion,
        [hashtable]$NewVersion
    )

    $isValid = $false
    $reason = ""

    # Check MAJOR increment
    if ($NewVersion.Major -gt $OldVersion.Major) {
        # MAJOR version bumped - MINOR and PATCH should reset to 0
        if ($NewVersion.Minor -eq 0 -and $NewVersion.Patch -eq 0) {
            $isValid = $true
            $reason = "MAJOR version increment (breaking changes)"
        }
        else {
            $isValid = $false
            $reason = "MAJOR version bumped but MINOR/PATCH not reset to 0"
        }
    }
    # Check MINOR increment
    elseif ($NewVersion.Major -eq $OldVersion.Major -and $NewVersion.Minor -gt $OldVersion.Minor) {
        # MINOR version bumped - PATCH should reset to 0
        if ($NewVersion.Patch -eq 0) {
            $isValid = $true
            $reason = "MINOR version increment (new features)"
        }
        else {
            $isValid = $false
            $reason = "MINOR version bumped but PATCH not reset to 0"
        }
    }
    # Check PATCH increment
    elseif ($NewVersion.Major -eq $OldVersion.Major -and
            $NewVersion.Minor -eq $OldVersion.Minor -and
            $NewVersion.Patch -gt $OldVersion.Patch) {
        $isValid = $true
        $reason = "PATCH version increment (bug fixes)"
    }
    # Same version
    elseif ($NewVersion.Major -eq $OldVersion.Major -and
            $NewVersion.Minor -eq $OldVersion.Minor -and
            $NewVersion.Patch -eq $OldVersion.Patch) {
        $isValid = $false
        $reason = "Version not incremented (same as previous)"
    }
    # Version decreased
    else {
        $isValid = $false
        $reason = "Version decreased (not allowed)"
    }

    return @{
        Valid = $isValid
        Reason = $reason
        ChangeType = if ($isValid) {
            if ($NewVersion.Major -gt $OldVersion.Major) { "MAJOR" }
            elseif ($NewVersion.Minor -gt $OldVersion.Minor) { "MINOR" }
            else { "PATCH" }
        } else { $null }
    }
}

# Main validation
Write-Info "=========================================="
Write-Info "Semantic Version Validation"
Write-Info "=========================================="
Write-Info "Version: $Version"
if ($ServiceName) {
    Write-Info "Service: $ServiceName"
}
Write-Info "=========================================="
Write-Host ""

# Parse version
$parsedVersion = Test-SemanticVersion -VersionString $Version

if (-not $parsedVersion.Valid) {
    Write-Error-Message "Invalid semantic version format"
    Write-Error-Message ""
    Write-Error-Message "Expected format: MAJOR.MINOR.PATCH"
    Write-Error-Message "Examples:"
    Write-Error-Message "  - 1.0.0"
    Write-Error-Message "  - 2.1.3"
    Write-Error-Message "  - 1.0.0-alpha"
    Write-Error-Message "  - 1.0.0-beta.1"
    Write-Error-Message "  - 1.0.0+build123"
    Write-Error-Message ""
    Write-Error-Message "Your version: $Version"
    exit 1
}

Write-Success "Version format is valid"
Write-Info "  Major: $($parsedVersion.Major)"
Write-Info "  Minor: $($parsedVersion.Minor)"
Write-Info "  Patch: $($parsedVersion.Patch)"

if ($parsedVersion.PreRelease) {
    Write-Info "  Pre-release: $($parsedVersion.PreRelease)"
}

if ($parsedVersion.BuildMetadata) {
    Write-Info "  Build metadata: $($parsedVersion.BuildMetadata)"
}

Write-Host ""

# Check version increment if requested
if ($CheckIncrement) {
    Write-Info "Checking version increment..."

    $previousVersionStr = Get-PreviousVersion -ServiceName $ServiceName

    if ($previousVersionStr) {
        Write-Info "Previous version: $previousVersionStr"

        $previousVersion = Test-SemanticVersion -VersionString $previousVersionStr

        if ($previousVersion.Valid) {
            $incrementCheck = Test-VersionIncrement -OldVersion $previousVersion -NewVersion $parsedVersion

            if ($incrementCheck.Valid) {
                Write-Success "Version increment is valid"
                Write-Success "  Change type: $($incrementCheck.ChangeType)"
                Write-Success "  Reason: $($incrementCheck.Reason)"
            }
            else {
                Write-Error-Message "Version increment is invalid"
                Write-Error-Message "  Reason: $($incrementCheck.Reason)"
                Write-Error-Message ""
                Write-Error-Message "Previous: $($previousVersion.Clean)"
                Write-Error-Message "New:      $($parsedVersion.Clean)"
                exit 1
            }
        }
        else {
            Write-Warning "Previous version format invalid: $previousVersionStr"
            Write-Warning "Skipping increment check"
        }
    }
    else {
        Write-Info "No previous version found (first release)"
        Write-Success "Version increment check skipped"
    }

    Write-Host ""
}

Write-Success "=========================================="
Write-Success "Semantic Version Validation PASSED"
Write-Success "=========================================="
Write-Success "Version: $($parsedVersion.Clean)"
if ($CheckIncrement -and $previousVersionStr) {
    Write-Success "Previous: $($previousVersion.Clean)"
    Write-Success "Change: $($incrementCheck.ChangeType)"
}
Write-Success "=========================================="

exit 0
