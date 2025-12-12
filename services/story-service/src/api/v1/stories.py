"""
Story Service API v1 - Backward Compatibility Layer
Maintains original API contract for legacy mobile apps

Key differences from v2:
- StoryList uses 'stories' (not 'data')
- Story uses 'content' (not 'body')
- No pagination metadata object
- No search endpoint
- No metadata field
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from lib_logging.logger import get_logger_with_trace
from ..v2.stories import SAMPLE_STORIES_V2, StoryV2

router = APIRouter(prefix="/v1", tags=["Stories v1"])


# V1 Data Models (original contract)
class Story(BaseModel):
    """Story model v1 - original format"""
    id: int
    title: str
    content: str = Field(..., description="Story content")
    age_range: str = Field(..., description="Target age range (e.g., '3-5', '6-8')")
    moral_lesson: Optional[str] = None
    created_at: Optional[str] = None


class StoryList(BaseModel):
    """List of stories v1 - original format"""
    stories: List[Story] = Field(..., description="List of stories")
    total: int


def v2_to_v1_story(story_v2: StoryV2) -> Story:
    """
    Convert v2 Story to v1 Story (compatibility layer)
    Renames 'body' back to 'content' and removes metadata
    """
    return Story(
        id=story_v2.id,
        title=story_v2.title,
        content=story_v2.body,  # Map v2 'body' to v1 'content'
        age_range=story_v2.age_range,
        moral_lesson=story_v2.moral_lesson,
        created_at=story_v2.created_at
    )


@router.get("/stories", response_model=StoryList)
async def list_stories_v1(
    request: Request,
    age_range: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List all stories (v1 - backward compatible)

    Uses original v1 contract:
    - Returns 'stories' array (not 'data')
    - No pagination metadata object
    """
    trace_id = getattr(request.state, "trace_id", None)
    logger = get_logger_with_trace(__name__, trace_id=trace_id)

    logger.info(
        "Listing stories (v1 compatibility)",
        extra={"age_range": age_range, "limit": limit, "offset": offset}
    )

    # Use v2 data source but convert to v1 format
    stories_v2 = SAMPLE_STORIES_V2
    if age_range:
        stories_v2 = [s for s in stories_v2 if s.age_range == age_range]

    # Apply pagination
    total = len(stories_v2)
    stories_v2 = stories_v2[offset:offset + limit]

    # Convert to v1 format
    stories_v1 = [v2_to_v1_story(s) for s in stories_v2]

    logger.info(f"Returning {len(stories_v1)} stories (v1, total: {total})")

    return StoryList(stories=stories_v1, total=total)


@router.get("/stories/{story_id}", response_model=Story)
async def get_story_v1(request: Request, story_id: int):
    """
    Get a specific story by ID (v1 - backward compatible)

    Uses original v1 contract:
    - Returns 'content' field (not 'body')
    - No metadata field
    """
    trace_id = getattr(request.state, "trace_id", None)
    logger = get_logger_with_trace(__name__, trace_id=trace_id)

    logger.info(f"Fetching story (v1 compatibility)", extra={"story_id": story_id})

    # Find story from v2 data source
    story_v2 = next((s for s in SAMPLE_STORIES_V2 if s.id == story_id), None)

    if not story_v2:
        logger.warning(f"Story not found (v1)", extra={"story_id": story_id})
        raise HTTPException(status_code=404, detail=f"Story {story_id} not found")

    # Convert to v1 format
    story_v1 = v2_to_v1_story(story_v2)

    logger.info(f"Story found (v1)", extra={"story_id": story_id, "title": story_v1.title})

    return story_v1


@router.post("/stories/{story_id}/personalize")
async def personalize_story_v1(
    request: Request,
    story_id: int,
    child_name: str,
    child_photo_url: Optional[str] = None
):
    """
    Personalize a story with child's name and photo (v1 - backward compatible)
    """
    trace_id = getattr(request.state, "trace_id", None)
    logger = get_logger_with_trace(__name__, trace_id=trace_id)

    logger.info(
        "Personalizing story (v1 compatibility)",
        extra={"story_id": story_id, "child_name": child_name}
    )

    # Find story from v2 data source
    story_v2 = next((s for s in SAMPLE_STORIES_V2 if s.id == story_id), None)

    if not story_v2:
        raise HTTPException(status_code=404, detail=f"Story {story_id} not found")

    # Personalize content (simple replacement for MVP)
    # Use v2 'body' field but return as 'content' for v1
    personalized_content = story_v2.body.replace("little", child_name)

    logger.info(f"Story personalized successfully (v1)", extra={"story_id": story_id})

    return {
        "story_id": story_id,
        "title": story_v2.title,
        "personalized_content": personalized_content,  # v1 uses 'content'
        "child_name": child_name,
        "trace_id": trace_id
        # No metadata in v1 response
    }
