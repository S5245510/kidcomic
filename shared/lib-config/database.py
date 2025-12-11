"""
Database Connection Manager
PostgreSQL connection pooling with health checks
"""

import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Database connection manager with pooling

    Minimal implementation for Phase 3 MVP
    Full implementation with SQLAlchemy and connection pooling will be in Phase 2 completion
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 5432,
        database: str = "kidcomic",
        user: str = "kidcomic",
        password: str = "",
        pool_size: int = 10,
        max_overflow: int = 20
    ):
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self._connection_string = self._build_connection_string()

        logger.info(
            f"DatabaseManager initialized (stub mode) - {self.database} at {self.host}:{self.port}"
        )

    def _build_connection_string(self) -> str:
        """Build PostgreSQL connection string"""
        return (
            f"postgresql://{self.user}:{self.password}@"
            f"{self.host}:{self.port}/{self.database}"
        )

    def get_connection_string(self) -> str:
        """Get the database connection string"""
        return self._connection_string

    def check_health(self) -> bool:
        """
        Check if database connection is healthy

        Returns:
            True if database is accessible, False otherwise
        """
        # In stub mode, always return True
        # TODO: Implement actual database ping in Phase 2
        # This would use SQLAlchemy:
        # engine = create_engine(self._connection_string)
        # try:
        #     with engine.connect() as conn:
        #         conn.execute("SELECT 1")
        #     return True
        # except Exception:
        #     return False

        logger.debug("Database health check (stub) - always returns True")
        return True

    def close(self) -> None:
        """Close database connections"""
        logger.info("Database connections closed (stub)")
        # TODO: Implement actual connection pool cleanup in Phase 2


def get_database_manager(
    service_name: str,
    config: Optional[dict] = None
) -> DatabaseManager:
    """
    Get database manager instance with configuration

    Args:
        service_name: Name of the service (for database naming)
        config: Optional configuration override

    Returns:
        DatabaseManager instance
    """
    if config is None:
        config = {}

    # Get configuration from environment or provided config
    host = config.get("host") or os.getenv("POSTGRES_HOST", "localhost")
    port = int(config.get("port") or os.getenv("POSTGRES_PORT", "5432"))
    database = config.get("database") or os.getenv("POSTGRES_DB", service_name)
    user = config.get("user") or os.getenv("POSTGRES_USER", "kidcomic")
    password = config.get("password") or os.getenv("POSTGRES_PASSWORD", "")

    return DatabaseManager(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
