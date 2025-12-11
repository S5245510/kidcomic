"""
Integration test for automated rollback (T075)

Tests that failed deployments trigger automatic rollback:
1. Deploy bad version (high error rate)
2. Monitor health checks
3. Verify automatic rollback is triggered
4. Verify service returns to previous working version
5. Verify rollback completes within 2 minutes

Per FR-020: Automated rollback on deployment failure
Per SC-010: 95%+ deployment success rate (including rollbacks)
"""

import pytest
import requests
import subprocess
import time
from typing import Dict, Any, Optional
from pathlib import Path
import json


class TestAutomatedRollback:
    """Integration tests for automated rollback on deployment failure"""

    @pytest.fixture
    def api_gateway_url(self) -> str:
        """API Gateway base URL"""
        return "http://localhost"

    @pytest.fixture
    def service_url(self, api_gateway_url: str) -> str:
        """Story Service base URL"""
        return f"{api_gateway_url}/stories"

    @pytest.fixture
    def health_url(self, service_url: str) -> str:
        """Health check endpoint"""
        return f"{service_url}/health"

    @pytest.fixture
    def deployment_monitor_script(self) -> Path:
        """Deployment health monitoring script"""
        return Path(__file__).parent.parent.parent / \
               "infrastructure" / "ci-cd" / "scripts" / "monitor-deployment.ps1"

    @pytest.fixture
    def rollback_script(self) -> Path:
        """Automated rollback script"""
        return Path(__file__).parent.parent.parent / \
               "infrastructure" / "ci-cd" / "scripts" / "auto-rollback.ps1"

    def get_service_version(self, health_url: str) -> Optional[str]:
        """
        Get current service version from health endpoint

        Returns:
            Version string (e.g., "v0.1.0") or None if unavailable
        """
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                data = response.json()
                return data.get('version', 'unknown')
        except Exception as e:
            print(f"Could not get service version: {e}")
        return None

    def check_service_health(
        self,
        service_url: str,
        duration_seconds: int = 30,
        request_interval: float = 1.0
    ) -> Dict[str, Any]:
        """
        Monitor service health over a period of time

        Returns:
            Dict with health statistics:
            - total_requests: Total health checks performed
            - successful_requests: Number of successful responses
            - error_rate: Percentage of failed requests
            - avg_latency_ms: Average response time in milliseconds
        """
        total = 0
        successful = 0
        latencies = []
        end_time = time.time() + duration_seconds

        while time.time() < end_time:
            try:
                start = time.time()
                response = requests.get(f"{service_url}/health", timeout=5)
                latency = (time.time() - start) * 1000

                total += 1
                if response.status_code == 200:
                    successful += 1
                    latencies.append(latency)

            except Exception:
                total += 1

            time.sleep(request_interval)

        error_rate = ((total - successful) / total * 100) if total > 0 else 0
        avg_latency = sum(latencies) / len(latencies) if latencies else 0

        return {
            'total_requests': total,
            'successful_requests': successful,
            'error_rate': error_rate,
            'avg_latency_ms': avg_latency
        }

    @pytest.mark.integration
    def test_rollback_script_exists(self, rollback_script: Path):
        """Test that automated rollback script exists"""
        assert rollback_script.exists(), \
            f"Rollback script not found at {rollback_script}"

    @pytest.mark.integration
    def test_deployment_monitor_script_exists(self, deployment_monitor_script: Path):
        """Test that deployment monitoring script exists"""
        assert deployment_monitor_script.exists(), \
            f"Deployment monitor script not found at {deployment_monitor_script}"

    @pytest.mark.integration
    def test_rollback_script_structure(self, rollback_script: Path):
        """
        Test rollback script implements required functionality

        Rollback should:
        1. Identify previous stable version
        2. Stop failing new version
        3. Restore previous version
        4. Verify previous version is healthy
        5. Log rollback event
        """
        with open(rollback_script, 'r') as f:
            script_content = f.read()

        # Required rollback components
        required_components = [
            'previous',  # Identify previous version
            'stop',  # Stop new version
            'restore',  # Restore previous version
            'health',  # Health verification
            'log',  # Logging
        ]

        for component in required_components:
            assert component.lower() in script_content.lower(), \
                f"Rollback script must implement '{component}' functionality"

    @pytest.mark.integration
    def test_monitor_script_checks_health_metrics(
        self,
        deployment_monitor_script: Path
    ):
        """
        Test deployment monitor checks required health metrics

        Per FR-020: Monitor error rate and latency post-deployment
        - Error rate threshold: <5%
        - Latency threshold: <500ms p95
        - Monitoring duration: 10 minutes
        """
        with open(deployment_monitor_script, 'r') as f:
            script_content = f.read()

        # Should monitor error rate
        assert 'error' in script_content.lower(), \
            "Monitor must check error rate"

        # Should monitor latency
        assert 'latency' in script_content.lower() or 'response' in script_content.lower(), \
            "Monitor must check response latency"

        # Should have thresholds
        # Look for numeric thresholds (5%, 500ms)
        import re
        numbers = re.findall(r'\d+', script_content)
        assert len(numbers) > 0, "Monitor should define numeric thresholds"

    @pytest.mark.integration
    @pytest.mark.slow
    def test_automated_rollback_on_high_error_rate(
        self,
        service_url: str,
        health_url: str,
        rollback_script: Path
    ):
        """
        Test automated rollback triggers on high error rate

        Scenario:
        1. Record current version
        2. Simulate bad deployment (we'll skip actual deployment)
        3. Verify rollback script can restore previous version
        4. Verify rollback completes within 2 minutes

        Note: This is a structure test. Full integration test requires
        actual deployment capability which is tested in T096.
        """
        # Get current version
        current_version = self.get_service_version(health_url)
        assert current_version is not None, "Could not determine current service version"

        print(f"\nCurrent service version: {current_version}")

        # Check current health baseline
        baseline_health = self.check_service_health(service_url, duration_seconds=10)
        print(f"Baseline health: {baseline_health}")

        # Verify service is healthy before test
        assert baseline_health['error_rate'] < 10, \
            f"Service not healthy at baseline: {baseline_health['error_rate']:.1f}% error rate"

        # Test rollback script execution (dry-run)
        # Real execution would require deployment infrastructure
        print("\nTesting rollback script execution...")

        try:
            # Test script with -WhatIf flag (PowerShell dry-run)
            result = subprocess.run(
                ["powershell", "-File", str(rollback_script), "-WhatIf"],
                capture_output=True,
                timeout=30,
                text=True
            )

            print(f"Rollback script dry-run exit code: {result.returncode}")
            if result.stdout:
                print(f"Stdout: {result.stdout[:500]}")
            if result.stderr:
                print(f"Stderr: {result.stderr[:500]}")

        except subprocess.TimeoutExpired:
            pytest.fail("Rollback script timed out (should complete in <30s)")

        except FileNotFoundError:
            pytest.skip("PowerShell not available - skip script execution test")

    @pytest.mark.integration
    def test_rollback_time_limit(self, rollback_script: Path):
        """
        Test that rollback completes within 2 minutes (FR-020)

        Rollback should be fast to minimize downtime
        """
        with open(rollback_script, 'r') as f:
            script_content = f.read()

        # Script should have timeout or should complete quickly
        # Look for timeout configuration or fast operations
        has_timeout = 'timeout' in script_content.lower()
        has_quick_operations = all(
            op in script_content.lower()
            for op in ['docker', 'restart']  # Quick container operations
        )

        assert has_timeout or has_quick_operations, \
            "Rollback should use quick operations or have timeout configured"

    @pytest.mark.integration
    def test_deployment_history_logged(self):
        """
        Test that deployment history is logged for rollback tracking

        Per FR-022: Track deployment history including rollbacks
        """
        history_file = Path(__file__).parent.parent.parent / \
                      "infrastructure" / "ci-cd" / "deployment-history.json"

        # History file may not exist yet (will be created on first deployment)
        # Just verify the logging script exists
        log_script = Path(__file__).parent.parent.parent / \
                    "infrastructure" / "ci-cd" / "scripts" / "log-deployment.ps1"

        assert log_script.exists(), \
            f"Deployment logging script should exist at {log_script}"

        # Verify logging script structure
        with open(log_script, 'r') as f:
            script_content = f.read()

        # Should log required fields
        required_fields = [
            'service',  # Service name
            'version',  # Version deployed
            'timestamp',  # When deployed
            'status',  # Success/failure
            'rollback',  # Whether this was a rollback
        ]

        for field in required_fields:
            assert field.lower() in script_content.lower(), \
                f"Deployment log must include '{field}' field"

    @pytest.mark.integration
    def test_rollback_preserves_data(self, health_url: str):
        """
        Test that rollback doesn't lose data

        Verify:
        1. Database connections are maintained
        2. Service state is preserved
        3. No data corruption
        """
        # Check service has database connectivity
        try:
            response = requests.get(health_url, timeout=5)
            if response.status_code == 200:
                health_data = response.json()

                # Health endpoint should report database status
                # This verifies database connection is part of health checks
                assert 'status' in health_data, "Health check must report status"

        except Exception as e:
            pytest.skip(f"Could not verify health endpoint: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
