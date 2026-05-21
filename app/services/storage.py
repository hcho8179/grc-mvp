"""File storage service — S3-compatible (AWS S3, Cloudflare R2, MinIO).

If S3 is not configured (s3_bucket is empty), all functions raise RuntimeError.
Callers should check `is_configured()` and fall back to DB blobs for local dev.
"""

from __future__ import annotations


def is_configured() -> bool:
    from app.config import get_settings
    s = get_settings()
    return bool(s.s3_bucket and s.s3_access_key and s.s3_secret_key)


def _client():
    import boto3
    from app.config import get_settings
    s = get_settings()
    return boto3.client(
        "s3",
        endpoint_url=s.s3_endpoint_url or None,  # None = AWS default
        aws_access_key_id=s.s3_access_key,
        aws_secret_access_key=s.s3_secret_key,
        region_name=s.s3_region,
    )


def upload(key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
    """Upload bytes to S3. Returns the key."""
    from app.config import get_settings
    _client().put_object(
        Bucket=get_settings().s3_bucket,
        Key=key,
        Body=data,
        ContentType=content_type,
    )
    return key


def download(key: str) -> bytes:
    """Download bytes from S3 by key."""
    from app.config import get_settings
    response = _client().get_object(Bucket=get_settings().s3_bucket, Key=key)
    return response["Body"].read()


def delete(key: str) -> None:
    """Delete an object from S3."""
    from app.config import get_settings
    _client().delete_object(Bucket=get_settings().s3_bucket, Key=key)
