"""URL queue management."""
from datetime import datetime, timezone
import asyncpg
from typing import Optional

from .models import QueueItem
from .db import get_connection


async def enqueue_if_new(conn: asyncpg.Connection, url_id: int, crawl_run_id: str, priority: int = 0) -> Optional[int]:
    """Add URL to queue if not already present. Returns queue item ID if added."""
    query = """
    INSERT INTO queue (url_id, priority, enqueued_at, next_fetch_at)
    SELECT $1, $2, now(), now()
    WHERE NOT EXISTS (
        SELECT 1 FROM queue WHERE url_id = $1
    )
    RETURNING id;
    """
    result = await conn.fetchval(query, url_id, priority)
    return result


async def pop_next(conn: asyncpg.Connection, domain: str) -> Optional[QueueItem]:
    """Get next URL to fetch for a domain, respecting crawl delay."""
    query = """
    WITH next_url AS (
        SELECT q.id, q.url_id, q.priority, q.enqueued_at, q.next_fetch_at
        FROM queue q
        JOIN urls u ON u.id = q.url_id
        WHERE u.domain = $1
          AND q.next_fetch_at <= now()
        ORDER BY q.priority DESC, q.enqueued_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    )
    DELETE FROM queue
    WHERE id = (SELECT id FROM next_url)
    RETURNING *;
    """
    row = await conn.fetchrow(query, domain)
    if row:
        return QueueItem(
            id=row["id"],
            url_id=row["url_id"],
            priority=row["priority"],
            enqueued_at=row["enqueued_at"],
            next_fetch_at=row["next_fetch_at"],
        )
    return None


async def get_queue_length(conn: asyncpg.Connection) -> int:
    """Get total number of URLs in queue."""
    return await conn.fetchval("SELECT count(*) FROM queue;")