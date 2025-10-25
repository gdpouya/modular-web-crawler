"""Integration test for full crawler."""
import os
import pytest
import pytest_asyncio
import asyncio
import httpx
from pathlib import Path

import app.db as db
from app.runner import Runner


@pytest_asyncio.fixture
async def database():
    """Set up test database."""
    pool = await db.get_pool()
    async with pool.acquire() as conn:
        await db.init_db(conn)
        yield conn
    await pool.close()


@pytest_asyncio.fixture
async def minio():
    """Wait for MinIO to be ready."""
    async with httpx.AsyncClient() as client:
        for _ in range(30):
            try:
                r = await client.get("http://localhost:9000/minio/health/live")
                if r.status_code == 200:
                    break
            except Exception:
                await asyncio.sleep(1)
        else:
            pytest.skip("MinIO not ready")


@pytest.mark.asyncio
async def test_crawler_integration(database, minio):
    """Test full crawler against static test server."""
    # Create test files
    fixtures = Path("tests/fixtures")
    fixtures.mkdir(exist_ok=True)
    
    index_html = fixtures / "index.html"
    index_html.write_text("""
    <html>
        <body>
            <h1>Test Site</h1>
            <a href="/page1.html">Page 1</a>
            <a href="http://external.com">External</a>
        </body>
    </html>
    """)
    
    page1_html = fixtures / "page1.html"
    page1_html.write_text("""
    <html>
        <body>
            <h1>Page 1</h1>
            <a href="/">Back to Index</a>
        </body>
    </html>
    """)
    
    # Run crawler
    runner = Runner(
        run_id="test-1",
        seed_url="http://localhost:8000/index.html",
    )
    await runner.start()
    
    # Check results
    rows = await database.fetch(
        "SELECT * FROM urls WHERE crawl_run_id = 'test-1'"
    )
    urls = {r["url"] for r in rows}
    
    # Should have found index, page1 and external
    assert "http://localhost:8000/index.html" in urls
    assert "http://localhost:8000/page1.html" in urls
    assert "http://external.com" in urls
    
    # Check crawl run stats
    run = await database.fetchrow(
        "SELECT * FROM crawl_runs WHERE id = 'test-1'"
    )
    assert run["total_fetched"] > 0
    assert run["total_discovered"] == 3