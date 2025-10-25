"""URL checker for robots.txt compliance."""
from datetime import datetime, timezone
import httpx
import urllib.robotparser
from typing import Optional, Dict
import asyncpg

from .config import settings
from .models import Domain


class RobotsCache:
    def __init__(self):
        self._cache: Dict[str, urllib.robotparser.RobotFileParser] = {}

    async def fetch_robots_txt(self, domain: str, conn: asyncpg.Connection) -> Optional[str]:
        """Fetch robots.txt for a domain and store in database."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"http://{domain}/robots.txt"
                resp = await client.get(url)
                if resp.status_code == 200:
                    robots_txt = resp.text
                    await conn.execute(
                        """
                        INSERT INTO domains (domain, robots_txt, robots_fetched_at)
                        VALUES ($1, $2, now())
                        ON CONFLICT (domain) DO UPDATE SET
                            robots_txt = $2,
                            robots_fetched_at = now()
                        """,
                        domain,
                        robots_txt,
                    )
                    return robots_txt
        except Exception:
            pass
        return None

    async def get_parser(self, domain: str, conn: asyncpg.Connection) -> urllib.robotparser.RobotFileParser:
        """Get RobotFileParser for domain, fetching robots.txt if needed."""
        if domain not in self._cache:
            row = await conn.fetchrow("SELECT * FROM domains WHERE domain = $1", domain)
            if not row or not row["robots_txt"]:
                robots_txt = await self.fetch_robots_txt(domain, conn)
            else:
                robots_txt = row["robots_txt"]

            parser = urllib.robotparser.RobotFileParser()
            if robots_txt:
                parser.parse(robots_txt.splitlines())
            self._cache[domain] = parser

        return self._cache[domain]

    async def allowed_to_fetch(self, domain: str, url: str, conn: asyncpg.Connection) -> bool:
        """Check if URL is allowed by robots.txt."""
        parser = await self.get_parser(domain, conn)
        return parser.can_fetch(settings.user_agent, url)

    async def get_crawl_delay(self, domain: str, conn: asyncpg.Connection) -> float:
        """Get crawl delay for domain from robots.txt or use default."""
        parser = await self.get_parser(domain, conn)
        delay = parser.crawl_delay(settings.user_agent)
        if delay is None:
            delay = settings.default_crawl_delay
        
        # Update domain crawl delay
        await conn.execute(
            """
            INSERT INTO domains (domain, crawl_delay_seconds)
            VALUES ($1, $2)
            ON CONFLICT (domain) DO UPDATE SET
                crawl_delay_seconds = $2
            """,
            domain,
            delay,
        )
        return delay