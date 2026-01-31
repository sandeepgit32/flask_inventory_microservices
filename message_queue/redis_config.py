"""
Redis Message Queue Configuration
"""
import os
import redis
from dotenv import load_dotenv

load_dotenv()


class RedisConfig:
    """Redis configuration settings"""
    HOST = os.environ.get('REDIS_HOST', 'localhost')
    PORT = int(os.environ.get('REDIS_PORT', 6379))
    PASSWORD = os.environ.get('REDIS_PASSWORD', None)
    QUEUE_NAME = os.environ.get('REDIS_QUEUE_NAME', 'inventory_updates')
    
    # Connection pool settings
    MAX_CONNECTIONS = 10
    SOCKET_TIMEOUT = 5
    SOCKET_CONNECT_TIMEOUT = 5
    
    @classmethod
    def get_connection_params(cls):
        """Get Redis connection parameters"""
        params = {
            'host': cls.HOST,
            'port': cls.PORT,
            'decode_responses': True,
            'socket_timeout': cls.SOCKET_TIMEOUT,
            'socket_connect_timeout': cls.SOCKET_CONNECT_TIMEOUT,
        }
        if cls.PASSWORD:
            params['password'] = cls.PASSWORD
        return params


# Redis connection pool for efficient connection reuse
_redis_pool = None


def get_redis_client() -> redis.Redis:
    """
    Get a Redis client from the connection pool.
    Creates the pool on first call.
    """
    global _redis_pool
    if _redis_pool is None:
        _redis_pool = redis.ConnectionPool(
            host=RedisConfig.HOST,
            port=RedisConfig.PORT,
            password=RedisConfig.PASSWORD,
            decode_responses=True,
            max_connections=RedisConfig.MAX_CONNECTIONS,
            socket_timeout=RedisConfig.SOCKET_TIMEOUT,
            socket_connect_timeout=RedisConfig.SOCKET_CONNECT_TIMEOUT
        )
    return redis.Redis(connection_pool=_redis_pool)
