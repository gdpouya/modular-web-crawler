"""Database connection and query helpers."""
import asyncpg
import contextlib
from typing import AsyncGenerator

from .config import settings


_pool: asyncpg.Pool | None = None


async def get_pool() -> asyncpg.Pool:
    """Create and return a connection pool."""
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(settings.get_postgres_dsn())
    return _pool


@contextlib.asynccontextmanager
async def get_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a database connection from the pool."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


async def init_db(conn: asyncpg.Connection) -> None:
    """Initialize database schema."""
    migration_path = "migrations/V001_init.sql"
    with open(migration_path) as f:
        sql = f.read()
    await conn.execute(sql)