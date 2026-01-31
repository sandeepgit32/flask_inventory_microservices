"""
Redis Cache Layer for Entity Caching

Provides functions for caching entities with TTL, warming cache on startup,
and fetching with circuit breaker fallback to source services.
"""

import json
import logging
import redis
from typing import Any, Dict, List, Optional, Callable
from message_queue.redis_config import get_redis_client
from message_queue.circuit_breaker import CircuitBreaker

logger = logging.getLogger(__name__)


def get_cache_key(entity_type: str, entity_id: int) -> str:
    """
    Generate standardized cache key.
    
    Args:
        entity_type: Type of entity (supplier, customer, product, etc.)
        entity_id: ID of the entity
        
    Returns:
        Cache key string (e.g., 'cache:supplier:123')
    """
    return f"cache:{entity_type}:{entity_id}"


def cache_entity(entity_type: str, entity_id: int, data: Dict, ttl: int = 86400):
    """
    Cache entity data in Redis.
    
    Args:
        entity_type: Type of entity (supplier, customer, product, etc.)
        entity_id: ID of the entity
        data: Entity data dictionary
        ttl: Time to live in seconds (default: 24 hours)
    """
    try:
        redis_client = get_redis_client()
        cache_key = get_cache_key(entity_type, entity_id)
        
        # Store as JSON string
        redis_client.setex(
            cache_key,
            ttl,
            json.dumps(data)
        )
        logger.debug(f"Cached {entity_type}:{entity_id} with TTL {ttl}s")
        
    except Exception as e:
        logger.error(f"Failed to cache {entity_type}:{entity_id}: {e}")


def get_cached_entity(entity_type: str, entity_id: int) -> Optional[Dict]:
    """
    Retrieve entity from cache.
    
    Args:
        entity_type: Type of entity
        entity_id: ID of the entity
        
    Returns:
        Entity data dictionary or None if not found
    """
    try:
        redis_client = get_redis_client()
        cache_key = get_cache_key(entity_type, entity_id)
        
        cached_data = redis_client.get(cache_key)
        if cached_data:
            logger.debug(f"Cache HIT for {entity_type}:{entity_id}")
            return json.loads(cached_data)
        else:
            logger.debug(f"Cache MISS for {entity_type}:{entity_id}")
            return None
            
    except Exception as e:
        logger.error(f"Failed to get cached {entity_type}:{entity_id}: {e}")
        return None


def delete_cache(entity_type: str, entity_id: int):
    """
    Delete entity from cache (for invalidation).
    
    Args:
        entity_type: Type of entity
        entity_id: ID of the entity
    """
    try:
        redis_client = get_redis_client()
        cache_key = get_cache_key(entity_type, entity_id)
        redis_client.delete(cache_key)
        logger.info(f"Invalidated cache for {entity_type}:{entity_id}")
        
    except Exception as e:
        logger.error(f"Failed to delete cache {entity_type}:{entity_id}: {e}")


def warm_cache_sync(entity_type: str, entities: List[Dict], ttl: int = 86400):
    """
    Warm cache with multiple entities (synchronous bulk load).
    
    Args:
        entity_type: Type of entity
        entities: List of entity dictionaries (must have 'id' field)
        ttl: Time to live in seconds (default: 24 hours)
    """
    try:
        redis_client = get_redis_client()
        pipeline = redis_client.pipeline()
        
        for entity in entities:
            entity_id = entity.get('id')
            if entity_id is None:
                logger.warning(f"Entity missing 'id' field, skipping: {entity}")
                continue
                
            cache_key = get_cache_key(entity_type, entity_id)
            pipeline.setex(
                cache_key,
                ttl,
                json.dumps(entity)
            )
        
        pipeline.execute()
        logger.info(f"Warmed cache with {len(entities)} {entity_type} entities")
        
    except Exception as e:
        logger.error(f"Failed to warm cache for {entity_type}: {e}")
        raise


