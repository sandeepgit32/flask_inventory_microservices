import sys
import os
import logging
import signal
import requests
from flask import Flask, request, jsonify

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from db import db
from models import Product
from message_queue.event_system import EventPublisher, EventConsumerProcess
from message_queue.cache import (warm_cache_sync, cache_entity, delete_cache, 
                                  invalidate_list_cache, get_cached_entity)
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


class ProductEventConsumer(EventConsumerProcess):
    """Consumer for product and supplier events"""
    
    def __init__(self):
        super().__init__(
            channels=['product_events', 'supplier_events'],
            name='product_consumer'
        )
    
    def handle_created(self, channel, entity_id, data):
        if channel == 'supplier_events':
            # Cache supplier data
            cache_entity('supplier', entity_id, data, ttl=86400)
            logger.info(f"Cached supplier {entity_id} from event")
    
    def handle_updated(self, channel, entity_id, data):
        if channel == 'product_events':
            delete_cache('product', entity_id)
            invalidate_list_cache('product')
            logger.info(f"Invalidated cache for product {entity_id}")
        elif channel == 'supplier_events':
            delete_cache('supplier', entity_id)
            if data:
                cache_entity('supplier', entity_id, data, ttl=86400)
            logger.info(f"Updated cache for supplier {entity_id}")
    
    def handle_deleted(self, channel, entity_id, data):
        if channel == 'product_events':
            delete_cache('product', entity_id)
            invalidate_list_cache('product')
        elif channel == 'supplier_events':
            delete_cache('supplier', entity_id)


def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)
    db.init_app(flask_app)

    # Attach runtime attributes available to routes
    flask_app.cache_warmed = False
    flask_app.supplier_breaker = CircuitBreaker(failure_threshold=5, timeout=30, name='supplier_service')

    # Register blueprint with product routes
    from routes import bp as product_bp
    flask_app.register_blueprint(product_bp)

    return flask_app


def main():
    logger.info("Starting Product Service...")
    app = create_app()
    
    # Warm cache
    try:
        with app.app_context():
            logger.info("Starting cache warming for products...")
            products = Product.query.all()
            product_dicts = [p.to_dict() for p in products]
            warm_cache_sync('product', product_dicts, ttl=86400)

            # Also warm supplier cache by fetching from supplier service
            logger.info("Warming supplier cache...")
            try:
                response = requests.get(f"{Config.SUPPLIER_SERVICE_URL}/suppliers", timeout=5)
                if response.status_code == 200:
                    suppliers = response.json().get('suppliers', [])
                    warm_cache_sync('supplier', suppliers, ttl=86400)
                    logger.info(f"Warmed {len(suppliers)} suppliers")
            except Exception as e:
                logger.warning(f"Could not warm supplier cache: {e}")

            app.cache_warmed = True
            logger.info(f"Cache warming complete: {len(product_dicts)} products loaded")
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")

    app.event_publisher = EventPublisher()

    app.supervisor = MultiProcessSupervisor()
    app.supervisor.add_process(
        lambda: ProductEventConsumer(),
        max_retries=3,
        retry_delay=5,
        check_interval=5
    )
    app.supervisor.start_all()
    
    def shutdown_handler(signum, frame):
        logger.info("Received shutdown signal, cleaning up...")
        if hasattr(app, 'supervisor') and app.supervisor:
            app.supervisor.stop_all()
        logger.info("Shutdown complete")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    logger.info(f"Product Service ready on port {Config.SERVICE_PORT}")
    
    app.run(host='0.0.0.0', port=Config.SERVICE_PORT, debug=False)


if __name__ == '__main__':
    main()
