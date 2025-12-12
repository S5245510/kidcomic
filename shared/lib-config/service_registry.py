"""
Service Registry Library
Consul service registration and discovery
"""

import os
import socket
from typing import Optional, List, Dict, Any
import logging

try:
    import consul
    CONSUL_AVAILABLE = True
except ImportError:
    CONSUL_AVAILABLE = False
    logging.warning("python-consul not installed - service registry will run in stub mode")

logger = logging.getLogger(__name__)


class ServiceRegistry:
    """
    Service registry client for Consul
    Handles service registration, deregistration, and health checks
    """

    def __init__(self, consul_host: str = "consul", consul_port: int = 8500):
        self.consul_host = consul_host
        self.consul_port = consul_port
        self.service_id: Optional[str] = None
        self.consul_client: Optional[Any] = None

        if CONSUL_AVAILABLE:
            try:
                self.consul_client = consul.Consul(host=consul_host, port=consul_port)
                # Test connection
                self.consul_client.agent.self()
                logger.info(f"ServiceRegistry initialized - Connected to Consul at {consul_host}:{consul_port}")
            except Exception as e:
                logger.error(f"Failed to connect to Consul at {consul_host}:{consul_port}: {e}")
                self.consul_client = None
        else:
            logger.warning(f"ServiceRegistry initialized (stub mode) - Consul client not available")

    def register(
        self,
        service_name: str,
        service_port: int,
        service_address: Optional[str] = None,
        health_check_interval: str = "10s",
        health_check_timeout: str = "5s",
        health_check_path: str = "/health",
        tags: Optional[List[str]] = None,
        meta: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Register service with Consul

        Args:
            service_name: Name of the service
            service_port: Port the service listens on
            service_address: Service address (default: auto-detect)
            health_check_interval: How often to check health
            health_check_timeout: Health check timeout
            health_check_path: Path for HTTP health check
            tags: Service tags for filtering (e.g., ['traefik.enable=true'])
            meta: Service metadata

        Returns:
            Service ID
        """
        # Auto-detect service address if not provided
        if not service_address:
            service_address = self._get_service_address()

        # Generate unique service ID
        self.service_id = f"{service_name}-{service_address}-{service_port}"

        # Default tags if not provided
        if tags is None:
            tags = []

        # Default meta if not provided
        if meta is None:
            meta = {}

        logger.info(
            f"Registering service: {service_name} at {service_address}:{service_port} "
            f"(ID: {self.service_id}, tags: {tags})"
        )

        # Register with Consul if available
        if self.consul_client:
            try:
                # Configure HTTP health check
                health_check = {
                    "http": f"http://{service_address}:{service_port}{health_check_path}",
                    "interval": health_check_interval,
                    "timeout": health_check_timeout,
                    "deregister_critical_service_after": "30s"
                }

                # Register service
                # Note: python-consul 1.1.0 doesn't support 'meta' parameter
                # Metadata is stored in tags instead
                self.consul_client.agent.service.register(
                    name=service_name,
                    service_id=self.service_id,
                    address=service_address,
                    port=service_port,
                    tags=tags,
                    check=health_check
                )

                logger.info(f"Successfully registered {service_name} with Consul (ID: {self.service_id})")
            except Exception as e:
                logger.error(f"Failed to register service with Consul: {e}")
                raise
        else:
            logger.warning(f"Consul client not available - service registration skipped")

        return self.service_id

    def deregister(self, service_id: Optional[str] = None) -> None:
        """
        Deregister service from Consul

        Args:
            service_id: Service ID (uses registered ID if not provided)
        """
        sid = service_id or self.service_id
        if not sid:
            logger.warning("No service ID to deregister")
            return

        logger.info(f"Deregistering service: {sid}")

        # Deregister from Consul if available
        if self.consul_client:
            try:
                self.consul_client.agent.service.deregister(sid)
                logger.info(f"Successfully deregistered {sid} from Consul")
            except Exception as e:
                logger.error(f"Failed to deregister service from Consul: {e}")
        else:
            logger.warning(f"Consul client not available - service deregistration skipped")

    def _get_service_address(self) -> str:
        """Get service address (hostname or IP)"""
        # Try to get hostname
        hostname = os.getenv("SERVICE_HOST", socket.gethostname())
        return hostname


def register_service(
    service_name: str,
    service_port: int,
    version: str = "v0.0.1",
    environment: str = "development",
    enable_prometheus_discovery: bool = True
) -> ServiceRegistry:
    """
    Convenience function to register a service with Consul
    Per T111 [US4]: Registers service with version tags for version-aware discovery

    Note: This registers services for Consul-based service discovery, primarily
    for Prometheus scraping. Traefik routing continues to use Docker labels.

    Args:
        service_name: Name of the service (e.g., "story-service")
        service_port: Port the service listens on
        version: Service version (e.g., "v1.0.0", "v2.0.0")
        environment: Deployment environment
        enable_prometheus_discovery: Enable Prometheus service discovery tags

    Returns:
        ServiceRegistry instance (call .deregister() on shutdown)

    Examples:
        # Register story-service v1.0.0
        registry = register_service("story-service", 8000, version="v1.0.0")

        # Register story-service v2.0.0 (both can run simultaneously)
        registry = register_service("story-service", 8100, version="v2.0.0")
    """
    registry = ServiceRegistry(
        consul_host=os.getenv("CONSUL_HOST", "consul"),
        consul_port=int(os.getenv("CONSUL_PORT", "8500"))
    )

    # Version-aware service registration (T111)
    # Format: service-name:version (e.g., "story-service:v1.0.0")
    versioned_service_name = f"{service_name}:{version}"

    tags = [
        f"version:{version}",
        f"environment:{environment}",
        "traefik.enable=true"  # Enable Traefik discovery
    ]

    # Add Prometheus discovery tags if enabled
    # These are used by Prometheus Consul SD to auto-discover services
    if enable_prometheus_discovery:
        tags.extend([
            "prometheus=true",
            "metrics_path:/metrics/"
        ])

    # Note: python-consul 1.1.0 doesn't support 'meta' parameter
    # Metadata stored in tags instead for backward compatibility
    meta = {
        "version": version,
        "environment": environment,
        "metrics_path": "/metrics/",
        "prometheus_port": str(service_port),
        "service_name": service_name  # Store base service name
    }

    # Register with versioned service name
    registry.register(
        service_name=versioned_service_name,
        service_port=service_port,
        tags=tags,
        meta=meta
    )

    return registry
