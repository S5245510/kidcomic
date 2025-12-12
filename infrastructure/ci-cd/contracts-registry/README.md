# API Contract Registry

**Purpose**: Store versioned OpenAPI schemas for all services to enable automated breaking change detection.

Per FR-027: API contract registry for version compatibility management.

---

## Directory Structure

```
contracts-registry/
├── story-service/
│   ├── v1.0.0/
│   │   └── openapi.json
│   ├── v1.1.0/
│   │   └── openapi.json
│   └── v2.0.0/
│       └── openapi.json
├── payment-service/
│   └── v1.0.0/
│       └── openapi.json
└── README.md
```

---

## Usage

### 1. Store Contract on Release

When deploying a new service version, store its OpenAPI schema:

```powershell
# Generate OpenAPI schema from service
cd services/story-service
python -c "
from src.main import app
import json
schema = app.openapi()
with open('openapi.json', 'w') as f:
    json.dump(schema, f, indent=2)
"

# Copy to contract registry
$version = "v1.0.0"
$targetDir = "../../infrastructure/ci-cd/contracts-registry/story-service/$version"
New-Item -ItemType Directory -Force -Path $targetDir
Copy-Item openapi.json "$targetDir/openapi.json"
```

### 2. Detect Breaking Changes

Before deploying a new version, compare schemas:

```powershell
cd infrastructure/ci-cd/scripts

.\detect-breaking-changes.ps1 `
    -OldSchemaPath "../contracts-registry/story-service/v1.0.0/openapi.json" `
    -NewSchemaPath "../contracts-registry/story-service/v2.0.0/openapi.json" `
    -ServiceName "story-service" `
    -RequireMajorBump
```

### 3. Validate Version Bump

Ensure version bump matches breaking changes:

```powershell
# If breaking changes detected, require MAJOR version bump
.\validate-semver.ps1 -Version "v2.0.0" -ServiceName "story-service" -CheckIncrement
```

---

## Contract Comparison

### Breaking Changes (Require MAJOR version bump)

- ❌ Removed endpoint
- ❌ Removed required field
- ❌ Changed field type
- ❌ Removed response code
- ❌ Renamed field

### Non-Breaking Changes (Allow MINOR/PATCH version bump)

- ✅ Added new endpoint
- ✅ Added optional field
- ✅ Made required field optional
- ✅ Added response code
- ✅ Added enum value

---

## Automated CI/CD Integration

The contract registry is integrated into the CI/CD pipeline:

```yaml
# .github/workflows/story-service-ci.yml

- name: Generate OpenAPI Schema
  run: |
    python -c "
    from src.main import app
    import json
    schema = app.openapi()
    with open('openapi-current.json', 'w') as f:
        json.dump(schema, f, indent=2)
    "

- name: Detect Breaking Changes
  run: |
    $latestVersion = git describe --tags --abbrev=0
    $oldSchema = "infrastructure/ci-cd/contracts-registry/story-service/$latestVersion/openapi.json"

    if (Test-Path $oldSchema) {
        .\infrastructure\ci-cd\scripts\detect-breaking-changes.ps1 `
            -OldSchemaPath $oldSchema `
            -NewSchemaPath "openapi-current.json" `
            -RequireMajorBump
    }

- name: Validate Version Bump
  run: |
    $newVersion = $env:GITHUB_REF -replace 'refs/tags/', ''
    .\infrastructure\ci-cd\scripts\validate-semver.ps1 `
        -Version $newVersion `
        -ServiceName "story-service" `
        -CheckIncrement
```

---

## Version Compatibility Matrix

| Version | Compatible With | Breaking Changes |
|---------|----------------|------------------|
| v1.0.0 | - | Initial release |
| v1.1.0 | v1.0.0 | None (added features) |
| v2.0.0 | - | Changed 'content' to 'body', changed response format |
| v2.1.0 | v2.0.0 | None (added endpoints) |

---

## Best Practices

1. **Store Every Release**: Always save the OpenAPI schema for each version deployed to production

2. **Compare Before Deploy**: Run breaking change detection before every deployment

3. **Document Breaking Changes**: Add notes in this README when introducing breaking changes

4. **Maintain v1 Compatibility**: Keep v1 endpoints active for at least 6 months after v2 release

5. **Version in URL**: Use path-based versioning (/v1/stories, /v2/stories) for clarity

6. **Deprecation Warnings**: Add deprecation warnings to v1 responses when v2 is available:
   ```json
   {
     "deprecated": true,
     "deprecation_message": "This endpoint is deprecated. Please use /v2/stories",
     "sunset_date": "2025-12-31"
   }
   ```

---

## Contract Testing

Contracts are validated with automated tests:

- `tests/contract/test_api_versioning.py` - Contract compliance tests
- `tests/integration/test_contract_validation.py` - Breaking change detection tests

Run tests:
```bash
pytest tests/contract/ -v
pytest tests/integration/test_contract_validation.py -v
```

---

## Troubleshooting

### Schema Generation Fails

```powershell
# Ensure FastAPI app is importable
cd services/story-service
python -c "from src.main import app; print(app.openapi())"
```

### Breaking Change Detection Fails

```powershell
# Verify schemas are valid JSON
Get-Content openapi.json | ConvertFrom-Json

# Run detection in dry-run mode
.\detect-breaking-changes.ps1 -OldSchemaPath "old.json" -NewSchemaPath "new.json" -WhatIf
```

---

## References

- **FR-025**: Automated breaking change detection
- **FR-027**: API contract registry
- **OpenAPI Specification**: https://swagger.io/specification/
- **Semantic Versioning**: https://semver.org/
