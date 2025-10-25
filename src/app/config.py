"""Configuration loading from environment variables."""
import os
from pydantic import PostgresDsn, HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    postgres_dsn: PostgresDsn | None = None
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "crawler"
    postgres_password: str = "crawler"
    postgres_db: str = "crawler"

    # MinIO / S3
    minio_endpoint: HttpUrl = HttpUrl("http://localhost:9000")
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "crawler"

    # Crawler behavior
    default_crawl_delay: float = 1.0  # seconds
    max_body_size: int = 2 * 1024 * 1024  # 2MB
    user_agent: str = "ModularWebCrawler/0.1.0"
    connect_timeout: float = 10.0  # seconds
    read_timeout: float = 30.0  # seconds

    def get_postgres_dsn(self) -> str:
        """Get PostgreSQL DSN, either from env or construct from components."""
        if self.postgres_dsn:
            return str(self.postgres_dsn)
        return f"postgresql://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


settings = Settings()