"""
Redis Message Queue Producer

This module provides functionality to publish messages to a Redis queue.
Used by the Supply Transaction Service to notify inventory updates.
"""
import json
import redis
from config import RedisConfig


class MessageProducer:
    """Redis-based message producer for publishing inventory updates"""
    
    def __init__(self):
        self._connection = None
    
    @property
    def connection(self):
        """Lazy connection to Redis"""
        if self._connection is None:
            self._connection = redis.Redis(**RedisConfig.get_connection_params())
        return self._connection
    
    def send_message(self, message_body: dict) -> bool:
        """
        Send a message to the Redis queue.
        
        Args:
            message_body: Dictionary containing the message data
            
        Returns:
            bool: True if message was sent successfully
        """
        try:
            message = json.dumps(message_body)
            self.connection.lpush(RedisConfig.QUEUE_NAME, message)
            print(f" [x] Sent {message_body}")
            return True
        except redis.RedisError as e:
            print(f" [!] Error sending message: {e}")
            return False
    
    def close(self):
        """Close the Redis connection"""
        if self._connection:
            self._connection.close()
            self._connection = None


# Global producer instance
_producer = None


def get_producer() -> MessageProducer:
    """Get or create a global producer instance"""
    global _producer
    if _producer is None:
        _producer = MessageProducer()
    return _producer


def send_message(message_body: dict) -> bool:
    """
    Convenience function to send a message using the global producer.
    
    Args:
        message_body: Dictionary containing:
            - product_code: The product code
            - warehouse_name: The warehouse name
            - quantity: The quantity to add
            
    Returns:
        bool: True if message was sent successfully
    """
    return get_producer().send_message(message_body)
