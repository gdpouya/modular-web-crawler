-- V001_init.sql
-- Initial schema for modular web crawler

-- Track crawl runs and their statistics
CREATE TABLE IF NOT EXISTS crawl_runs (
    id TEXT PRIMARY KEY,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    finished_at TIMESTAMP WITH TIME ZONE,
    seed_domain TEXT NOT NULL,
    total_fetched INTEGER NOT NULL DEFAULT 0,
    total_discovered INTEGER NOT NULL DEFAULT 0
);

-- Store unique URLs and their metadata
CREATE TABLE IF NOT EXISTS urls (
    id SERIAL PRIMARY KEY,
    url TEXT NOT NULL,
    normalized_url TEXT NOT NULL,
    domain TEXT NOT NULL,
    first_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    last_seen TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    status TEXT NOT NULL DEFAULT 'new',  -- new, fetched, error
    http_status INTEGER,
    fetch_attempts INTEGER NOT NULL DEFAULT 0,
    content_type TEXT,
    content_size INTEGER,
    stored_object_key TEXT,
    crawl_run_id TEXT NOT NULL REFERENCES crawl_runs(id) ON DELETE CASCADE,
    CONSTRAINT urls_url_unique UNIQUE (url),
    CONSTRAINT urls_normalized_url_unique UNIQUE (normalized_url)
);

-- Queue for URLs to be fetched
CREATE TABLE IF NOT EXISTS queue (
    id SERIAL PRIMARY KEY,
    url_id INTEGER NOT NULL REFERENCES urls(id) ON DELETE CASCADE,
    priority INTEGER NOT NULL DEFAULT 0,
    enqueued_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    next_fetch_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now()
);

-- Track fetch errors
CREATE TABLE IF NOT EXISTS fetch_errors (
    id SERIAL PRIMARY KEY,
    url_id INTEGER NOT NULL REFERENCES urls(id) ON DELETE CASCADE,
    occurred_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    error_type TEXT NOT NULL,
    error_msg TEXT NOT NULL
);

-- Store domain-specific metadata including robots.txt
CREATE TABLE IF NOT EXISTS domains (
    domain TEXT PRIMARY KEY,
    robots_txt TEXT,
    robots_fetched_at TIMESTAMP WITH TIME ZONE,
    crawl_delay_seconds FLOAT NOT NULL DEFAULT 1.0
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_urls_normalized_url ON urls(normalized_url);
CREATE INDEX IF NOT EXISTS idx_urls_domain ON urls(domain);
CREATE INDEX IF NOT EXISTS idx_urls_status ON urls(status);
CREATE INDEX IF NOT EXISTS idx_queue_next_fetch_at ON queue(next_fetch_at);
CREATE INDEX IF NOT EXISTS idx_queue_url_id ON queue(url_id);
CREATE INDEX IF NOT EXISTS idx_fetch_errors_url_id ON fetch_errors(url_id);
CREATE INDEX IF NOT EXISTS idx_urls_crawl_run_id ON urls(crawl_run_id);