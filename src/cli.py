"""CLI interface."""
from pathlib import Path
import json
import typer
import asyncio

from app.runner import Runner
from app.db import get_connection

app = typer.Typer()


@app.command()
def run(
    seed: str = typer.Option(..., "--seed", help="Seed URL to start crawling from"),
    run_id: str = typer.Option(..., "--run-id", help="Unique identifier for this crawl run"),
):
    """Start a new crawl run."""
    runner = Runner(run_id=run_id, seed_url=seed)
    asyncio.run(runner.start())


@app.command()
def report(
    run_id: str = typer.Option(..., "--run-id", help="Crawl run ID to generate report for"),
    out: Path = typer.Option(..., "--out", help="Output JSON file path"),
):
    """Generate a crawl run report."""
    async def _generate():
        async with await get_connection() as conn:
            # Get run info
            run = await conn.fetchrow(
                "SELECT * FROM crawl_runs WHERE id = $1",
                run_id,
            )
            if not run:
                typer.echo(f"Run {run_id} not found")
                raise typer.Exit(1)
                
            # Get pages and errors
            pages = await conn.fetch(
                """
                SELECT url, status, http_status, content_type, content_size, stored_object_key
                FROM urls
                WHERE crawl_run_id = $1
                ORDER BY id
                """,
                run_id,
            )
            
            errors = await conn.fetch(
                """
                SELECT u.url, e.error_type, e.error_msg, e.occurred_at
                FROM fetch_errors e
                JOIN urls u ON u.id = e.url_id
                WHERE u.crawl_run_id = $1
                ORDER BY e.occurred_at
                """,
                run_id,
            )
            
            # Build report
            report = {
                "run_id": run["id"],
                "seed_domain": run["seed_domain"],
                "started_at": run["started_at"].isoformat(),
                "finished_at": run["finished_at"].isoformat() if run["finished_at"] else None,
                "total_fetched": run["total_fetched"],
                "total_discovered": run["total_discovered"],
                "pages": [dict(p) for p in pages],
                "errors": [dict(e) for e in errors],
            }
            
            # Write JSON
            out.write_text(json.dumps(report, indent=2))
            typer.echo(f"Report written to {out}")
            
    asyncio.run(_generate())


if __name__ == "__main__":
    app()