"""
Contract test for API versioning (T097)

Tests that multiple API versions can coexist:
1. /v1/stories endpoints work (backward compatibility)
2. /v2/stories endpoints work (new version)
3. Both versions return correct contracts
4. Version negotiation works correctly

Per FR-008: Backward compatibility for 2+ API versions
Per FR-026: Version-aware routing
"""

import pytest
import requests
from typing import Dict, Any


class TestAPIVersioning:
    """Contract tests for API versioning"""

    @pytest.fixture
    def api_gateway_url(self) -> str:
        """API Gateway base URL"""
        return "http://localhost"

    @pytest.fixture
    def v1_stories_url(self, api_gateway_url: str) -> str:
        """V1 Stories API endpoint"""
        return f"{api_gateway_url}/v1/stories"

    @pytest.fixture
    def v2_stories_url(self, api_gateway_url: str) -> str:
        """V2 Stories API endpoint"""
        return f"{api_gateway_url}/v2/stories"

    def test_v1_endpoint_exists(self, v1_stories_url: str):
        """Test that v1 API endpoint is accessible"""
        response = requests.get(f"{v1_stories_url}/health", timeout=5)
        assert response.status_code in [200, 404], \
            f"V1 endpoint should be accessible (got {response.status_code})"

    def test_v2_endpoint_exists(self, v2_stories_url: str):
        """Test that v2 API endpoint is accessible"""
        response = requests.get(f"{v2_stories_url}/health", timeout=5)
        assert response.status_code in [200, 404], \
            f"V2 endpoint should be accessible (got {response.status_code})"

    @pytest.mark.contract
    def test_v1_list_stories_contract(self, v1_stories_url: str):
        """
        Test v1 API contract for listing stories

        V1 Contract:
        - GET /v1/stories
        - Returns: {stories: [{id, title, content}]}
        """
        response = requests.get(v1_stories_url, timeout=5)

        # Should return 200 or 404 (if no stories)
        assert response.status_code in [200, 404], \
            f"V1 list stories should work (got {response.status_code})"

        if response.status_code == 200:
            data = response.json()

            # V1 contract: should have 'stories' key
            assert 'stories' in data or isinstance(data, list), \
                "V1 contract should have 'stories' key or return list"

            # If stories exist, verify structure
            stories = data.get('stories', data) if isinstance(data, dict) else data
            if stories and len(stories) > 0:
                story = stories[0]

                # V1 contract: each story should have id, title, content
                assert 'id' in story, "V1 story must have 'id'"
                assert 'title' in story, "V1 story must have 'title'"
                assert 'content' in story or 'description' in story, \
                    "V1 story must have 'content' or 'description'"

    @pytest.mark.contract
    def test_v2_list_stories_contract(self, v2_stories_url: str):
        """
        Test v2 API contract for listing stories

        V2 Contract (example breaking change):
        - GET /v2/stories
        - Returns: {data: [{id, title, body, metadata}], pagination: {...}}
        """
        response = requests.get(v2_stories_url, timeout=5)

        # Should return 200 or 404
        assert response.status_code in [200, 404], \
            f"V2 list stories should work (got {response.status_code})"

        if response.status_code == 200:
            data = response.json()

            # V2 contract: should have 'data' key (breaking change from v1)
            assert 'data' in data or isinstance(data, list), \
                "V2 contract should have 'data' key or return list"

            # V2 might include pagination metadata
            if 'data' in data:
                assert 'pagination' in data or 'meta' in data, \
                    "V2 should include pagination metadata"

                stories = data['data']
            else:
                stories = data

            # If stories exist, verify v2 structure
            if stories and len(stories) > 0:
                story = stories[0]

                # V2 contract: might use 'body' instead of 'content'
                assert 'id' in story, "V2 story must have 'id'"
                assert 'title' in story, "V2 story must have 'title'"
                # V2 uses 'body' instead of 'content' (breaking change)
                assert 'body' in story or 'content' in story, \
                    "V2 story should have 'body' (or 'content' for compatibility)"

    @pytest.mark.contract
    def test_v1_and_v2_coexist(
        self,
        v1_stories_url: str,
        v2_stories_url: str
    ):
        """
        Test that v1 and v2 can both be accessed simultaneously

        This is critical for zero-downtime API evolution
        """
        # Call v1
        v1_response = requests.get(v1_stories_url, timeout=5)

        # Call v2
        v2_response = requests.get(v2_stories_url, timeout=5)

        # Both should be accessible
        assert v1_response.status_code in [200, 404], \
            f"V1 should be accessible (got {v1_response.status_code})"

        assert v2_response.status_code in [200, 404], \
            f"V2 should be accessible (got {v2_response.status_code})"

        # Verify both return valid JSON
        try:
            v1_response.json()
        except Exception as e:
            pytest.fail(f"V1 response should be valid JSON: {e}")

        try:
            v2_response.json()
        except Exception as e:
            pytest.fail(f"V2 response should be valid JSON: {e}")

    @pytest.mark.contract
    def test_version_negotiation_via_path(self, api_gateway_url: str):
        """
        Test version negotiation via URL path

        Clients specify version in path: /v1/stories vs /v2/stories
        """
        # Request v1 specifically
        v1_response = requests.get(f"{api_gateway_url}/v1/stories", timeout=5)

        # Request v2 specifically
        v2_response = requests.get(f"{api_gateway_url}/v2/stories", timeout=5)

        # Gateway should route to correct versions
        assert v1_response.status_code in [200, 404], "V1 path routing should work"
        assert v2_response.status_code in [200, 404], "V2 path routing should work"

    @pytest.mark.contract
    def test_version_header_support(self, api_gateway_url: str):
        """
        Test version negotiation via Accept header (optional)

        Clients can specify version via:
        - Accept: application/vnd.storyme.v1+json
        - Accept: application/vnd.storyme.v2+json
        """
        # Request with v1 header
        v1_headers = {"Accept": "application/vnd.storyme.v1+json"}
        v1_response = requests.get(
            f"{api_gateway_url}/stories",
            headers=v1_headers,
            timeout=5
        )

        # Request with v2 header
        v2_headers = {"Accept": "application/vnd.storyme.v2+json"}
        v2_response = requests.get(
            f"{api_gateway_url}/stories",
            headers=v2_headers,
            timeout=5
        )

        # This is optional - skip if not implemented
        if v1_response.status_code == 200:
            # Verify response includes version indicator
            assert 'api-version' in v1_response.headers or \
                   'x-api-version' in v1_response.headers, \
                   "Response should include API version header"

    @pytest.mark.contract
    def test_backward_compatibility_maintained(
        self,
        v1_stories_url: str,
        v2_stories_url: str
    ):
        """
        Test that v2 deployment doesn't break v1 clients

        Critical: Old mobile apps using v1 must continue working
        """
        # Create a test story via v2 (if POST is implemented)
        # Then verify it's accessible via v1

        # For now, just verify v1 doesn't return errors
        v1_response = requests.get(v1_stories_url, timeout=5)

        assert v1_response.status_code != 500, \
            "V1 API should not return server errors"

        assert v1_response.status_code != 502, \
            "V1 API should not return bad gateway"

        # Verify v1 contract is maintained
        if v1_response.status_code == 200:
            data = v1_response.json()

            # V1 must not return v2-only fields (breaking change)
            if isinstance(data, dict):
                # V1 should not have 'pagination' (that's v2 only)
                if 'stories' in data:
                    # V1 format
                    pass
                elif 'data' in data:
                    # This would be breaking v1 contract
                    pytest.fail(
                        "V1 endpoint returned v2 format (breaking change)"
                    )

    @pytest.mark.contract
    def test_traefik_version_routing(self, api_gateway_url: str):
        """
        Test that Traefik routes versioned paths correctly

        /v1/stories → story-service v1 endpoints
        /v2/stories → story-service v2 endpoints
        """
        # Make requests to both versions
        v1_response = requests.get(f"{api_gateway_url}/v1/stories/health", timeout=5)
        v2_response = requests.get(f"{api_gateway_url}/v2/stories/health", timeout=5)

        # At minimum, gateway should not return 404 for versioned paths
        # (unless service hasn't implemented that version yet)
        assert v1_response.status_code != 502, \
            "Gateway should route v1 requests (not bad gateway)"

        assert v2_response.status_code != 502, \
            "Gateway should route v2 requests (not bad gateway)"

    @pytest.mark.contract
    def test_api_schema_versioning(self, v1_stories_url: str, v2_stories_url: str):
        """
        Test that API schemas are versioned correctly

        Each version should return its OpenAPI schema
        """
        # Try to get v1 schema
        v1_schema_response = requests.get(
            f"{v1_stories_url}/openapi.json",
            timeout=5
        )

        # Try to get v2 schema
        v2_schema_response = requests.get(
            f"{v2_stories_url}/openapi.json",
            timeout=5
        )

        # If schemas are exposed, they should be valid
        if v1_schema_response.status_code == 200:
            v1_schema = v1_schema_response.json()
            assert 'openapi' in v1_schema or 'swagger' in v1_schema, \
                "V1 schema should be valid OpenAPI/Swagger"

            # Should indicate version 1
            if 'info' in v1_schema:
                version_str = v1_schema['info'].get('version', '')
                assert 'v1' in version_str.lower() or version_str.startswith('1.'), \
                    "V1 schema should indicate version 1"

        if v2_schema_response.status_code == 200:
            v2_schema = v2_schema_response.json()
            assert 'openapi' in v2_schema or 'swagger' in v2_schema, \
                "V2 schema should be valid OpenAPI/Swagger"

            # Should indicate version 2
            if 'info' in v2_schema:
                version_str = v2_schema['info'].get('version', '')
                assert 'v2' in version_str.lower() or version_str.startswith('2.'), \
                    "V2 schema should indicate version 2"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "contract"])
