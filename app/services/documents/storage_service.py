"""AWS S3 storage helpers for Vincendum document uploads.

This module is intentionally independent of SQLAlchemy models, auth, and
HTTP routes. It operates only on storage keys and file metadata.

Configuration is read from existing environment variables:

- ``AWS_ACCESS_KEY_ID``
- ``AWS_SECRET_ACCESS_KEY``
- ``AWS_REGION``
- ``AWS_S3_BUCKET``
"""

from __future__ import annotations

import os

import boto3
from botocore.client import BaseClient

PRESIGNED_URL_EXPIRATION_SECONDS = 900

_REQUIRED_ENV_VARS = (
    "AWS_ACCESS_KEY_ID",
    "AWS_SECRET_ACCESS_KEY",
    "AWS_REGION",
    "AWS_S3_BUCKET",
)

_s3_client: BaseClient | None = None


def _require_env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(
            f"Missing required AWS configuration: {name}. "
            "S3 storage cannot be used until this environment variable is set."
        )
    return value


def _get_bucket_name() -> str:
    return _require_env("AWS_S3_BUCKET")


def get_s3_client() -> BaseClient:
    """
    Return a shared boto3 S3 client configured from environment variables.

    Raises:
        RuntimeError: If any required AWS environment variable is missing.
    """
    global _s3_client
    if _s3_client is None:
        access_key = _require_env("AWS_ACCESS_KEY_ID")
        secret_key = _require_env("AWS_SECRET_ACCESS_KEY")
        region = _require_env("AWS_REGION")
        # Validate bucket presence at client creation time so misconfiguration
        # fails early rather than during the first upload/download call.
        _require_env("AWS_S3_BUCKET")
        _s3_client = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region,
        )
    return _s3_client


def reset_s3_client() -> None:
    """Clear the cached S3 client (useful in tests)."""
    global _s3_client
    _s3_client = None


def generate_upload_url(storage_key: str, content_type: str) -> str:
    """
    Generate a presigned S3 PUT URL for direct browser upload.

    Args:
        storage_key: Object key within the configured bucket.
        content_type: MIME type the client must send with the PUT request.

    Returns:
        A temporary presigned URL for uploading to S3.
    """
    if not storage_key.strip():
        raise ValueError("storage_key must be a non-empty string")
    if not content_type.strip():
        raise ValueError("content_type must be a non-empty string")

    client = get_s3_client()
    url: str = client.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": _get_bucket_name(),
            "Key": storage_key,
            "ContentType": content_type,
        },
        ExpiresIn=PRESIGNED_URL_EXPIRATION_SECONDS,
    )
    return url


def generate_download_url(storage_key: str) -> str:
    """
    Generate a presigned S3 GET URL for temporary file access.

    Args:
        storage_key: Object key within the configured bucket.

    Returns:
        A temporary presigned URL for downloading from S3.
    """
    if not storage_key.strip():
        raise ValueError("storage_key must be a non-empty string")

    client = get_s3_client()
    url: str = client.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": _get_bucket_name(),
            "Key": storage_key,
        },
        ExpiresIn=PRESIGNED_URL_EXPIRATION_SECONDS,
    )
    return url


def delete_object(storage_key: str) -> None:
    """
    Delete an object from the configured S3 bucket.

    Args:
        storage_key: Object key within the configured bucket.
    """
    if not storage_key.strip():
        raise ValueError("storage_key must be a non-empty string")

    client = get_s3_client()
    client.delete_object(
        Bucket=_get_bucket_name(),
        Key=storage_key,
    )