def get_or_fetch(
    entity_type: str,
    entity_id: int,
    fetch_callback: Callable[[int], Optional[Dict]],
    ttl: int = 86400
) -> Optional[Dict]:
    """
    Get entity from cache or fetch from source (cache-aside pattern).
    
    Args:
        entity_type: Type of entity
        entity_id: ID of the entity
        fetch_callback: Function to fetch entity if not in cache
        ttl: Time to live in seconds
        
    Returns:
        Entity data dictionary or None if not found
    """
    # Try cache first
    cached = get_cached_entity(entity_type, entity_id)
    if cached is not None:
        return cached
    
    # Fetch from source
    try:
        entity_data = fetch_callback(entity_id)
        if entity_data:
            # Cache for future requests
            cache_entity(entity_type, entity_id, entity_data, ttl)
        return entity_data
        
    except Exception as e:
        logger.error(f"Failed to fetch {entity_type}:{entity_id}: {e}")
        return None


def get_or_fetch_with_breaker(
    entity_type: str,
    entity_id: int,
    fetch_callback: Callable[[int], Optional[Dict]],
    breaker: CircuitBreaker,
    ttl: int = 86400
) -> Optional[Dict]:
    """
    Get entity from cache or fetch with circuit breaker protection.
    
    Args:
        entity_type: Type of entity
        entity_id: ID of the entity
        fetch_callback: Function to fetch entity if not in cache
        breaker: CircuitBreaker instance for protection
        ttl: Time to live in seconds
        
    Returns:
        Entity data dictionary or None if not found
    """
    # Try cache first
    cached = get_cached_entity(entity_type, entity_id)
    if cached is not None:
        return cached
    
    # Fetch from source with circuit breaker
    try:
        entity_data = breaker.call(fetch_callback, entity_id)
        if entity_data:
            # Cache for future requests
            cache_entity(entity_type, entity_id, entity_data, ttl)
        return entity_data
        
    except Exception as e:
        logger.error(
            f"Failed to fetch {entity_type}:{entity_id} "
            f"(Circuit breaker: {breaker.get_state()}): {e}"
        )
        return None


def cache_list(entity_type: str, list_key: str, data: List[Dict], ttl: int = 3600):
    """
    Cache a list of entities (for paginated results).
    
    Args:
        entity_type: Type of entity
        list_key: Unique key for this list (e.g., 'page_1_limit_50')
        data: List of entity dictionaries
        ttl: Time to live in seconds (default: 1 hour)
    """
    try:
        redis_client = get_redis_client()
        cache_key = f"cache:{entity_type}:list:{list_key}"
        
        redis_client.setex(
            cache_key,
            ttl,
            json.dumps(data)
        )
        logger.debug(f"Cached list {entity_type}:{list_key}")
        
    except Exception as e:
        logger.error(f"Failed to cache list {entity_type}:{list_key}: {e}")


def get_cached_list(entity_type: str, list_key: str) -> Optional[List[Dict]]:
    """
    Retrieve cached list.
    
    Args:
        entity_type: Type of entity
        list_key: Unique key for this list
        
    Returns:
        List of entity dictionaries or None if not found
    """
    try:
        redis_client = get_redis_client()
        cache_key = f"cache:{entity_type}:list:{list_key}"
        
        cached_data = redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        return None
        
    except Exception as e:
        logger.error(f"Failed to get cached list {entity_type}:{list_key}: {e}")
        return None


def invalidate_list_cache(entity_type: str):
    """
    Invalidate all list caches for an entity type.
    
    Args:
        entity_type: Type of entity
    """
    try:
        redis_client = get_redis_client()
        pattern = f"cache:{entity_type}:list:*"
        
        # Scan and delete matching keys
        for key in redis_client.scan_iter(match=pattern):
            redis_client.delete(key)
            
        logger.info(f"Invalidated all list caches for {entity_type}")
        
    except Exception as e:
        logger.error(f"Failed to invalidate list cache for {entity_type}: {e}")
