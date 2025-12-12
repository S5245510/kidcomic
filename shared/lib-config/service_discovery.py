"""
Service Discovery Library
Per T112 [US4]: Version-aware service discovery for Consul
Lookup services by name and version range (e.g., "story-service >=v1.0.0 <v2.0.0")
"""

import os
import logging
from typing import Optional, List, Dict, Any, Tuple
import re

try:
    import consul
    CONSUL_AVAILABLE = True
except ImportError:
    CONSUL_AVAILABLE = False
    logging.warning("python-consul not installed - service discovery will run in stub mode")

logger = logging.getLogger(__name__)


class ServiceDiscovery:
    """
    Version-aware service discovery client for Consul
    Supports semantic versioning constraints for service lookup
    """

    def __init__(self, consul_host: str = "consul", consul_port: int = 8500):
        self.consul_host = consul_host
        self.consul_port = consul_port
        self.consul_client: Optional[Any] = None

        if CONSUL_AVAILABLE:
            try:
                self.consul_client = consul.Consul(host=consul_host, port=consul_port)
                # Test connection
                self.consul_client.agent.self()
                logger.info(f"ServiceDiscovery initialized - Connected to Consul at {consul_host}:{consul_port}")
            except Exception as e:
                logger.error(f"Failed to connect to Consul at {consul_host}:{consul_port}: {e}")
                self.consul_client = None
        else:
            logger.warning(f"ServiceDiscovery initialized (stub mode) - Consul client not available")

    def discover_service(
        self,
        service_name: str,
        version_constraint: Optional[str] = None,
        environment: Optional[str] = None,
        passing_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Discover service instances by name and version constraint

        Args:
            service_name: Base service name (e.g., "story-service")
            version_constraint: SemVer constraint (e.g., ">=v1.0.0 <v2.0.0", "v2.0.0", None for all)
            environment: Filter by environment (staging, production, etc.)
            passing_only: Only return instances passing health checks

        Returns:
            List of service instances with address, port, version, tags

        Examples:
            # Get all story-service instances
            instances = discover_service("story-service")

            # Get story-service v1.x.x instances
            instances = discover_service("story-service", version_constraint=">=v1.0.0 <v2.0.0")

            # Get story-service v2.0.0 instances in production
            instances = discover_service("story-service", version_constraint="v2.0.0", environment="production")
        """
        if not self.consul_client:
            logger.warning("Consul client not available - returning empty service list")
            return []

        try:
            # Query Consul catalog for all services matching base name
            # Consul stores versioned services as "service-name:version"
            _, services = self.consul_client.catalog.services()

            matching_services = []
            for svc_name in services.keys():
                # Extract base name and version from "service-name:version" format
                if ":" in svc_name:
                    base_name, version = svc_name.split(":", 1)
                    if base_name == service_name:
                        # Check version constraint
                        if version_constraint is None or self._matches_version_constraint(version, version_constraint):
                            matching_services.append(svc_name)
                elif svc_name == service_name:
                    # Service registered without version
                    if version_constraint is None:
                        matching_services.append(svc_name)

            logger.info(f"Found {len(matching_services)} services matching '{service_name}' with constraint '{version_constraint}'")

            # Get instances for each matching service
            instances = []
            for svc_name in matching_services:
                svc_instances = self._get_service_instances(
                    svc_name,
                    environment=environment,
                    passing_only=passing_only
                )
                instances.extend(svc_instances)

            return instances

        except Exception as e:
            logger.error(f"Failed to discover services: {e}")
            return []

    def _get_service_instances(
        self,
        service_name: str,
        environment: Optional[str] = None,
        passing_only: bool = True
    ) -> List[Dict[str, Any]]:
        """Get instances for a specific service (internal helper)"""
        try:
            # Query service health
            _, instances = self.consul_client.health.service(
                service_name,
                passing=passing_only
            )

            result = []
            for instance in instances:
                service_info = instance.get("Service", {})
                tags = service_info.get("Tags", [])

                # Filter by environment if specified
                if environment:
                    env_tags = [t for t in tags if t.startswith(f"environment:{environment}")]
                    if not env_tags:
                        continue  # Skip this instance

                # Extract version from tags
                version = None
                for tag in tags:
                    if tag.startswith("version:"):
                        version = tag.split(":", 1)[1]
                        break

                result.append({
                    "service_name": service_name,
                    "address": service_info.get("Address"),
                    "port": service_info.get("Port"),
                    "version": version,
                    "tags": tags,
                    "meta": service_info.get("Meta", {}),
                    "node": instance.get("Node", {}).get("Node")
                })

            return result

        except Exception as e:
            logger.error(f"Failed to get instances for {service_name}: {e}")
            return []

    def _matches_version_constraint(self, version: str, constraint: str) -> bool:
        """
        Check if version matches constraint

        Supports:
        - Exact match: "v1.0.0"
        - Greater than: ">v1.0.0"
        - Greater than or equal: ">=v1.0.0"
        - Less than: "<v2.0.0"
        - Less than or equal: "<=v2.0.0"
        - Range: ">=v1.0.0 <v2.0.0"

        Args:
            version: Version string (e.g., "v1.0.0")
            constraint: Constraint expression

        Returns:
            True if version matches constraint
        """
        # Parse version (strip 'v' prefix if present)
        version_clean = version.lstrip('v')
        version_tuple = self._parse_version(version_clean)

        # Parse constraint (can have multiple parts like ">=v1.0.0 <v2.0.0")
        constraint_parts = constraint.split()

        for i in range(0, len(constraint_parts)):
            part = constraint_parts[i]

            # Extract operator and version
            if part.startswith(">="):
                operator = ">="
                constraint_version = part[2:].lstrip('v')
            elif part.startswith("<="):
                operator = "<="
                constraint_version = part[2:].lstrip('v')
            elif part.startswith(">"):
                operator = ">"
                constraint_version = part[1:].lstrip('v')
            elif part.startswith("<"):
                operator = "<"
                constraint_version = part[1:].lstrip('v')
            elif part.startswith("v") or part[0].isdigit():
                # Exact version
                operator = "="
                constraint_version = part.lstrip('v')
            else:
                continue  # Skip non-version parts

            constraint_tuple = self._parse_version(constraint_version)

            # Compare versions
            if not self._compare_versions(version_tuple, operator, constraint_tuple):
                return False

        return True

    def _parse_version(self, version: str) -> Tuple[int, int, int]:
        """
        Parse version string into tuple (major, minor, patch)

        Args:
            version: Version string (e.g., "1.0.0" or "2.1.3-beta")

        Returns:
            Tuple of (major, minor, patch)
        """
        # Extract numeric version (ignore pre-release and build metadata)
        version_match = re.match(r'(\d+)\.(\d+)\.(\d+)', version)
        if version_match:
            major, minor, patch = version_match.groups()
            return (int(major), int(minor), int(patch))
        else:
            logger.warning(f"Invalid version format: {version}, defaulting to (0, 0, 0)")
            return (0, 0, 0)

    def _compare_versions(
        self,
        version: Tuple[int, int, int],
        operator: str,
        constraint: Tuple[int, int, int]
    ) -> bool:
        """
        Compare two version tuples with operator

        Args:
            version: Version tuple to check
            operator: Comparison operator (=, >, >=, <, <=)
            constraint: Constraint version tuple

        Returns:
            True if version satisfies constraint
        """
        if operator == "=":
            return version == constraint
        elif operator == ">":
            return version > constraint
        elif operator == ">=":
            return version >= constraint
        elif operator == "<":
            return version < constraint
        elif operator == "<=":
            return version <= constraint
        else:
            logger.warning(f"Unknown operator: {operator}")
            return False

    def get_service_url(
        self,
        service_name: str,
        version_constraint: Optional[str] = None,
        environment: Optional[str] = None,
        protocol: str = "http"
    ) -> Optional[str]:
        """
        Get URL for a service instance (load balanced if multiple instances)

        Args:
            service_name: Base service name
            version_constraint: SemVer constraint
            environment: Filter by environment
            protocol: URL protocol (http, https)

        Returns:
            Service URL (e.g., "http://story-service-host:8000") or None if not found

        Examples:
            # Get URL for any story-service v1.x.x instance
            url = get_service_url("story-service", version_constraint=">=v1.0.0 <v2.0.0")

            # Get URL for story-service v2.0.0 in production
            url = get_service_url("story-service", version_constraint="v2.0.0", environment="production")
        """
        instances = self.discover_service(
            service_name=service_name,
            version_constraint=version_constraint,
            environment=environment,
            passing_only=True
        )

        if not instances:
            logger.warning(f"No instances found for {service_name} with constraint {version_constraint}")
            return None

        # Simple round-robin: pick first healthy instance
        # In production, use proper load balancing library
        instance = instances[0]

        url = f"{protocol}://{instance['address']}:{instance['port']}"
        logger.info(f"Resolved {service_name} to {url} (version: {instance['version']})")

        return url


def get_service_discovery() -> ServiceDiscovery:
    """
    Factory function to create ServiceDiscovery instance

    Returns:
        ServiceDiscovery instance connected to Consul
    """
    return ServiceDiscovery(
        consul_host=os.getenv("CONSUL_HOST", "consul"),
        consul_port=int(os.getenv("CONSUL_PORT", "8500"))
    )


# Convenience functions

def discover_service(
    service_name: str,
    version_constraint: Optional[str] = None,
    environment: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to discover services

    Args:
        service_name: Base service name (e.g., "story-service")
        version_constraint: SemVer constraint (e.g., ">=v1.0.0 <v2.0.0")
        environment: Filter by environment

    Returns:
        List of service instances

    Examples:
        # Get all story-service v1.x.x instances
        instances = discover_service("story-service", ">=v1.0.0 <v2.0.0")

        # Get payment-service v2.0.0 instances in production
        instances = discover_service("payment-service", "v2.0.0", "production")
    """
    sd = get_service_discovery()
    return sd.discover_service(service_name, version_constraint, environment)


def get_service_url(
    service_name: str,
    version_constraint: Optional[str] = None,
    environment: Optional[str] = None
) -> Optional[str]:
    """
    Convenience function to get service URL

    Args:
        service_name: Base service name
        version_constraint: SemVer constraint
        environment: Filter by environment

    Returns:
        Service URL or None

    Examples:
        # Get URL for story-service v1.x.x
        url = get_service_url("story-service", ">=v1.0.0 <v2.0.0")

        # Call the service
        import requests
        response = requests.get(f"{url}/stories/")
    """
    sd = get_service_discovery()
    return sd.get_service_url(service_name, version_constraint, environment)
