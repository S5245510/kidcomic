<#
.SYNOPSIS
    Breaking Change Detection Script (T101)

.DESCRIPTION
    Compares OpenAPI schemas to detect breaking changes:
    - Removed endpoints
    - Removed required fields
    - Changed field types
    - Removed response codes
    - Added required request fields

    Per FR-025: Automated breaking change detection
    Per FR-027: API contract registry integration

.PARAMETER OldSchemaPath
    Path to old version OpenAPI schema

.PARAMETER NewSchemaPath
    Path to new version OpenAPI schema

.PARAMETER ServiceName
    Name of the service being checked

.PARAMETER RequireMajorBump
    Fail if breaking changes detected without MAJOR version bump

.EXAMPLE
    .\detect-breaking-changes.ps1 -OldSchemaPath "./v1.0.0/openapi.json" -NewSchemaPath "./v2.0.0/openapi.json"

.EXAMPLE
    .\detect-breaking-changes.ps1 -OldSchemaPath "./v1.0.0/openapi.json" -NewSchemaPath "./v1.1.0/openapi.json" -RequireMajorBump

.NOTES
    Breaking changes require MAJOR version bump (1.x.x → 2.0.0)
    Non-breaking changes can use MINOR (1.0.0 → 1.1.0) or PATCH (1.0.0 → 1.0.1)
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$OldSchemaPath,

    [Parameter(Mandatory=$true)]
    [string]$NewSchemaPath,

    [Parameter()]
    [string]$ServiceName,

    [Parameter()]
    [switch]$RequireMajorBump,

    [Parameter()]
    [switch]$WhatIf
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Color output
function Write-Info { param([string]$Message); Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-Success { param([string]$Message); Write-Host "[SUCCESS] $Message" -ForegroundColor Green }
function Write-Warning { param([string]$Message); Write-Host "[WARNING] $Message" -ForegroundColor Yellow }
function Write-Error-Message { param([string]$Message); Write-Host "[ERROR] $Message" -ForegroundColor Red }
function Write-Breaking { param([string]$Message); Write-Host "[BREAKING] $Message" -ForegroundColor Red }

function Get-OpenAPISchema {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Schema file not found: $Path"
    }

    try {
        $content = Get-Content $Path -Raw | ConvertFrom-Json
        return $content
    }
    catch {
        throw "Failed to parse OpenAPI schema: $_"
    }
}

function Get-SchemaPaths {
    param([object]$Schema)

    if ($Schema.paths) {
        return $Schema.paths.PSObject.Properties.Name
    }
    return @()
}

function Get-SchemaDefinitions {
    param([object]$Schema)

    # OpenAPI 3.x uses 'components.schemas', Swagger 2.0 uses 'definitions'
    if ($Schema.components -and $Schema.components.schemas) {
        return $Schema.components.schemas
    }
    elseif ($Schema.definitions) {
        return $Schema.definitions
    }
    return @{}
}

function Compare-Paths {
    param(
        [array]$OldPaths,
        [array]$NewPaths
    )

    $breakingChanges = @()

    # Check for removed paths
    foreach ($oldPath in $OldPaths) {
        if ($oldPath -notin $NewPaths) {
            $breakingChanges += "Removed endpoint: $oldPath"
        }
    }

    return $breakingChanges
}

function Compare-SchemaDefinitions {
    param(
        [object]$OldSchemas,
        [object]$NewSchemas
    )

    $breakingChanges = @()

    if (-not $OldSchemas) { return $breakingChanges }

    # Iterate through old schemas
    foreach ($schemaName in $OldSchemas.PSObject.Properties.Name) {
        $oldDef = $OldSchemas.$schemaName

        # Check if schema was removed
        if (-not $NewSchemas -or -not $NewSchemas.PSObject.Properties.Name.Contains($schemaName)) {
            $breakingChanges += "Removed schema: $schemaName"
            continue
        }

        $newDef = $NewSchemas.$schemaName

        # Check for removed required fields
        $oldRequired = if ($oldDef.required) { $oldDef.required } else { @() }
        $newRequired = if ($newDef.required) { $newDef.required } else { @() }

        foreach ($reqField in $oldRequired) {
            if ($reqField -notin $newRequired) {
                $breakingChanges += "Schema '$schemaName': Removed required field '$reqField'"
            }
        }

        # Check for removed properties
        if ($oldDef.properties) {
            $oldProps = $oldDef.properties.PSObject.Properties.Name

            foreach ($propName in $oldProps) {
                if (-not $newDef.properties -or -not $newDef.properties.PSObject.Properties.Name.Contains($propName)) {
                    $breakingChanges += "Schema '$schemaName': Removed property '$propName'"
                }
                else {
                    # Check for type changes
                    $oldType = $oldDef.properties.$propName.type
                    $newType = $newDef.properties.$propName.type

                    if ($oldType -and $newType -and $oldType -ne $newType) {
                        $breakingChanges += "Schema '$schemaName'.'$propName': Type changed from '$oldType' to '$newType'"
                    }
                }
            }
        }

        # Check for added required fields (breaking for requests)
        foreach ($reqField in $newRequired) {
            if ($reqField -notin $oldRequired) {
                # This is potentially breaking if it's a request body
                # For now, just warn
                Write-Warning "Schema '$schemaName': Added required field '$reqField' (may be breaking for requests)"
            }
        }
    }

    return $breakingChanges
}

