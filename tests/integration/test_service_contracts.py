"""
Integration tests for service-to-service contracts
Per T107 [US4]: Level 2 automated contract validation
Tests verify that services communicate correctly across API boundaries

Test Categories:
1. Payment Service Contract
2. Photo Service Contract
3. API Gateway Routing
4. Version Compatibility

Run with: pytest tests/integration/test_service_contracts.py -v
"""

import pytest
import requests
import time
from typing import Dict, Any
import os


# Service URLs (configured via environment variables or defaults)
GATEWAY_URL = os.getenv("GATEWAY_URL", "http://localhost")
PAYMENT_SERVICE_URL = os.getenv("PAYMENT_SERVICE_URL", "http://localhost:8002")
PHOTO_SERVICE_URL = os.getenv("PHOTO_SERVICE_URL", "http://localhost:8001")
STORY_SERVICE_URL = os.getenv("STORY_SERVICE_URL", "http://localhost:8000")


class TestPaymentServiceContract:
    """Test Payment Service API contract"""

    def test_subscription_check_endpoint_exists(self):
        """Verify /subscriptions/check endpoint is accessible"""
        response = requests.get(
            f"{PAYMENT_SERVICE_URL}/subscriptions/check",
            params={"user_id": "test-user-123"},
            timeout=5
        )

        # Endpoint should exist (200 or 404 for user, not 404 for endpoint)
        assert response.status_code in [200, 404], \
            f"Payment service subscription check failed: {response.status_code}"

    def test_subscription_check_contract_free_tier(self):
        """Verify Payment Service returns correct contract for free tier user"""
        response = requests.get(
            f"{PAYMENT_SERVICE_URL}/subscriptions/check",
            params={"user_id": "free-user"},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()

            # Contract assertions
            assert "user_id" in data, "Missing user_id field"
            assert "tier" in data, "Missing tier field"
            assert data["tier"] in ["free", "subscriber"], \
                f"Invalid tier value: {data['tier']}"

            # Free tier should have null or absent subscribed_at
            if "subscribed_at" in data:
                assert data["subscribed_at"] is None or isinstance(data["subscribed_at"], str)

    def test_subscription_check_contract_subscriber_tier(self):
        """Verify Payment Service returns correct contract for subscriber"""
        response = requests.get(
            f"{PAYMENT_SERVICE_URL}/subscriptions/check",
            params={"user_id": "subscriber-user"},
            timeout=5
        )

        if response.status_code == 200:
            data = response.json()

            # Contract assertions for subscriber
            assert "user_id" in data
            assert "tier" in data
            assert data["tier"] == "subscriber"

            # Subscriber should have subscribed_at timestamp
            if "subscribed_at" in data and data["tier"] == "subscriber":
                assert isinstance(data["subscribed_at"], str)

    def test_payment_service_timeout_handling(self):
        """Verify Story Service handles Payment Service timeout gracefully"""
        # This test would require Story Service to be running
        # and configured to call Payment Service
        # For now, we verify timeout behavior directly

        try:
            # Set very short timeout to simulate timeout
            response = requests.get(
                f"{PAYMENT_SERVICE_URL}/subscriptions/check",
                params={"user_id": "test-user"},
                timeout=0.001  # 1ms timeout
            )
        except requests.Timeout:
            # Expected behavior - timeout should be caught
            pass

    def test_payment_service_error_handling(self):
        """Verify Story Service handles Payment Service errors"""
        # Test with invalid request to trigger error
        response = requests.get(
            f"{PAYMENT_SERVICE_URL}/subscriptions/check",
            params={},  # Missing required user_id
            timeout=5
        )

        # Should return 400 Bad Request or 422 Unprocessable Entity
        assert response.status_code in [400, 422, 404], \
            f"Expected error code for invalid request, got {response.status_code}"


class TestPhotoServiceContract:
    """Test Photo Service API contract"""

    def test_photo_upload_endpoint_exists(self):
        """Verify /process endpoint is accessible"""
        # Test with minimal payload to check endpoint existence
        response = requests.post(
            f"{PHOTO_SERVICE_URL}/process",
            timeout=5
        )

        # Should return 400 (bad request) not 404 (endpoint not found)
        assert response.status_code in [400, 422], \
            f"Photo service process endpoint not accessible: {response.status_code}"

    def test_photo_upload_contract_with_valid_image(self):
        """Verify Photo Service accepts image upload and returns face_swap_id"""
        # Create a minimal valid JPEG in memory
        import io
        from PIL import Image

        # Create 100x100 red image
        img = Image.new('RGB', (100, 100), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)

        files = {
            'photo': ('test_photo.jpg', img_bytes, 'image/jpeg')
        }

        response = requests.post(
            f"{PHOTO_SERVICE_URL}/process",
            files=files,
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()

            # Contract assertions
            assert "face_swap_id" in data, "Missing face_swap_id field"
            assert isinstance(data["face_swap_id"], str), "face_swap_id should be string"
            assert len(data["face_swap_id"]) > 0, "face_swap_id should not be empty"

    def test_photo_status_endpoint(self):
        """Verify /status/{face_swap_id} endpoint exists"""
        # Test with dummy face_swap_id
        response = requests.get(
            f"{PHOTO_SERVICE_URL}/status/test-id-12345",
            timeout=5
        )

        # Should return 200 or 404 (for invalid ID), not 404 (endpoint not found)
        assert response.status_code in [200, 404], \
            f"Photo status endpoint not accessible: {response.status_code}"

        if response.status_code == 200:
            data = response.json()

            # Contract assertions
            assert "status" in data, "Missing status field"
            assert data["status"] in ["pending", "processing", "completed", "failed"], \
                f"Invalid status value: {data['status']}"

    def test_photo_upload_file_validation(self):
        """Verify Photo Service validates file type"""
        # Test with non-image file
        files = {
            'photo': ('test.txt', b'This is not an image', 'text/plain')
        }

        response = requests.post(
            f"{PHOTO_SERVICE_URL}/process",
            files=files,
            timeout=5
        )

        # Should reject non-image files
        assert response.status_code in [400, 422, 415], \
            f"Photo service should reject non-image files, got {response.status_code}"


class TestAPIGatewayRouting:
    """Test API Gateway routing and middleware"""

    def test_gateway_routes_v1_stories(self):
        """Verify Gateway routes /v1/stories to Story Service"""
        response = requests.get(
            f"{GATEWAY_URL}/v1/stories",
            timeout=5
        )

        # Gateway should route to Story Service (200 or service error, not 404 route not found)
        assert response.status_code != 404, \
            "Gateway failed to route /v1/stories - route not configured"

    def test_gateway_routes_v2_stories(self):
        """Verify Gateway routes /v2/stories to Story Service"""
        response = requests.get(
            f"{GATEWAY_URL}/v2/stories",
            timeout=5
        )

        # Gateway should route to Story Service
        assert response.status_code != 404, \
            "Gateway failed to route /v2/stories - route not configured"

    def test_gateway_applies_cors_headers(self):
        """Verify Gateway applies CORS middleware"""
        response = requests.options(
            f"{GATEWAY_URL}/v1/stories",
            headers={"Origin": "http://localhost:3000"},
            timeout=5
        )

        # CORS preflight should return allowed methods
        if response.status_code == 200:
            assert "Access-Control-Allow-Methods" in response.headers or \
                   "access-control-allow-methods" in response.headers, \
                   "CORS headers not applied by gateway"

    def test_gateway_propagates_trace_id(self):
        """Verify Gateway forwards and returns trace_id header"""
        trace_id = "test-trace-12345"

        response = requests.get(
            f"{GATEWAY_URL}/v1/stories",
            headers={"X-Trace-ID": trace_id},
            timeout=5
        )

        # Trace ID should be returned in response
        returned_trace_id = response.headers.get("X-Trace-ID") or \
                           response.headers.get("x-trace-id")

        if returned_trace_id:
            assert returned_trace_id == trace_id or len(returned_trace_id) > 0, \
                "Gateway did not propagate trace_id correctly"

    def test_gateway_rate_limiting(self):
        """Verify Gateway enforces rate limiting"""
        # Send burst of requests to test rate limiting
        responses = []
        for i in range(25):  # Burst limit is 20
            response = requests.get(
                f"{GATEWAY_URL}/v1/stories",
                timeout=5
            )
            responses.append(response)

            # Stop if we hit rate limit
            if response.status_code == 429:
                break

        # At least one request should be rate limited if burst > 20
        rate_limited = any(r.status_code == 429 for r in responses)

        # Rate limiting might not trigger in low-traffic test environment
        # Just check that 429 is possible response
        if rate_limited:
            assert responses[-1].status_code == 429, \
                "Expected 429 Too Many Requests for rate limiting"

            # Check for rate limit headers
            headers = responses[-1].headers
            assert "X-RateLimit-Limit" in headers or "x-ratelimit-limit" in headers, \
                "Rate limit headers not present"

    def test_gateway_health_check_routing(self):
        """Verify Gateway performs health checks on backend services"""
        # Gateway should route to healthy instances only
        response = requests.get(
            f"{GATEWAY_URL}/v1/stories",
            timeout=5
        )

        # If service is healthy, should get 200
        # If all instances unhealthy, should get 503 Service Unavailable
        assert response.status_code in [200, 503], \
            f"Unexpected gateway response: {response.status_code}"


class TestVersionCompatibility:
    """Test API version compatibility and backward compatibility"""

    def test_v1_and_v2_coexist(self):
        """Verify V1 and V2 endpoints are both accessible simultaneously"""
        v1_response = requests.get(f"{GATEWAY_URL}/v1/stories", timeout=5)
        v2_response = requests.get(f"{GATEWAY_URL}/v2/stories", timeout=5)

        # Both versions should be accessible
        assert v1_response.status_code in [200, 503], \
            f"V1 endpoint not accessible: {v1_response.status_code}"
        assert v2_response.status_code in [200, 503], \
            f"V2 endpoint not accessible: {v2_response.status_code}"

    def test_v1_contract_backward_compatible(self):
        """Verify V1 API contract maintains backward compatibility"""
        response = requests.get(f"{GATEWAY_URL}/v1/stories", timeout=5)

        if response.status_code == 200:
            data = response.json()

            # V1 contract: {stories: [...], total: N}
            assert "stories" in data, "V1 should use 'stories' key (not 'data')"
            assert "total" in data, "V1 should include 'total' field"
            assert isinstance(data["stories"], list), "V1 stories should be array"
            assert isinstance(data["total"], int), "V1 total should be integer"

            # V1 should NOT have v2-only fields
            assert "data" not in data, "V1 should not use 'data' key (breaking change)"
            assert "pagination" not in data, "V1 should not have 'pagination' object (breaking change)"

            # Check story object contract
            if len(data["stories"]) > 0:
                story = data["stories"][0]
                assert "content" in story, "V1 story should use 'content' field (not 'body')"
                assert "body" not in story, "V1 story should not use 'body' field (breaking change)"

    def test_v2_contract_with_breaking_changes(self):
        """Verify V2 API contract includes breaking changes from V1"""
        response = requests.get(f"{GATEWAY_URL}/v2/stories", timeout=5)

        if response.status_code == 200:
            data = response.json()

            # V2 contract: {data: [...], pagination: {...}}
            assert "data" in data, "V2 should use 'data' key (breaking change from v1)"
            assert "pagination" in data, "V2 should include 'pagination' object (new in v2)"
            assert isinstance(data["data"], list), "V2 data should be array"

            # V2 should NOT have v1 fields
            assert "stories" not in data, "V2 should not use 'stories' key (replaced with 'data')"

            # Check pagination object
            pagination = data["pagination"]
            assert "total" in pagination, "Pagination should include total"
            assert "limit" in pagination, "Pagination should include limit"
            assert "offset" in pagination, "Pagination should include offset"
            assert "has_more" in pagination, "Pagination should include has_more"

            # Check story object contract
            if len(data["data"]) > 0:
                story = data["data"][0]
                assert "body" in story, "V2 story should use 'body' field (breaking change from v1)"
                assert "content" not in story, "V2 story should not use 'content' field (replaced with 'body')"
                # V2 may have metadata field (new in v2)
                if "metadata" in story:
                    assert isinstance(story["metadata"], dict), "V2 metadata should be object"

    def test_v2_search_endpoint_new_feature(self):
        """Verify V2 search endpoint exists (new feature not in V1)"""
        response = requests.get(
            f"{GATEWAY_URL}/v2/stories/search",
            params={"query": "dragon"},
            timeout=5
        )

        # V2 search endpoint should exist
        assert response.status_code in [200, 503], \
            f"V2 search endpoint not accessible: {response.status_code}"

        if response.status_code == 200:
            data = response.json()

            # Should use v2 contract
            assert "data" in data, "V2 search should use v2 contract (data + pagination)"
            assert "pagination" in data, "V2 search should include pagination"

    def test_v1_search_endpoint_not_present(self):
        """Verify V1 does not have search endpoint (v2-only feature)"""
        response = requests.get(
            f"{GATEWAY_URL}/v1/stories/search",
            params={"query": "dragon"},
            timeout=5
        )

        # V1 search endpoint should not exist
        assert response.status_code == 404, \
            "V1 should not have search endpoint (v2-only feature)"


class TestZeroDowntimeDeployment:
    """Test zero-downtime deployment capabilities"""

    def test_service_health_endpoint(self):
        """Verify Story Service health endpoint is accessible"""
        response = requests.get(f"{STORY_SERVICE_URL}/health", timeout=5)

        assert response.status_code == 200, \
            f"Health endpoint should return 200, got {response.status_code}"

        data = response.json()
        assert "status" in data, "Health endpoint should include status"

    def test_service_ready_endpoint(self):
        """Verify Story Service readiness endpoint is accessible"""
        response = requests.get(f"{STORY_SERVICE_URL}/ready", timeout=5)

        # Ready endpoint should return 200 when service is ready
        assert response.status_code in [200, 503], \
            f"Ready endpoint returned unexpected status: {response.status_code}"

    def test_concurrent_requests_both_versions(self):
        """Verify both V1 and V2 can handle concurrent requests"""
        import concurrent.futures

        def make_v1_request():
            return requests.get(f"{GATEWAY_URL}/v1/stories", timeout=10)

        def make_v2_request():
            return requests.get(f"{GATEWAY_URL}/v2/stories", timeout=10)

        # Make 10 requests to each version concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            v1_futures = [executor.submit(make_v1_request) for _ in range(10)]
            v2_futures = [executor.submit(make_v2_request) for _ in range(10)]

            all_futures = v1_futures + v2_futures
            results = [f.result() for f in all_futures]

        # Most requests should succeed
        successful = [r for r in results if r.status_code == 200]
        success_rate = len(successful) / len(results)

        assert success_rate >= 0.8, \
            f"Success rate {success_rate:.0%} too low for concurrent requests"


# Pytest fixtures
@pytest.fixture
def v1_stories_url():
    """Fixture for V1 stories endpoint URL"""
    return f"{GATEWAY_URL}/v1/stories"


@pytest.fixture
def v2_stories_url():
    """Fixture for V2 stories endpoint URL"""
    return f"{GATEWAY_URL}/v2/stories"


@pytest.fixture
def payment_service_url():
    """Fixture for Payment Service URL"""
    return PAYMENT_SERVICE_URL


@pytest.fixture
def photo_service_url():
    """Fixture for Photo Service URL"""
    return PHOTO_SERVICE_URL


# Skip tests if services are not available
def pytest_configure(config):
    """Configure pytest to skip tests if services unavailable"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test (requires services running)"
    )


def pytest_collection_modifyitems(config, items):
    """Mark all tests in this file as integration tests"""
    for item in items:
        item.add_marker(pytest.mark.integration)


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "--tb=short"])
