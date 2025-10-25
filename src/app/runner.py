"""Main crawler runner."""
import asyncio
from datetime import datetime, timezone
from urllib.parse import urlparse
import structlog

from .config import settings
from .db import get_connection
from .models import CrawlRun, Url, FetchError
from .queue import enqueue_if_new, pop_next
from .url_checker import RobotsCache
from .fetcher import fetch_url
from .parser import parse_and_extract_links, normalize_url
from .storage import Storage

logger = structlog.get_logger()


class Runner:
    def __init__(self, run_id: str, seed_url: str):
        """Initialize crawler run."""
        self.run_id = run_id
        self.seed_url = seed_url
        self.robots_cache = RobotsCache()
        self.storage = Storage()
        self.visited_urls = set()
        
    async def start(self):
        """Start crawl run."""
        async with get_connection() as conn:
            # Initialize storage
            await self.storage.ensure_bucket()
            
            # Create crawl run
            seed_domain = urlparse(self.seed_url).netloc
            await conn.execute(
                """
                INSERT INTO crawl_runs (id, seed_domain)
                VALUES ($1, $2)
                """,
                self.run_id,
                seed_domain,
            )
            
            # Add seed URL
            url_id = await conn.fetchval(
                """
                INSERT INTO urls (url, normalized_url, domain, crawl_run_id)
                VALUES ($1, $2, $3, $4)
                RETURNING id
                """,
                self.seed_url,
                normalize_url(self.seed_url),
                seed_domain,
                self.run_id,
            )
            await enqueue_if_new(conn, url_id, self.run_id)
            
            # Main crawl loop
            while True:
                # Get next URL for each domain respecting robots
                domains = await conn.fetch(
                    "SELECT DISTINCT domain FROM urls WHERE crawl_run_id = $1",
                    self.run_id,
                )
                
                if not domains:
                    break
                    
                for row in domains:
                    domain = row["domain"]
                    
                    # Check robots.txt and crawl delay
                    crawl_delay = await self.robots_cache.get_crawl_delay(domain, conn)
                    
                    # Get next URL for this domain
                    queue_item = await pop_next(conn, domain)
                    if not queue_item:
                        continue
                        
                    # Get URL details
                    url_row = await conn.fetchrow(
                        "SELECT * FROM urls WHERE id = $1",
                        queue_item.url_id,
                    )
                    url = url_row["url"]
                    
                    # Check if allowed by robots.txt
                    if not await self.robots_cache.allowed_to_fetch(domain, url, conn):
                        logger.info("skipping_robots_disallowed", url=url)
                        continue
                    
                    # Fetch URL
                    status_code, content, content_type = await fetch_url(url)
                    
                    # Record fetch attempt
                    if status_code == 0:
                        # Error
                        await conn.execute(
                            """
                            UPDATE urls
                            SET status = 'error',
                                fetch_attempts = fetch_attempts + 1,
                                last_seen = now()
                            WHERE id = $1
                            """,
                            queue_item.url_id,
                        )
                        await conn.execute(
                            """
                            INSERT INTO fetch_errors (url_id, error_type, error_msg)
                            VALUES ($1, $2, $3)
                            """,
                            queue_item.url_id,
                            "connection_error",
                            "Failed to connect",
                        )
                        continue
                    
                    # Store HTML content if available
                    stored_key = None
                    if content:
                        stored_key = await self.storage.store_html(
                            self.run_id,
                            url,
                            content,
                        )
                    
                    # Update URL record
                    await conn.execute(
                        """
                        UPDATE urls
                        SET status = 'fetched',
                            http_status = $1,
                            fetch_attempts = fetch_attempts + 1,
                            content_type = $2,
                            content_size = $3,
                            stored_object_key = $4,
                            last_seen = now()
                        WHERE id = $1
                        """,
                        queue_item.url_id,
                        status_code,
                        content_type,
                        len(content) if content else None,
                        stored_key,
                    )
                    
                    # Parse links if HTML content available
                    if content and content_type and "text/html" in content_type.lower():
                        links = parse_and_extract_links(content.decode(), url)
                        for link in links:
                            link_domain = urlparse(link).netloc
                            # Add URL if new
                            link_id = await conn.fetchval(
                                """
                                INSERT INTO urls (url, normalized_url, domain, crawl_run_id)
                                VALUES ($1, $2, $3, $4)
                                ON CONFLICT (normalized_url) DO UPDATE
                                SET last_seen = now()
                                RETURNING id
                                """,
                                link,
                                normalize_url(link),
                                link_domain,
                                self.run_id,
                            )
                            # Add to queue if same domain
                            if link_domain == domain:
                                await enqueue_if_new(conn, link_id, self.run_id)
                    
                    # Respect crawl delay
                    await asyncio.sleep(crawl_delay)
            
            # Update crawl run stats
            stats = await conn.fetchrow(
                """
                SELECT
                    count(*) FILTER (WHERE status = 'fetched') as total_fetched,
                    count(*) as total_discovered
                FROM urls
                WHERE crawl_run_id = $1
                """,
                self.run_id,
            )
            await conn.execute(
                """
                UPDATE crawl_runs
                SET finished_at = now(),
                    total_fetched = $1,
                    total_discovered = $2
                WHERE id = $3
                """,
                stats["total_fetched"],
                stats["total_discovered"],
                self.run_id,
            )