import os
import sys
import time
import subprocess
import asyncio
from pathlib import Path

import asyncpg
import pytest

# ensure src is on path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from app.runner import Runner


@pytest.mark.asyncio
async def test_crawl_against_static_server():
    # bring up docker-compose stack (db, minio, static_server)
    subprocess.check_call(["docker-compose", "up", "-d", "--build"])

    # wait for postgres and initialize schema
    dsn = "postgresql://crawler:crawler@localhost:5432/crawler"
    for _ in range(30):
        try:
            conn = await asyncpg.connect(dsn)
            with open(ROOT / "migrations/V001_init.sql") as f:
                sql = f.read()
            await conn.execute(sql)
            await conn.close()
            break
        except Exception:
            time.sleep(1)
    else:
        pytest.skip("Postgres did not become ready")

    # ensure our pool is initialized
    import app.db as db
    await db.get_pool()

    # run the crawler against the static server
    seed = "http://localhost:8000/index.html"
    run_id = "test-run-1"
    runner = Runner(run_id=run_id, seed_url=seed)
    await runner.start()

    # verify DB entries
    pool = await asyncpg.create_pool(dsn)
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT url FROM urls WHERE crawl_run_id=$1", run_id)
        urls = [r["url"] for r in rows]
        assert any("index.html" in u for u in urls)
        assert any("page1.html" in u for u in urls)

    await pool.close()
