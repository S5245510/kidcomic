"""
Story Service API v2
Breaking changes from v1:
- StoryList uses 'data' instead of 'stories'
- Story uses 'body' instead of 'content'
- Added pagination metadata
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from lib_logging.logger import get_logger_with_trace

router = APIRouter(prefix="/v2", tags=["Stories v2"])


# V2 Data Models (with breaking changes)
class StoryV2(BaseModel):
    """Story model v2 - uses 'body' instead of 'content'"""
    id: int
    title: str
    body: str = Field(..., description="Story content (renamed from 'content' in v1)")
    age_range: str = Field(..., description="Target age range (e.g., '3-5', '6-8')")
    moral_lesson: Optional[str] = None
    created_at: Optional[str] = None
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata (new in v2)")


class PaginationMetadata(BaseModel):
    """Pagination metadata (new in v2)"""
    total: int
    limit: int
    offset: int
    has_more: bool


class StoryListV2(BaseModel):
    """List of stories v2 - uses 'data' instead of 'stories', added pagination"""
    data: List[StoryV2] = Field(..., description="List of stories (renamed from 'stories' in v1)")
    pagination: PaginationMetadata = Field(..., description="Pagination info (new in v2)")


# Sample data (shared with v1)
# In production, this would come from database
SAMPLE_STORIES_V2 = [
    StoryV2(
        id=1,
        title="The Brave Little Turtle",
        body="Once upon a time, there was a brave little turtle who lived by the sea...",
        age_range="3-5",
        moral_lesson="Courage comes in all sizes",
        created_at="2024-01-01T00:00:00Z",
        metadata={"theme": "courage", "characters": ["turtle"]}
    ),
    StoryV2(
        id=2,
        title="The Magic Paintbrush",
        body="In a small village, there lived a young artist who discovered a magic paintbrush...",
        age_range="6-8",
        moral_lesson="Use your talents to help others",
        created_at="2024-01-02T00:00:00Z",
        metadata={"theme": "generosity", "characters": ["artist"]}
    ),
    StoryV2(
        id=3,
        title="The Friendly Dragon",
        body="High in the mountains lived a dragon who just wanted to make friends...",
        age_range="4-6",
        moral_lesson="Don't judge by appearances",
        created_at="2024-01-03T00:00:00Z",
        metadata={"theme": "acceptance", "characters": ["dragon"]}
    )
]


@router.get("/stories", response_model=StoryListV2)
async def list_stories_v2(
    request: Request,
    age_range: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """
    List all stories (v2)

    Breaking changes from v1:
    - Response uses 'data' instead of 'stories'
    - Added 'pagination' metadata object
    """
    trace_id = getattr(request.state, "trace_id", None)
    logger = get_logger_with_trace(__name__, trace_id=trace_id)

    logger.info(
        "Listing stories (v2)",
        extra={"age_range": age_range, "limit": limit, "offset": offset}
    )

    # Filter by age_range if provided
    stories = SAMPLE_STORIES_V2
    if age_range:
        stories = [s for s in stories if s.age_range == age_range]

    # Calculate pagination
    total = len(stories)
    paginated_stories = stories[offset:offset + limit]
    has_more = (offset + limit) < total

    pagination = PaginationMetadata(
        total=total,
        limit=limit,
        offset=offset,
        has_more=has_more
    )

    logger.info(f"Returning {len(paginated_stories)} stories (v2, total: {total})")

    return StoryListV2(data=paginated_stories, pagination=pagination)


@router.get("/stories/{story_id}", response_model=StoryV2)
async def get_story_v2(request: Request, story_id: int):
    """
    Get a specific story by ID (v2)

    Breaking changes from v1:
    - Story uses 'body' instead of 'content'
    - Added 'metadata' field
    """
    trace_id = getattr(request.state, "trace_id", None)
    logger = get_logger_with_trace(__name__, trace_id=trace_id)

    logger.info(f"Fetching story (v2)", extra={"story_id": story_id})

    # Find story
    story = next((s for s in SAMPLE_STORIES_V2 if s.id == story_id), None)

    if not story:
        logger.warning(f"Story not found (v2)", extra={"story_id": story_id})
        raise HTTPException(status_code=404, detail=f"Story {story_id} not found")

    logger.info(f"Story found (v2)", extra={"story_id": story_id, "title": story.title})

    return story


@router.get("/stories/search", response_model=StoryListV2)
async def search_stories_v2(
    request: Request,
    query: str,
    limit: int = 100,
    offset: int = 0
):
    """
    Search stories by title or content (new in v2)
    """
    trace_id = getattr(request.state, "trace_id", None)
    logger = get_logger_with_trace(__name__, trace_id=trace_id)

    logger.info(f"Searching stories (v2)", extra={"query": query})

    # Simple search implementation
    query_lower = query.lower()
    stories = [
        s for s in SAMPLE_STORIES_V2
        if query_lower in s.title.lower() or query_lower in s.body.lower()
    ]

    # Calculate pagination
    total = len(stories)
    paginated_stories = stories[offset:offset + limit]
    has_more = (offset + limit) < total

    pagination = PaginationMetadata(
        total=total,
        limit=limit,
        offset=offset,
        has_more=has_more
    )

    logger.info(f"Found {len(paginated_stories)} stories (v2, total: {total})")

    return StoryListV2(data=paginated_stories, pagination=pagination)


@router.post("/stories/{story_id}/personalize")
async def personalize_story_v2(
    request: Request,
    story_id: int,
    child_name: str,
    child_photo_url: Optional[str] = None
):
    """
    Personalize a story with child's name and photo (v2)
    """
    trace_id = getattr(request.state, "trace_id", None)
    logger = get_logger_with_trace(__name__, trace_id=trace_id)

    logger.info(
        "Personalizing story (v2)",
        extra={"story_id": story_id, "child_name": child_name}
    )

    # Find story
    story = next((s for s in SAMPLE_STORIES_V2 if s.id == story_id), None)

    if not story:
        raise HTTPException(status_code=404, detail=f"Story {story_id} not found")

    # Personalize content (simple replacement for MVP)
    personalized_body = story.body.replace("little", child_name)

    logger.info(f"Story personalized successfully (v2)", extra={"story_id": story_id})

    return {
        "story_id": story_id,
        "title": story.title,
        "personalized_body": personalized_body,  # v2 uses 'body'
        "child_name": child_name,
        "trace_id": trace_id,
        "metadata": story.metadata  # Include metadata in v2
    }
