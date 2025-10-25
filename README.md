# Modular Web Crawler

A single-threaded, asynchronous modular web crawler written in Python 3.11. Uses PostgreSQL for metadata storage and MinIO for raw HTML storage.

## Features

- Asynchronous single-threaded crawling using `httpx` and `asyncio`
- PostgreSQL storage for crawl metadata and URL queue
- MinIO (S3-compatible) storage for raw HTML content
- URL normalization and deduplication
- Robots.txt compliance
- Configurable crawl delays and politeness rules
- Docker and docker-compose support
- Integration tests using containerized static test server

## Quick Start

1. Build and start services:
```bash
docker-compose up --build -d
```

2. Run a crawl:
```bash
docker-compose exec app crawler run --seed <URL> --run-id local1
```

3. Generate a report:
```bash
docker-compose exec app crawler report --run-id local1 --out /tmp/report.json
```

## Development

Requirements:
- Python 3.11+
- Docker and docker-compose
- PostgreSQL 15+
- MinIO

Install dependencies:
```bash
pip install -e ".[dev,test]"
```

Run tests:
```bash
pytest
```

Run linting:
```bash
black src tests
ruff check src tests
```

## Configuration

See `.env.example` for available environment variables. Key settings:

- `POSTGRES_*`: Database connection settings
- `MINIO_*`: MinIO/S3 connection and credentials
- Crawler behavior: delays, timeouts, max body size

## Architecture

See [docs/design.md](docs/design.md) for architecture details and [docs/runbook.md](docs/runbook.md) for operational procedures.

This repository contains a single-threaded, asynchronous modular web crawler written in Python 3.11.

What is included
- App source under `src/crawler`
- Dockerfile and `docker-compose.yml` to run the app, Postgres, and MinIO
- SQL migration under `sql/migrations/001_create_schema.sql`
- Tests (pytest) and integration test which uses `docker-compose`
- CI workflow in `.github/workflows/ci.yml`
- Docs: `docs/design.md`, `docs/runbook.md`, `docs/example_report.json`

Quick start

1. Build and start the stack:

   docker-compose up -d --build

2. Run crawler locally (ensures PYTHONPATH so `src` is importable):

   PYTHONPATH=src python -m crawler.cli run --seed http://localhost:8000/index.html --run-id demo-1

Notes
- Postgres is on port 5432, user/password: crawler/crawler
- MinIO is on port 9000, access/secret: minioadmin/minioadmin
# modular-web-crawler