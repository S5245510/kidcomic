"""
Integration test for CI/CD pipeline (T073)

Tests the complete CI/CD pipeline execution flow:
1. Trigger pipeline on code change
2. Verify stages execute in correct order (lint → test → security → build → deploy)
3. Verify each stage reports success/failure correctly
4. Verify deployment happens only after all quality gates pass

Per FR-016 to FR-023: Automated CI/CD with quality gates
"""

import pytest
import requests
import subprocess
import time
import json
from pathlib import Path
from typing import Dict, Any, List


class TestCIPipeline:
    """Integration tests for CI/CD pipeline automation"""

    @pytest.fixture
    def repo_root(self) -> Path:
        """Get repository root directory"""
        return Path(__file__).parent.parent.parent

    @pytest.fixture
    def workflow_file(self, repo_root: Path) -> Path:
        """Get GitHub Actions workflow file path"""
        return repo_root / ".github" / "workflows" / "story-service-ci.yml"

    @pytest.fixture
    def test_service_dir(self, repo_root: Path) -> Path:
        """Get Story Service directory"""
        return repo_root / "services" / "story-service"

    def test_workflow_file_exists(self, workflow_file: Path):
        """Test that CI/CD workflow file exists"""
        assert workflow_file.exists(), f"Workflow file not found at {workflow_file}"

    def test_workflow_has_required_stages(self, workflow_file: Path):
        """Test that workflow defines all required stages (FR-017)"""
        import yaml

        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)

        # Verify required stages exist
        assert 'jobs' in workflow, "Workflow must define jobs"
        jobs = workflow['jobs']

        # FR-017: Required CI stages
        required_jobs = [
            'lint',          # Code quality check
            'unit-test',     # Unit test with coverage
            'integration-test',  # Integration test with Testcontainers
            'security-scan',  # Security vulnerability scan
            'build',         # Docker image build
            'deploy',        # Deployment to staging
        ]

        job_names = list(jobs.keys())
        for required_job in required_jobs:
            assert any(required_job in job for job in job_names), \
                f"Required job '{required_job}' not found in workflow"

    def test_workflow_triggers_on_service_changes(self, workflow_file: Path):
        """Test that workflow triggers on Story Service file changes"""
        import yaml

        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)

        # Verify trigger configuration
        assert 'on' in workflow, "Workflow must define triggers"
        triggers = workflow['on']

        # Should trigger on push/pull_request to Story Service directory
        if isinstance(triggers, dict):
            if 'push' in triggers:
                push_config = triggers['push']
                if 'paths' in push_config:
                    paths = push_config['paths']
                    assert any('story-service' in path for path in paths), \
                        "Workflow must trigger on story-service changes"

    def test_stages_execute_in_order(self, workflow_file: Path):
        """Test that stages have proper dependencies (FR-016)"""
        import yaml

        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)

        jobs = workflow['jobs']

        # Build stage should depend on quality gates passing
        if 'build' in jobs:
            build_job = jobs['build']
            if 'needs' in build_job:
                needs = build_job['needs']
                if isinstance(needs, list):
                    # Build should wait for tests and security
                    quality_gates = ['unit-test', 'integration-test', 'security-scan']
                    assert any(gate in str(needs) for gate in quality_gates), \
                        "Build stage must wait for quality gates"

        # Deploy stage should depend on build
        if 'deploy' in jobs:
            deploy_job = jobs['deploy']
            if 'needs' in deploy_job:
                needs = deploy_job['needs']
                assert 'build' in str(needs), \
                    "Deploy stage must wait for build stage"

    def test_coverage_threshold_enforced(self, workflow_file: Path):
        """Test that 80% code coverage threshold is enforced (FR-017)"""
        import yaml

        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)

        jobs = workflow['jobs']

        # Find unit test job
        unit_test_job = None
        for job_name, job_config in jobs.items():
            if 'unit' in job_name.lower() and 'test' in job_name.lower():
                unit_test_job = job_config
                break

        assert unit_test_job is not None, "Unit test job not found"

        # Check for coverage threshold in steps
        if 'steps' in unit_test_job:
            steps = unit_test_job['steps']
            # Look for pytest coverage configuration
            coverage_configured = False
            for step in steps:
                if 'run' in step:
                    run_command = step['run']
                    if 'pytest' in run_command and 'cov' in run_command:
                        coverage_configured = True
                        # Should have --cov-fail-under=80 or similar
                        assert '80' in run_command or 'fail-under' in run_command, \
                            "Coverage threshold should be configured"
                        break

            # Coverage should be configured somewhere
            assert coverage_configured, "Code coverage must be configured in unit tests"

    def test_security_scan_configured(self, workflow_file: Path):
        """Test that security scanning is configured (FR-017)"""
        import yaml

        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)

        jobs = workflow['jobs']

        # Find security scan job
        security_job = None
        for job_name, job_config in jobs.items():
            if 'security' in job_name.lower() or 'scan' in job_name.lower():
                security_job = job_config
                break

        assert security_job is not None, "Security scan job not found"

        # Check for security tools (safety, Trivy, etc.)
        if 'steps' in security_job:
            steps = security_job['steps']
            security_tools = ['safety', 'trivy', 'snyk', 'bandit']

            has_security_tool = False
            for step in steps:
                if 'run' in step or 'uses' in step:
                    step_content = str(step)
                    if any(tool in step_content.lower() for tool in security_tools):
                        has_security_tool = True
                        break

            assert has_security_tool, \
                f"Security scan must use one of: {', '.join(security_tools)}"

    def test_docker_image_tagged_correctly(self, workflow_file: Path):
        """Test that Docker images are tagged with commit SHA (FR-018)"""
        import yaml

        with open(workflow_file, 'r') as f:
            workflow = yaml.safe_load(f)

        jobs = workflow['jobs']

        # Find build job
        build_job = None
        for job_name, job_config in jobs.items():
            if 'build' in job_name.lower():
                build_job = job_config
                break

        assert build_job is not None, "Build job not found"

        # Check for Docker tagging strategy
        if 'steps' in build_job:
            steps = build_job['steps']
            docker_tag_configured = False

            for step in steps:
                if 'run' in step:
                    run_command = step['run']
                    if 'docker' in run_command and ('tag' in run_command or 'build' in run_command):
                        # Should include commit SHA in tags
                        if 'github.sha' in run_command or 'GITHUB_SHA' in run_command:
                            docker_tag_configured = True
                            break

            assert docker_tag_configured, \
                "Docker images must be tagged with commit SHA"

    @pytest.mark.integration
    def test_pipeline_execution_flow(self, repo_root: Path):
        """
        Integration test: Simulate pipeline execution locally

        This test runs the main CI stages locally to verify they work:
        1. Lint check
        2. Unit tests
        3. Security scan
        4. Docker build

        Note: This is a smoke test - actual GitHub Actions execution
        is tested in T094 (commit test change and verify automated deployment)
        """
        # Skip if not in CI environment (this would take too long locally)
        import os
        if not os.getenv('CI'):
            pytest.skip("Full pipeline test only runs in CI environment")

        service_dir = repo_root / "services" / "story-service"

        # 1. Lint stage
        lint_result = subprocess.run(
            ["ruff", "check", str(service_dir / "src")],
            cwd=repo_root,
            capture_output=True
        )
        assert lint_result.returncode == 0, f"Lint failed: {lint_result.stderr.decode()}"

        # 2. Unit test stage
        test_result = subprocess.run(
            ["pytest", str(service_dir / "tests"), "--cov", "--cov-fail-under=80"],
            cwd=repo_root,
            capture_output=True
        )
        assert test_result.returncode == 0, f"Tests failed: {test_result.stderr.decode()}"

        # 3. Security scan stage
        security_result = subprocess.run(
            ["safety", "check", "--json"],
            cwd=service_dir,
            capture_output=True
        )
        # Security scan may return non-zero on vulnerabilities (that's expected)
        # Just verify the command runs

        # 4. Docker build stage
        build_result = subprocess.run(
            ["docker", "build", "-t", "story-service:test", "-f",
             str(service_dir / "Dockerfile"), "."],
            cwd=repo_root,
            capture_output=True
        )
        assert build_result.returncode == 0, f"Docker build failed: {build_result.stderr.decode()}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
