"""
Configuration Management Library
12-factor app pattern with environment variables
"""

import os
from typing import Any, Dict, Optional
from pathlib import Path


class Config:
    """Configuration manager for environment variables"""

    def __init__(self, env_file: Optional[str] = None):
        self._config: Dict[str, str] = {}
        if env_file:
            self.load_from_file(env_file)
        self.load_from_environment()

    def load_from_file(self, filepath: str) -> None:
        """Load configuration from .env file"""
        env_path = Path(filepath)
        if not env_path.exists():
            return

        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    self._config[key.strip()] = value.strip()

    def load_from_environment(self) -> None:
        """Load configuration from environment variables"""
        self._config.update(os.environ)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config.get(key, default)

    def get_int(self, key: str, default: int = 0) -> int:
        """Get configuration value as integer"""
        value = self.get(key, default)
        return int(value) if value else default

    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get configuration value as boolean"""
        value = self.get(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() in ('true', '1', 'yes', 'on')

    def require(self, key: str) -> str:
        """Get required configuration value, raise error if missing"""
        value = self.get(key)
        if value is None:
            raise ValueError(f"Required configuration '{key}' not found")
        return value


# Global configuration instance
_config: Optional[Config] = None


def load_env_config(env_file: Optional[str] = None) -> Config:
    """
    Load configuration from environment

    Args:
        env_file: Optional path to .env file

    Returns:
        Configuration instance
    """
    global _config
    _config = Config(env_file)
    return _config


def get_config() -> Config:
    """
    Get global configuration instance

    Returns:
        Configuration instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
