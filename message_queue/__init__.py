"""
Message Queue Package

Redis-based message queue for inter-service communication.
"""
from .producer import send_message, get_producer, MessageProducer
from .consumer import create_consumer, MessageConsumer
from .config import RedisConfig

__all__ = [
    'send_message',
    'get_producer', 
    'MessageProducer',
    'create_consumer',
    'MessageConsumer',
    'RedisConfig',
]
