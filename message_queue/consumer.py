"""
Redis Message Queue Consumer

This module provides functionality to consume messages from a Redis queue.
Used by the Inventory Service to process inventory updates.
"""
import json
import time
import redis
from message_queue.redis_config import RedisConfig


class MessageConsumer:
    """Redis-based message consumer for processing inventory updates"""
    
    def __init__(self, callback):
        """
        Initialize the consumer.
        
        Args:
            callback: Function to call when a message is received.
                     Should accept a single dict argument (the message body).
        """
        self._connection = None
        self.callback = callback
        self.running = False
    
    @property
    def connection(self):
        """Lazy connection to Redis"""
        if self._connection is None:
            self._connection = redis.Redis(**RedisConfig.get_connection_params())
        return self._connection
    
    def start_consuming(self, block_timeout: int = 5):
        """
        Start consuming messages from the queue.
        
        Args:
            block_timeout: Seconds to block waiting for messages (0 = forever)
        """
        self.running = True
        print(f' [*] Waiting for messages on queue "{RedisConfig.QUEUE_NAME}". To exit press CTRL+C')
        
        while self.running:
            try:
                # BRPOP blocks until a message is available
                result = self.connection.brpop(RedisConfig.QUEUE_NAME, timeout=block_timeout)
                
                if result:
                    _, message = result
                    try:
                        message_body = json.loads(message)
                        print(f" [x] Received {message_body}")
                        self.callback(message_body)
                    except json.JSONDecodeError as e:
                        print(f" [!] Error decoding message: {e}")
                    except Exception as e:
                        print(f" [!] Error processing message: {e}")
                        
            except redis.RedisError as e:
                print(f" [!] Redis error: {e}. Reconnecting in 5 seconds...")
                self._connection = None
                time.sleep(5)
            except KeyboardInterrupt:
                print("\n [*] Stopping consumer...")
                self.stop()
    
    def stop(self):
        """Stop consuming messages"""
        self.running = False
        if self._connection:
            self._connection.close()
            self._connection = None


def create_consumer(callback) -> MessageConsumer:
    """
    Create a new message consumer.
    
    Args:
        callback: Function to call when a message is received
        
    Returns:
        MessageConsumer instance
    """
    return MessageConsumer(callback)
