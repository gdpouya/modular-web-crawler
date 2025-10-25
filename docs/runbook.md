# Operations Runbook

## Prerequisites

- Docker and docker-compose
- Python 3.11+ (for local development)
- PostgreSQL client (optional, for debugging)
- MinIO client (optional, for debugging)

## Setup

1. Clone repository:
```bash
git clone <repo-url>
cd modular-web-crawler
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Build and start services:
```bash
docker-compose up --build -d
```

## Running the Crawler

1. Start a crawl:
```bash
docker-compose exec app crawler run --seed <URL> --run-id <id>
```

2. Generate a report:
```bash
docker-compose exec app crawler report --run-id <id> --out /tmp/report.json
```

## Monitoring

1. Check logs:
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f app
docker-compose logs -f postgres
docker-compose logs -f minio
```

2. Check database:
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U crawler crawler

# Useful queries
SELECT * FROM crawl_runs ORDER BY started_at DESC LIMIT 5;
SELECT COUNT(*) FROM urls WHERE crawl_run_id = '<run_id>';
SELECT COUNT(*) FROM queue;
```

3. Check MinIO:
```bash
# Install mc (MinIO Client)
mc alias set local http://localhost:9000 minioadmin minioadmin
mc ls local/crawler
```

## Troubleshooting

### Database Issues

1. Connection errors:
```bash
# Check if PostgreSQL is up
docker-compose ps postgres
docker-compose logs postgres

# Verify connection settings
docker-compose exec postgres pg_isready -U crawler
```

2. Reset database:
```bash
# Remove volume and recreate
docker-compose down -v
docker-compose up -d
```

### MinIO Issues

1. Access denied:
```bash
# Verify credentials
echo $MINIO_ACCESS_KEY
echo $MINIO_SECRET_KEY

# Check if MinIO is healthy
curl http://localhost:9000/minio/health/live
```

2. Reset storage:
```bash
# Remove volume and recreate
docker-compose down -v
docker-compose up -d
```

### Crawler Issues

1. Hung crawler:
```bash
# Check logs
docker-compose logs -f app

# Check queue size
docker-compose exec postgres psql -U crawler crawler -c "SELECT COUNT(*) FROM queue;"
```

2. Performance issues:
```bash
# Check crawl delays
SELECT domain, crawl_delay_seconds FROM domains;

# Check fetch errors
SELECT error_type, COUNT(*) FROM fetch_errors GROUP BY error_type;
```

## Maintenance

1. Cleanup old data:
```sql
-- Delete old runs
DELETE FROM crawl_runs WHERE started_at < NOW() - INTERVAL '30 days';

-- Delete orphaned URLs
DELETE FROM urls WHERE crawl_run_id NOT IN (SELECT id FROM crawl_runs);
```

2. Backup database:
```bash
docker-compose exec postgres pg_dump -U crawler crawler > backup.sql
```

3. Backup MinIO:
```bash
mc mirror local/crawler backup/
```

## Development

1. Install dependencies:
```bash
pip install -e ".[dev,test]"
```

2. Run tests:
```bash
pytest
```

3. Run linting:
```bash
black src tests
ruff check src tests
```
