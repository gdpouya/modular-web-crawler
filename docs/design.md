# Design Document

## Architecture

The modular web crawler is designed as a single-threaded, asynchronous application with the following key components:

### Components

1. Runner (`runner.py`)
   - Main orchestration logic
   - Manages crawl sessions
   - Coordinates between queue, fetcher, parser, and storage

2. Queue Management (`queue.py`)
   - Handles URL queue in PostgreSQL
   - Implements priority queuing
   - Ensures URLs are fetched only once
   - Supports domain-based queueing for politeness

3. URL Checker (`url_checker.py`)
   - Fetches and parses robots.txt
   - Caches robots rules in memory
   - Enforces crawl delays per domain
   - Implements politeness policies

4. Fetcher (`fetcher.py`)
   - Handles HTTP requests using httpx
   - Follows redirects
   - Implements timeouts and retries
   - Filters by content type
   - Enforces max body size

5. Parser (`parser.py`)
   - Extracts links from HTML using BeautifulSoup
   - Normalizes URLs for deduplication
   - Filters invalid/unwanted URLs
   - Resolves relative URLs

6. Storage (`storage.py`)
   - Stores raw HTML in MinIO
   - Uses deterministic object keys
   - Handles S3 API interaction

### Data Model

1. Crawl Runs
   - Track individual crawl sessions
   - Store statistics and metadata
   - Enable parallel crawls with isolation

2. URLs
   - Store unique URLs with normalization
   - Track fetch status and attempts
   - Link to stored HTML content

3. Queue
   - Manage pending URLs
   - Support priority ordering
   - Enable politeness delays

4. Domains
   - Cache robots.txt content
   - Store crawl delays
   - Track domain-specific metadata

### Storage Design

1. PostgreSQL
   - Stores all metadata and queue state
   - Enables transactional operations
   - Supports efficient querying
   - Handles concurrency control

2. MinIO
   - Stores raw HTML content
   - Provides S3-compatible API
   - Enables scalable object storage
   - Supports content type metadata

### URL Normalization Rules

URLs are normalized for consistent storage and deduplication:

1. Lowercase scheme and host
2. Remove default ports (80/443)
3. Remove fragments (#...)
4. Sort query parameters alphabetically
5. Remove trailing slashes (except root path)

### Politeness & Rate Limiting

1. Per-domain queues
2. Respect robots.txt
3. Configurable crawl delays
4. Skip unwanted content types
5. Max body size limits

## Scalability Considerations

While currently single-threaded, the design allows for future scaling:

1. Multiple crawlers sharing queue
2. Distributed storage (MinIO)
3. Database partitioning
4. Separate queue consumers

## Extension Points

1. Custom queue prioritization
2. Additional storage backends
3. Custom parsing rules
4. Rate limiting strategies
5. URL filtering policies