function Compare-PathMethods {
    param(
        [object]$OldSchema,
        [object]$NewSchema,
        [array]$CommonPaths
    )

    $breakingChanges = @()

    foreach ($path in $CommonPaths) {
        $oldPathDef = $OldSchema.paths.$path
        $newPathDef = $NewSchema.paths.$path

        # Check HTTP methods
        $oldMethods = $oldPathDef.PSObject.Properties.Name
        $newMethods = $newPathDef.PSObject.Properties.Name

        foreach ($method in $oldMethods) {
            # Skip non-HTTP method properties
            if ($method -notin @('get', 'post', 'put', 'patch', 'delete', 'options', 'head')) {
                continue
            }

            # Check if method was removed
            if ($method -notin $newMethods) {
                $breakingChanges += "Removed method: $method $path"
                continue
            }

            # Check response codes
            $oldResponses = if ($oldPathDef.$method.responses) {
                $oldPathDef.$method.responses.PSObject.Properties.Name
            } else { @() }

            $newResponses = if ($newPathDef.$method.responses) {
                $newPathDef.$method.responses.PSObject.Properties.Name
            } else { @() }

            foreach ($responseCode in $oldResponses) {
                if ($responseCode -notin $newResponses) {
                    $breakingChanges += "Removed response code $responseCode from $method $path"
                }
            }
        }
    }

    return $breakingChanges
}

# Main execution
Write-Info "=========================================="
Write-Info "Breaking Change Detection"
Write-Info "=========================================="
Write-Info "Old schema: $OldSchemaPath"
Write-Info "New schema: $NewSchemaPath"
if ($ServiceName) {
    Write-Info "Service: $ServiceName"
}
Write-Info "=========================================="
Write-Host ""

if ($WhatIf) {
    Write-Info "[DRY-RUN MODE]"
    Write-Host ""
}

# Load schemas
try {
    Write-Info "Loading OpenAPI schemas..."
    $oldSchema = Get-OpenAPISchema -Path $OldSchemaPath
    $newSchema = Get-OpenAPISchema -Path $NewSchemaPath

    Write-Success "Schemas loaded successfully"
    Write-Host ""
}
catch {
    Write-Error-Message "Failed to load schemas: $_"
    exit 1
}

# Collect all breaking changes
$allBreakingChanges = @()

# Compare paths (endpoints)
Write-Info "Comparing API endpoints..."
$oldPaths = Get-SchemaPaths -Schema $oldSchema
$newPaths = Get-SchemaPaths -Schema $newSchema

$pathChanges = Compare-Paths -OldPaths $oldPaths -NewPaths $newPaths
$allBreakingChanges += $pathChanges

if ($pathChanges.Count -gt 0) {
    Write-Host ""
    foreach ($change in $pathChanges) {
        Write-Breaking $change
    }
}
else {
    Write-Success "No endpoint removals detected"
}
Write-Host ""

# Compare methods on common paths
Write-Info "Comparing HTTP methods..."
$commonPaths = $oldPaths | Where-Object { $_ -in $newPaths }
$methodChanges = Compare-PathMethods -OldSchema $oldSchema -NewSchema $newSchema -CommonPaths $commonPaths
$allBreakingChanges += $methodChanges

if ($methodChanges.Count -gt 0) {
    Write-Host ""
    foreach ($change in $methodChanges) {
        Write-Breaking $change
    }
}
else {
    Write-Success "No method removals detected"
}
Write-Host ""

# Compare schema definitions
Write-Info "Comparing data schemas..."
$oldSchemas = Get-SchemaDefinitions -Schema $oldSchema
$newSchemas = Get-SchemaDefinitions -Schema $newSchema

$schemaChanges = Compare-SchemaDefinitions -OldSchemas $oldSchemas -NewSchemas $newSchemas
$allBreakingChanges += $schemaChanges

if ($schemaChanges.Count -gt 0) {
    Write-Host ""
    foreach ($change in $schemaChanges) {
        Write-Breaking $change
    }
}
else {
    Write-Success "No schema breaking changes detected"
}
Write-Host ""

# Summary
Write-Info "=========================================="
Write-Info "Detection Complete"
Write-Info "=========================================="

if ($allBreakingChanges.Count -eq 0) {
    Write-Success "No breaking changes detected"
    Write-Success ""
    Write-Success "Safe to deploy with MINOR or PATCH version bump"
    Write-Success "=========================================="
    exit 0
}
else {
    Write-Warning ""
    Write-Warning "Found $($allBreakingChanges.Count) breaking change(s):"
    Write-Warning ""

    for ($i = 0; $i -lt $allBreakingChanges.Count; $i++) {
        Write-Warning "  $($i + 1). $($allBreakingChanges[$i])"
    }

    Write-Warning ""
    Write-Warning "=========================================="
    Write-Error-Message ""
    Write-Error-Message "BREAKING CHANGES DETECTED"
    Write-Error-Message ""

    if ($RequireMajorBump) {
        Write-Error-Message "MAJOR version bump is REQUIRED"
        Write-Error-Message "Example: v1.0.0 → v2.0.0"
        Write-Error-Message ""
        Write-Error-Message "Deployment BLOCKED until version is bumped"
        Write-Error-Message "=========================================="
        exit 1
    }
    else {
        Write-Error-Message "MAJOR version bump is RECOMMENDED"
        Write-Error-Message "Example: v1.0.0 → v2.0.0"
        Write-Error-Message ""
        Write-Error-Message "To enforce version bump, use -RequireMajorBump flag"
        Write-Error-Message "=========================================="
        exit 0  # Warning only, don't block
    }
}
