"""
Redis Message Queue Producer

Publishes messages to Redis queue for inventory updates.
"""
import os
import sys

# Add message_queue to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'message_queue'))

from message_queue.producer import send_message

__all__ = ['send_message']
