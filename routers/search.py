# routers/search.py

from typing import List, Optional
import logging

from fastapi import APIRouter, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel

from services.ddg_service import search as ddg_search

logger = logging.getLogger("syne-backend")

router = APIRouter(
    prefix="/v1/search",  # ✅ Versioned route
    tags=["Search"],      # ✅ OpenAPI grouping
)


class SearchResult(BaseModel):
    title: str
    snippet: str
    url: str


@router.get(
    "",
    summary="Perform a real-time search using DuckDuckGo",
    response_model=List[SearchResult],
)
async def perform_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(5, ge=1, le=20, description="Max results to return"),
    safe: Optional[bool] = Query(True, description="Enable safe search"),
    region: Optional[str] = Query(None, description="Region code (e.g. 'in', 'us')")
) -> List[SearchResult]:
    """
    Perform a real-time search using DuckDuckGo.

    Args:
        q (str): The search query.
        limit (int): Number of results to return.
        safe (bool): Whether to enable safe search.
        region (str): Optional region code.

    Returns:
        List[SearchResult]: Search results with title, snippet, and URL.
    """
    try:
        logger.info("DDG search q=%r limit=%d safe=%s region=%s", q, limit, safe, region)
        results = await run_in_threadpool(ddg_search, q, limit, safe, region)

        if not results:
            raise HTTPException(status_code=404, detail="No results found")

        logger.info("DDG returned %d results", len(results))
        return results

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Search failed for query %r: %s", q, e)
        raise HTTPException(status_code=500, detail="Search failed")

