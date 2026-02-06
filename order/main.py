import sys
import os
import logging
import signal
import json
import requests
from datetime import datetime
from flask import Flask, request, jsonify

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from db import db
from models import Orders
from message_queue.event_system import EventPublisher, EventConsumerProcess
from message_queue.cache import (warm_cache_sync, cache_entity, get_cached_entity,
                                  cache_list, get_cached_list)
from message_queue.circuit_breaker import CircuitBreaker
from message_queue.supervisor import MultiProcessSupervisor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

event_publisher = None
supervisor = None
cache_warmed = False
customer_breaker = CircuitBreaker(failure_threshold=5, timeout=30, name='customer_service')
product_breaker = CircuitBreaker(failure_threshold=5, timeout=30, name='product_service')


class OrderEventConsumer(EventConsumerProcess):
    """Consumer for customer and product events"""
    
    def __init__(self):
        super().__init__(
            channels=['customer_events', 'product_events'],
            name='order_consumer'
        )
    
    def handle_created(self, channel, entity_id, data):
        if channel == 'customer_events':
            cache_entity('customer', entity_id, data, ttl=86400)
            logger.info(f"Cached customer {entity_id} from event")
        elif channel == 'product_events':
            cache_entity('product', entity_id, data, ttl=86400)
            logger.info(f"Cached product {entity_id} from event")
    
    def handle_updated(self, channel, entity_id, data):
        if channel == 'customer_events':
            cache_entity('customer', entity_id, data, ttl=86400)
        elif channel == 'product_events':
            cache_entity('product', entity_id, data, ttl=86400)


def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)
    db.init_app(flask_app)

    flask_app.cache_warmed = False
    flask_app.customer_breaker = CircuitBreaker(failure_threshold=5, timeout=30, name='customer_service')
    flask_app.product_breaker = CircuitBreaker(failure_threshold=5, timeout=30, name='product_service')

    from routes import bp as order_bp
    flask_app.register_blueprint(order_bp)

    return flask_app


def main():
    logger.info("Starting Order Service...")
    app = create_app()
    
    # Warm cache
    try:
        with app.app_context():
            logger.info("Starting cache warming for orders...")
            
            # Warm customer cache
            try:
                response = requests.get(f"{Config.CUSTOMER_SERVICE_URL}/customers", timeout=5)
                if response.status_code == 200:
                    customers = response.json().get('customers', [])
                    warm_cache_sync('customer', customers, ttl=86400)
                    logger.info(f"Warmed {len(customers)} customers")
            except Exception as e:
                logger.warning(f"Could not warm customer cache: {e}")
            
            # Warm product cache
            try:
                response = requests.get(f"{Config.PRODUCT_SERVICE_URL}/products", timeout=5)
                if response.status_code == 200:
                    products = response.json().get('products', [])
                    warm_cache_sync('product', products, ttl=86400)
                    logger.info(f"Warmed {len(products)} products")
            except Exception as e:
                logger.warning(f"Could not warm product cache: {e}")
            
            app.cache_warmed = True
            logger.info("Cache warming complete")
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")
    
    app.event_publisher = EventPublisher()
    
    # Initialize and start supervisor
    app.supervisor = MultiProcessSupervisor()
    app.supervisor.add_process(
        lambda: OrderEventConsumer(),
        max_retries=3,
        retry_delay=5,
        check_interval=5
    )
    app.supervisor.start_all()
    
    # Handle shutdown signals
    def shutdown_handler(signum, frame):
        logger.info("Received shutdown signal, cleaning up...")
        if hasattr(app, 'supervisor') and app.supervisor:
            app.supervisor.stop_all()
        logger.info("Shutdown complete")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    logger.info(f"Order Service ready on port {Config.SERVICE_PORT}")
    
    app.run(host='0.0.0.0', port=Config.SERVICE_PORT, debug=False)


if __name__ == '__main__':
    main()
