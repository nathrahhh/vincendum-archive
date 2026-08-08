"""Redis client helpers for optional application caching."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import redis

logger = logging.getLogger(__name__)

DEFAULT_TTL_SECONDS = 3600

_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis:
    """Return a shared Redis client configured from ``REDIS_URL``."""
    global _client
    if _client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _client = redis.Redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
            socket_timeout=1,
        )
    return _client


def reset_redis_client() -> None:
    """Clear the cached client (useful in tests)."""
    global _client
    _client = None


def cache_get(key: str) -> str | None:
    """Get a raw string value from Redis, or ``None`` on miss/error."""
    try:
        value = get_redis_client().get(key)
        if value is None:
            return None
        return str(value)
    except Exception as exc:
        logger.warning("Redis get failed for key=%s: %s", key, exc)
        return None


def cache_get_json(key: str) -> dict[str, Any] | None:
    """Get and JSON-decode a cached value, or ``None`` on miss/error."""
    raw = cache_get(key)
    if raw is None:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Redis JSON decode failed for key=%s: %s", key, exc)
        return None
    if not isinstance(parsed, dict):
        return None
    return parsed


def cache_set(
    key: str,
    value: str,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> bool:
    """Set a raw string value with TTL. Returns False on Redis errors."""
    try:
        get_redis_client().setex(key, ttl_seconds, value)
        return True
    except Exception as exc:
        logger.warning("Redis set failed for key=%s: %s", key, exc)
        return False


def cache_set_json(
    key: str,
    value: dict[str, Any],
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> bool:
    """JSON-encode and cache a dictionary with TTL."""
    try:
        payload = json.dumps(value, default=str)
    except (TypeError, ValueError) as exc:
        logger.warning("Redis JSON encode failed for key=%s: %s", key, exc)
        return False
    return cache_set(key, payload, ttl_seconds=ttl_seconds)


def cache_delete(key: str) -> bool:
    """Delete a single cache key. Returns False on Redis errors."""
    try:
        get_redis_client().delete(key)
        return True
    except Exception as exc:
        logger.warning("Redis delete failed for key=%s: %s", key, exc)
        return False


def cache_delete_pattern(pattern: str) -> int:
    """
    Delete all keys matching ``pattern``.

    Returns the number of keys deleted, or ``0`` on Redis errors.
    """
    try:
        client = get_redis_client()
        deleted = 0
        for key in client.scan_iter(match=pattern, count=100):
            client.delete(key)
            deleted += 1
        return deleted
    except Exception as exc:
        logger.warning("Redis delete pattern failed for pattern=%s: %s", pattern, exc)
        return 0
