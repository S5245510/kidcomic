"""
Docker Secrets Reader
Read secrets from Docker Swarm secrets or Kubernetes secrets
"""

import os
from pathlib import Path
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class SecretsManager:
    """
    Secrets manager for Docker/Kubernetes secrets

    Minimal implementation for Phase 3 MVP
    Reads secrets from files mounted at /run/secrets/ (Docker Swarm)
    or environment variables as fallback
    """

    def __init__(self, secrets_dir: str = "/run/secrets"):
        self.secrets_dir = Path(secrets_dir)
        logger.info(f"SecretsManager initialized - secrets dir: {self.secrets_dir}")

    def get_secret(self, secret_name: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret value

        First checks Docker secrets directory, then environment variables

        Args:
            secret_name: Name of the secret
            default: Default value if secret not found

        Returns:
            Secret value or default
        """
        # Try to read from Docker secrets
        secret_file = self.secrets_dir / secret_name
        if secret_file.exists():
            try:
                with open(secret_file, 'r') as f:
                    value = f.read().strip()
                logger.debug(f"Secret '{secret_name}' loaded from file")
                return value
            except Exception as e:
                logger.error(f"Failed to read secret '{secret_name}' from file: {e}")

        # Fallback to environment variable
        env_secret = os.getenv(secret_name.upper())
        if env_secret:
            logger.debug(f"Secret '{secret_name}' loaded from environment")
            return env_secret

        logger.warning(f"Secret '{secret_name}' not found, using default")
        return default

    def require_secret(self, secret_name: str) -> str:
        """
        Get required secret, raise error if missing

        Args:
            secret_name: Name of the secret

        Returns:
            Secret value

        Raises:
            ValueError: If secret not found
        """
        value = self.get_secret(secret_name)
        if value is None:
            raise ValueError(f"Required secret '{secret_name}' not found")
        return value


# Global secrets manager instance
_secrets_manager: Optional[SecretsManager] = None


def get_secrets_manager() -> SecretsManager:
    """
    Get global secrets manager instance

    Returns:
        SecretsManager instance
    """
    global _secrets_manager
    if _secrets_manager is None:
        secrets_dir = os.getenv("SECRETS_DIR", "/run/secrets")
        _secrets_manager = SecretsManager(secrets_dir)
    return _secrets_manager


def get_secret(secret_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Convenience function to get a secret

    Args:
        secret_name: Name of the secret
        default: Default value if not found

    Returns:
        Secret value or default
    """
    manager = get_secrets_manager()
    return manager.get_secret(secret_name, default)
