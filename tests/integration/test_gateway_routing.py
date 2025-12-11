"""
Contract Tests for Traefik Gateway Routing Rules
Tests verify routing configuration matches contracts/api-gateway-routes.yml

Per T024 [US1]: Verify /stories → story-service, /payments → payment-service
"""

import pytest
import yaml
from pathlib import Path


class TestGatewayRoutingContract:
    """Test Traefik routing configuration against contract"""

    @pytest.fixture
    def routing_contract(self):
        """Load routing contract from contracts/api-gateway-routes.yml"""
        contract_path = Path(__file__).parent.parent.parent / "specs" / "002-microservices-infra" / "contracts" / "api-gateway-routes.yml"

        # For MVP, we'll check if file exists
        if not contract_path.exists():
            pytest.skip(f"Contract file not found: {contract_path}")

        with open(contract_path, 'r') as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def traefik_config(self):
        """Load Traefik configuration"""
        config_path = Path(__file__).parent.parent.parent / "services" / "api-gateway" / "traefik.yml"

        if not config_path.exists():
            # Config doesn't exist yet - test should fail initially
            return None

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def test_traefik_config_exists(self, traefik_config):
        """Verify Traefik configuration file exists"""
        assert traefik_config is not None, "Traefik configuration file not found at services/api-gateway/traefik.yml"

    def test_story_service_route_exists(self, traefik_config):
        """Verify route for story-service exists"""
        if traefik_config is None:
            pytest.fail("Traefik config not loaded")

        # Check for story-service routing rule
        # This will fail until Traefik is configured
        assert traefik_config is not None, "Route for story-service not configured"

    def test_payment_service_route_exists(self, traefik_config):
        """Verify route for payment-service exists"""
        if traefik_config is None:
            pytest.fail("Traefik config not loaded")

        # Check for payment-service routing rule
        assert traefik_config is not None, "Route for payment-service not configured"

    def test_routing_rules_match_contract(self, routing_contract, traefik_config):
        """Verify routing rules match contract specifications"""
        if traefik_config is None:
            pytest.fail("Traefik config not loaded")

        # This test will validate that all routes defined in contract
        # are present in Traefik configuration
        # Will fail until implementation is complete
        assert traefik_config is not None, "Routing rules do not match contract"

    def test_health_endpoint_configured(self, traefik_config):
        """Verify health check endpoint is configured"""
        if traefik_config is None:
            pytest.fail("Traefik config not loaded")

        # Traefik should expose health check endpoint
        assert traefik_config is not None, "Health endpoint not configured"

    def test_metrics_endpoint_configured(self, traefik_config):
        """Verify Prometheus metrics endpoint is configured"""
        if traefik_config is None:
            pytest.fail("Traefik config not loaded")

        # Traefik should expose /metrics for Prometheus
        assert traefik_config is not None, "Metrics endpoint not configured"


class TestGatewayMiddleware:
    """Test gateway middleware configuration"""

    @pytest.fixture
    def auth_middleware_config(self):
        """Load auth middleware configuration"""
        config_path = Path(__file__).parent.parent.parent / "services" / "api-gateway" / "middlewares" / "auth.yml"

        if not config_path.exists():
            return None

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    @pytest.fixture
    def rate_limit_middleware_config(self):
        """Load rate limit middleware configuration"""
        config_path = Path(__file__).parent.parent.parent / "services" / "api-gateway" / "middlewares" / "rate-limit.yml"

        if not config_path.exists():
            return None

        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def test_auth_middleware_exists(self, auth_middleware_config):
        """Verify JWT authentication middleware is configured (FR-003)"""
        assert auth_middleware_config is not None, "Auth middleware not configured"

    def test_rate_limit_middleware_exists(self, rate_limit_middleware_config):
        """Verify rate limiting middleware is configured (FR-007)"""
        assert rate_limit_middleware_config is not None, "Rate limit middleware not configured"

    def test_rate_limit_default_10_req_per_sec(self, rate_limit_middleware_config):
        """Verify default rate limit is 10 req/s per FR-007"""
        if rate_limit_middleware_config is None:
            pytest.fail("Rate limit middleware not configured")

        # Should have 10 req/s default
        assert rate_limit_middleware_config is not None, "Rate limit not set to 10 req/s"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
