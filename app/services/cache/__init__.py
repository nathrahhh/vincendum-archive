"""Optional Redis caching utilities."""

from app.services.cache.redis_client import (
    cache_delete,
    cache_delete_pattern,
    cache_get,
    cache_get_json,
    cache_set,
    cache_set_json,
    get_redis_client,
    reset_redis_client,
)

__all__ = [
    "cache_delete",
    "cache_delete_pattern",
    "cache_get",
    "cache_get_json",
    "cache_set",
    "cache_set_json",
    "get_redis_client",
    "reset_redis_client",
]
