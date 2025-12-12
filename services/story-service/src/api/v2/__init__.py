"""
API v2 - Latest version with enhanced features
Breaking changes from v1:
- StoryList uses 'data' instead of 'stories'
- Story uses 'body' instead of 'content'
- Added pagination metadata
"""
from .stories import router

__all__ = ["router"]
