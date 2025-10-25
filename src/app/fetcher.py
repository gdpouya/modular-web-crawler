"""URL fetcher module."""
import httpx
from typing import Optional, Tuple
import structlog

from .config import settings

logger = structlog.get_logger()


async def fetch_url(url: str) -> Tuple[int, Optional[bytes], Optional[str]]:
    """
    Fetch a URL and return (status_code, content, content_type).
    
    Args:
        url: The URL to fetch

    Returns:
        Tuple of (HTTP status code, content bytes if HTML, content type if HTML)
    """
    try:
        async with httpx.AsyncClient(
            follow_redirects=True,
            timeout=httpx.Timeout(
                connect=settings.connect_timeout,
                read=settings.read_timeout,
            ),
            headers={"User-Agent": settings.user_agent},
        ) as client:
            response = await client.get(url)
            
            content_type = response.headers.get("content-type", "").lower()
            if not content_type.startswith("text/html"):
                logger.info("skipping_non_html", url=url, content_type=content_type)
                return response.status_code, None, content_type

            content_length = len(response.content)
            if content_length > settings.max_body_size:
                logger.warning("skipping_large_body", url=url, size=content_length)
                return response.status_code, None, content_type

            return response.status_code, response.content, content_type

    except httpx.RequestError as e:
        logger.error("fetch_failed", url=url, error=str(e))
        return 0, None, None