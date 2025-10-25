"""Database models and helper functions."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, HttpUrl


class CrawlRun(BaseModel):
    """Represents a crawl session."""
    id: str
    started_at: datetime
    finished_at: Optional[datetime] = None
    seed_domain: str
    total_fetched: int = 0
    total_discovered: int = 0


class Url(BaseModel):
    """Represents a URL with its metadata."""
    id: int
    url: HttpUrl
    normalized_url: HttpUrl
    domain: str
    first_seen: datetime
    last_seen: datetime
    status: str  # new, fetched, error
    http_status: Optional[int] = None
    fetch_attempts: int = 0
    content_type: Optional[str] = None
    content_size: Optional[int] = None
    stored_object_key: Optional[str] = None
    crawl_run_id: str


class QueueItem(BaseModel):
    """Represents a URL in the crawl queue."""
    id: int
    url_id: int
    priority: int = 0
    enqueued_at: datetime
    next_fetch_at: datetime


class FetchError(BaseModel):
    """Represents a fetch error."""
    id: int
    url_id: int
    occurred_at: datetime
    error_type: str
    error_msg: str


class Domain(BaseModel):
    """Represents domain-specific metadata."""
    domain: str
    robots_txt: Optional[str] = None
    robots_fetched_at: Optional[datetime] = None
    crawl_delay_seconds: float = 1.0