"""
Event System for Asynchronous Communication

Publisher: Publish events to Redis channels
Consumer: Subscribe to channels and handle events
"""

import json
import logging
import os
import time
import redis
from datetime import datetime
from multiprocessing import Process
from typing import Dict, List, Callable
from message_queue.redis_config import get_redis_client, RedisConfig

logger = logging.getLogger(__name__)


def get_pubsub_redis_client():
    """
    Get a Redis client configured for pub/sub (no socket timeout).
    Pub/sub requires blocking reads so we need no timeout.
    """
    return redis.Redis(
        host=RedisConfig.HOST,
        port=RedisConfig.PORT,
        password=RedisConfig.PASSWORD,
        decode_responses=True,
        socket_timeout=None,  # No timeout for pub/sub
        socket_connect_timeout=30
    )


class EventPublisher:
    """
    Publisher for Redis pub/sub events.
    """
    
    def __init__(self):
        self.redis_client = get_redis_client()
    
    def publish(self, channel: str, event_type: str, entity_id: int, data: Dict = None):
        """
        Publish event to Redis channel.
        
        Args:
            channel: Channel name (e.g., 'supplier_events')
            event_type: Type of event ('created', 'updated', 'deleted')
            entity_id: ID of the entity
            data: Optional entity data
        """
        try:
            event_payload = {
                "event_type": event_type,
                "entity_id": entity_id,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data or {}
            }
            
            message = json.dumps(event_payload)
            self.redis_client.publish(channel, message)
            
            logger.info(
                f"Published event: channel={channel}, "
                f"type={event_type}, entity_id={entity_id}"
            )
            
        except Exception as e:
            logger.error(f"Failed to publish event to {channel}: {e}")
            raise


class EventConsumerProcess(Process):
    """
    Base class for event consumer processes.
    
    Subscribes to Redis channels and handles events by calling
    handler methods (handle_created, handle_updated, handle_deleted).
    
    Subclasses should override handler methods with custom logic.
    """
    
    def __init__(self, channels: List[str], name: str = "consumer"):
        """
        Initialize event consumer process.
        
        Args:
            channels: List of channel names to subscribe to
            name: Name identifier for this consumer
        """
        super().__init__(name=name)
        self.channels = channels
        self.consumer_name = name
        self._should_stop = False
        
    def run(self):
        """
        Main process loop - subscribe to channels and handle messages.
        """
        logger.info(
            f"Starting event consumer '{self.consumer_name}' "
            f"for channels: {self.channels}"
        )
        
        try:
            # Use a separate Redis client with no socket timeout for pub/sub
            redis_client = get_pubsub_redis_client()
            pubsub = redis_client.pubsub(ignore_subscribe_messages=True)
            pubsub.subscribe(*self.channels)
            
            logger.info(f"Consumer '{self.consumer_name}' subscribed successfully")
            
            # Listen for messages
            for message in pubsub.listen():
                if self._should_stop:
                    break
                    
                if message['type'] == 'message':
                    self._handle_message(message)
                    
        except Exception as e:
            logger.error(f"Consumer '{self.consumer_name}' error: {e}")
            raise
        finally:
            logger.info(f"Consumer '{self.consumer_name}' shutting down")
    
    def _handle_message(self, message: Dict):
        """
        Parse and route message to appropriate handler.
        
        Args:
            message: Redis pub/sub message
        """
        try:
            # With decode_responses=True, channel and data are already strings
            channel = message['channel']
            data_str = message['data']
            event_data = json.loads(data_str)
            
            event_type = event_data.get('event_type')
            entity_id = event_data.get('entity_id')
            data = event_data.get('data', {})
            
            logger.debug(
                f"Consumer '{self.consumer_name}' received: "
                f"channel={channel}, type={event_type}, id={entity_id}"
            )
            
            # Route to handler based on event type
            if event_type == 'created':
                self.handle_created(channel, entity_id, data)
            elif event_type == 'updated':
                self.handle_updated(channel, entity_id, data)
            elif event_type == 'deleted':
                self.handle_deleted(channel, entity_id, data)
            else:
                logger.warning(f"Unknown event type: {event_type}")
                
        except Exception as e:
            logger.error(f"Error handling message: {e}")
    
    def handle_created(self, channel: str, entity_id: int, data: Dict):
        """
        Handle entity created event.
        Override in subclass.
        """
        pass
    
    def handle_updated(self, channel: str, entity_id: int, data: Dict):
        """
        Handle entity updated event.
        Override in subclass.
        """
        pass
    
    def handle_deleted(self, channel: str, entity_id: int, data: Dict):
        """
        Handle entity deleted event.
        Override in subclass.
        """
        pass
    
    def stop(self):
        """
        Signal the consumer to stop.
        """
        self._should_stop = True


class InventoryEventConsumer(EventConsumerProcess):
    """
    Consumer for inventory stock in/out events.
    """
    
    def __init__(self, update_callback: Callable[[str, int, int], None]):
        """
        Initialize inventory consumer.
        
        Args:
            update_callback: Function(event_type, product_id, quantity)
        """
        super().__init__(
            channels=['procurement_stock_in', 'order_stock_out'],
            name='inventory_consumer'
        )
        self.update_callback = update_callback
    
    def _handle_message(self, message: Dict):
        """
        Handle inventory update messages.
        """
        try:
            channel = message['channel'].decode('utf-8')
            data_str = message['data'].decode('utf-8')
            event_data = json.loads(data_str)
            
            product_id = event_data.get('product_id')
            quantity = event_data.get('quantity')
            
            if not product_id or not quantity:
                logger.warning(f"Invalid inventory event: {event_data}")
                return
            
            logger.info(
                f"Inventory event: channel={channel}, "
                f"product_id={product_id}, quantity={quantity}"
            )
            
            # Call update callback
            self.update_callback(channel, product_id, quantity)
            
        except Exception as e:
            logger.error(f"Error handling inventory message: {e}")
