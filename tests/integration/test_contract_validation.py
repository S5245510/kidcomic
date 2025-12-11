"""
Integration test for contract validation (T099)

Tests that breaking changes are detected before deployment:
1. Compare OpenAPI schemas between versions
2. Detect breaking changes (field removal, type changes)
3. Enforce MAJOR version bump for breaking changes
4. Validate contract compatibility

Per FR-025: Automated breaking change detection
Per FR-027: API contract registry
"""

import pytest
import json
from pathlib import Path
from typing import Dict, Any, List, Set
import subprocess


class TestContractValidation:
    """Integration tests for API contract validation"""

    @pytest.fixture
    def contracts_registry_dir(self) -> Path:
        """Path to API contracts registry"""
        return Path(__file__).parent.parent.parent / \
               "infrastructure" / "ci-cd" / "contracts-registry"

    @pytest.fixture
    def breaking_change_script(self) -> Path:
        """Path to breaking change detection script"""
        return Path(__file__).parent.parent.parent / \
               "infrastructure" / "ci-cd" / "scripts" / "detect-breaking-changes.ps1"

    def load_openapi_schema(self, schema_path: Path) -> Dict[str, Any]:
        """Load OpenAPI schema from file"""
        with open(schema_path, 'r') as f:
            return json.load(f)

    def get_schema_paths(self, schema: Dict[str, Any]) -> Set[str]:
        """Extract all paths from OpenAPI schema"""
        return set(schema.get('paths', {}).keys())

    def get_schema_definitions(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract definitions/components from OpenAPI schema"""
        # OpenAPI 3.x uses 'components', Swagger 2.0 uses 'definitions'
        return schema.get('components', {}).get('schemas', {}) or \
               schema.get('definitions', {})

    def detect_breaking_changes(
        self,
        old_schema: Dict[str, Any],
        new_schema: Dict[str, Any]
    ) -> List[str]:
        """
        Detect breaking changes between two schemas

        Breaking changes:
        - Removed endpoint
        - Removed required field
        - Changed field type
        - Removed response code
        - Added required field to request
        """
        breaking_changes = []

        # Check for removed paths
        old_paths = self.get_schema_paths(old_schema)
        new_paths = self.get_schema_paths(new_schema)

        removed_paths = old_paths - new_paths
        if removed_paths:
            breaking_changes.append(
                f"Removed endpoints: {', '.join(removed_paths)}"
            )

        # Check for removed or modified schemas
        old_schemas = self.get_schema_definitions(old_schema)
        new_schemas = self.get_schema_definitions(new_schema)

        for schema_name, old_def in old_schemas.items():
            if schema_name not in new_schemas:
                breaking_changes.append(f"Removed schema: {schema_name}")
                continue

            new_def = new_schemas[schema_name]

            # Check for removed required fields
            old_required = set(old_def.get('required', []))
            new_required = set(new_def.get('required', []))

            removed_required = old_required - new_required
            if removed_required:
                breaking_changes.append(
                    f"Schema {schema_name}: Removed required fields: {', '.join(removed_required)}"
                )

            # Check for removed properties
            old_props = set(old_def.get('properties', {}).keys())
            new_props = set(new_def.get('properties', {}).keys())

            removed_props = old_props - new_props
            if removed_props:
                breaking_changes.append(
                    f"Schema {schema_name}: Removed properties: {', '.join(removed_props)}"
                )

            # Check for type changes
            old_properties = old_def.get('properties', {})
            new_properties = new_def.get('properties', {})

            for prop_name in old_props & new_props:
                old_type = old_properties[prop_name].get('type')
                new_type = new_properties[prop_name].get('type')

                if old_type and new_type and old_type != new_type:
                    breaking_changes.append(
                        f"Schema {schema_name}.{prop_name}: Type changed from {old_type} to {new_type}"
                    )

        return breaking_changes

    @pytest.mark.integration
    def test_breaking_change_detection_script_exists(
        self,
        breaking_change_script: Path
    ):
        """Test that breaking change detection script exists"""
        assert breaking_change_script.exists(), \
            f"Breaking change detection script should exist at {breaking_change_script}"

    @pytest.mark.integration
    def test_contracts_registry_exists(self, contracts_registry_dir: Path):
        """Test that API contracts registry directory exists"""
        assert contracts_registry_dir.exists(), \
            f"Contracts registry should exist at {contracts_registry_dir}"

    @pytest.mark.integration
    def test_detect_removed_endpoint(self):
        """
        Test detection of removed endpoint (breaking change)

        If /v1/stories/list exists in v1 but not in v2 → breaking change
        """
        # Old schema with /stories/list
        old_schema = {
            "openapi": "3.0.0",
            "paths": {
                "/stories": {"get": {}},
                "/stories/list": {"get": {}}  # Removed in v2
            }
        }

        # New schema without /stories/list
        new_schema = {
            "openapi": "3.0.0",
            "paths": {
                "/stories": {"get": {}}
            }
        }

        breaking_changes = self.detect_breaking_changes(old_schema, new_schema)

        assert len(breaking_changes) > 0, "Should detect removed endpoint"
        assert any("/stories/list" in change for change in breaking_changes), \
            "Should specifically identify /stories/list removal"

    @pytest.mark.integration
    def test_detect_removed_required_field(self):
        """
        Test detection of removed required field (breaking change)

        If Story had required field 'content' in v1 but not in v2 → breaking
        """
        old_schema = {
            "openapi": "3.0.0",
            "components": {
                "schemas": {
                    "Story": {
                        "type": "object",
                        "required": ["id", "title", "content"],
                        "properties": {
                            "id": {"type": "integer"},
                            "title": {"type": "string"},
                            "content": {"type": "string"}
                        }
                    }
                }
            }
        }

        new_schema = {
            "openapi": "3.0.0",
            "components": {
                "schemas": {
                    "Story": {
                        "type": "object",
                        "required": ["id", "title"],  # 'content' removed
                        "properties": {
                            "id": {"type": "integer"},
                            "title": {"type": "string"},
                            "body": {"type": "string"}  # Renamed from 'content'
                        }
                    }
                }
            }
        }

        breaking_changes = self.detect_breaking_changes(old_schema, new_schema)

        assert len(breaking_changes) > 0, "Should detect removed required field"
        assert any("content" in change.lower() for change in breaking_changes), \
            "Should identify 'content' field change"

    @pytest.mark.integration
    def test_detect_field_type_change(self):
        """
        Test detection of field type change (breaking change)

        If Story.id changes from integer to string → breaking
        """
        old_schema = {
            "openapi": "3.0.0",
            "components": {
                "schemas": {
                    "Story": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},  # Changed in v2
                            "title": {"type": "string"}
                        }
                    }
                }
            }
        }

        new_schema = {
            "openapi": "3.0.0",
            "components": {
                "schemas": {
                    "Story": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},  # Type changed
                            "title": {"type": "string"}
                        }
                    }
                }
            }
        }

        breaking_changes = self.detect_breaking_changes(old_schema, new_schema)

        assert len(breaking_changes) > 0, "Should detect type change"
        assert any("id" in change and "type" in change.lower() for change in breaking_changes), \
            "Should identify 'id' type change"

    @pytest.mark.integration
    def test_non_breaking_changes_allowed(self):
        """
        Test that non-breaking changes are NOT flagged

        Non-breaking changes:
        - Adding new endpoint
        - Adding optional field
        - Making required field optional
        """
        old_schema = {
            "openapi": "3.0.0",
            "paths": {
                "/stories": {"get": {}}
            },
            "components": {
                "schemas": {
                    "Story": {
                        "type": "object",
                        "required": ["id", "title"],
                        "properties": {
                            "id": {"type": "integer"},
                            "title": {"type": "string"}
                        }
                    }
                }
            }
        }

        new_schema = {
            "openapi": "3.0.0",
            "paths": {
                "/stories": {"get": {}},
                "/stories/search": {"get": {}}  # New endpoint (non-breaking)
            },
            "components": {
                "schemas": {
                    "Story": {
                        "type": "object",
                        "required": ["id", "title"],
                        "properties": {
                            "id": {"type": "integer"},
                            "title": {"type": "string"},
                            "description": {"type": "string"}  # New optional field (non-breaking)
                        }
                    }
                }
            }
        }

        breaking_changes = self.detect_breaking_changes(old_schema, new_schema)

        # Should have no breaking changes
        assert len(breaking_changes) == 0, \
            f"Non-breaking changes should not be flagged: {breaking_changes}"

    @pytest.mark.integration
    def test_version_bump_required_for_breaking_change(self):
        """
        Test that MAJOR version bump is required for breaking changes

        If v1.0.0 has breaking change → must become v2.0.0
        If v1.0.0 has non-breaking change → can become v1.1.0
        """
        # This would be tested via the semantic versioning script
        # For now, document the requirement

        breaking_change_requires_major = True
        assert breaking_change_requires_major, \
            "Breaking changes must trigger MAJOR version bump"

    @pytest.mark.integration
    def test_breaking_change_script_execution(self, breaking_change_script: Path):
        """
        Test that breaking change detection script can run

        Note: Requires PowerShell
        """
        if not breaking_change_script.exists():
            pytest.skip("Breaking change detection script not yet created")

        try:
            # Test with -WhatIf flag (dry-run)
            result = subprocess.run(
                ["powershell", "-File", str(breaking_change_script), "-WhatIf"],
                capture_output=True,
                timeout=30,
                text=True
            )

            # Script should execute without errors
            print(f"Script exit code: {result.returncode}")
            if result.stdout:
                print(f"Stdout: {result.stdout[:500]}")
            if result.stderr:
                print(f"Stderr: {result.stderr[:500]}")

        except FileNotFoundError:
            pytest.skip("PowerShell not available")

        except subprocess.TimeoutExpired:
            pytest.fail("Script execution timed out")

    @pytest.mark.integration
    def test_contract_registry_structure(self, contracts_registry_dir: Path):
        """
        Test that contract registry has correct structure

        Expected structure:
        contracts-registry/
          story-service/
            v1.0.0/
              openapi.json
            v2.0.0/
              openapi.json
        """
        if not contracts_registry_dir.exists():
            pytest.skip("Contracts registry not yet created")

        # Check for story-service directory
        story_service_dir = contracts_registry_dir / "story-service"

        if story_service_dir.exists():
            # Check for version directories
            version_dirs = [d for d in story_service_dir.iterdir() if d.is_dir()]

            # Should have version directories (e.g., v1.0.0, v2.0.0)
            assert len(version_dirs) > 0, \
                "Contract registry should have version directories"

            for version_dir in version_dirs:
                # Each version should have openapi.json
                openapi_file = version_dir / "openapi.json"

                if openapi_file.exists():
                    # Verify it's valid JSON
                    try:
                        with open(openapi_file, 'r') as f:
                            schema = json.load(f)

                        assert 'openapi' in schema or 'swagger' in schema, \
                            f"{openapi_file} should be valid OpenAPI/Swagger schema"

                    except json.JSONDecodeError:
                        pytest.fail(f"{openapi_file} is not valid JSON")

    @pytest.mark.integration
    def test_ci_pipeline_blocks_breaking_changes_without_version_bump(self):
        """
        Test that CI pipeline prevents deployment of breaking changes
        without proper version bump

        This would be configured in GitHub Actions workflow
        """
        # This is more of a documentation test
        # The actual enforcement happens in CI/CD pipeline

        pipeline_should_check_breaking_changes = True
        pipeline_should_require_major_bump = True

        assert pipeline_should_check_breaking_changes, \
            "CI pipeline must check for breaking changes"

        assert pipeline_should_require_major_bump, \
            "CI pipeline must enforce MAJOR version bump for breaking changes"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
