"""MinIO storage for raw HTML content."""
import hashlib
import aioboto3
from typing import Optional
import structlog

from .config import settings

logger = structlog.get_logger()


class Storage:
    def __init__(self):
        """Initialize MinIO storage with settings."""
        self.session = aioboto3.Session()
        self.endpoint = settings.minio_endpoint
        self.access_key = settings.minio_access_key
        self.secret_key = settings.minio_secret_key
        self.bucket = settings.minio_bucket

    async def ensure_bucket(self) -> None:
        """Create bucket if it doesn't exist."""
        async with self.session.client(
            "s3",
            endpoint_url=str(self.endpoint),
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
        ) as client:
            try:
                await client.head_bucket(Bucket=self.bucket)
            except:
                await client.create_bucket(Bucket=self.bucket)

    async def store_html(self, run_id: str, url: str, content: bytes) -> Optional[str]:
        """
        Store HTML content in MinIO.
        
        Args:
            run_id: Crawl run ID
            url: Source URL
            content: Raw HTML bytes
            
        Returns:
            Object key if stored successfully
        """
        # Generate deterministic key from URL
        url_hash = hashlib.sha256(url.encode()).hexdigest()
        key = f"{run_id}/{url_hash}.html"
        
        try:
            async with self.session.client(
                "s3",
                endpoint_url=str(self.endpoint),
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
            ) as client:
                await client.put_object(
                    Bucket=self.bucket,
                    Key=key,
                    Body=content,
                    ContentType="text/html",
                )
                return key
                
        except Exception as e:
            logger.error("store_failed", url=url, error=str(e))
            return None