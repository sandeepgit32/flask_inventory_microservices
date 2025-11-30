# Message Queue Service

Redis-based message queue for inter-service communication in the Flask Inventory Microservices system.

## Overview

This service provides a lightweight message queue using Redis Lists for asynchronous communication between microservices. It replaces RabbitMQ with a simpler Redis-based solution.

## Components

- **producer.py** - Publishes messages to the Redis queue
- **consumer.py** - Consumes and processes messages from the Redis queue
- **config.py** - Redis configuration settings
- **redis.conf** - Redis server configuration

## Message Flow

```
Supply Transaction Service                    Inventory Service
        │                                            │
        │  ┌─────────────────────────────────────┐  │
        └──►       Redis Queue                   ├──┘
           │   (inventory_updates)               │
           └─────────────────────────────────────┘
```

1. When a supply transaction is created, the Supply Transaction Service publishes a message
2. The message contains: `product_code`, `warehouse_name`, `quantity`
3. The Inventory Service's consumer receives the message and updates the storage quantity

## Configuration

Environment variables (`.env`):

| Variable | Description | Default |
|----------|-------------|---------|
| `REDIS_HOST` | Redis server hostname | `localhost` |
| `REDIS_PORT` | Redis server port | `6379` |
| `REDIS_PASSWORD` | Redis password (optional) | `None` |
| `REDIS_QUEUE_NAME` | Name of the queue | `inventory_updates` |

## Usage

### Producer (in Supply Transaction Service)

```python
from message_queue.producer import send_message

message = {
    "product_code": "PROD001",
    "warehouse_name": "Main_Warehouse",
    "quantity": 100
}
send_message(message)
```

### Consumer (in Inventory Service)

```python
from message_queue.consumer import create_consumer

def process_message(message):
    product_code = message['product_code']
    warehouse_name = message['warehouse_name']
    quantity = message['quantity']
    # Update storage...

consumer = create_consumer(process_message)
consumer.start_consuming()
```

## Docker

The Redis server is configured via `Dockerfile` and `redis.conf`. The service is included in the main `docker-compose.yml`.

## Dependencies

- `redis` - Python Redis client

Add to your service's `requirements.txt`:
```
redis>=4.0.0
```
