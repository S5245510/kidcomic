"""
API v1 - Compatibility layer for legacy clients
Maintains backward compatibility with original API contract
"""
from .stories import router

__all__ = ["router"]
