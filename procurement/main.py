import logging
import os
import signal
import sys

import requests
from flask import Flask

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from db import db
from models import Procurements

from message_queue.cache import (
    cache_entity,
    cache_list,
    get_cached_entity,
    get_cached_list,
    warm_cache_sync,
)
from message_queue.circuit_breaker import CircuitBreaker
from message_queue.event_system import EventConsumerProcess, EventPublisher
from message_queue.supervisor import MultiProcessSupervisor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

event_publisher = None
supervisor = None
cache_warmed = False
supplier_breaker = CircuitBreaker(failure_threshold=5, timeout=30, name='supplier_service')
product_breaker = CircuitBreaker(failure_threshold=5, timeout=30, name='product_service')


class ProcurementEventConsumer(EventConsumerProcess):
    """Consumer for supplier and product events"""
    
    def __init__(self):
        super().__init__(
            channels=['supplier_events', 'product_events'],
            name='procurement_consumer'
        )
    
    def handle_created(self, channel, entity_id, data):
        if channel == 'supplier_events':
            cache_entity('supplier', entity_id, data, ttl=86400)
            logger.info(f"Cached supplier {entity_id} from event")
        elif channel == 'product_events':
            cache_entity('product', entity_id, data, ttl=86400)
            logger.info(f"Cached product {entity_id} from event")
    
    def handle_updated(self, channel, entity_id, data):
        if channel == 'supplier_events':
            cache_entity('supplier', entity_id, data, ttl=86400)
        elif channel == 'product_events':
            cache_entity('product', entity_id, data, ttl=86400)


def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)
    db.init_app(flask_app)
    # Attach shared runtime objects so routes and other parts can access them via current_app
    flask_app.supplier_breaker = supplier_breaker
    flask_app.product_breaker = product_breaker
    flask_app.cache_warmed = False
    # Register blueprint containing routes
    from routes import bp as procurement_bp
    flask_app.register_blueprint(procurement_bp)
    return flask_app


# Routes moved to `procurement/routes.py` using a Flask Blueprint
# See `procurement/routes.py` for all route handlers



def warm_cache(app):
    try:
        with app.app_context():
            logger.info("Starting cache warming for procurement...")
            
            # Warm supplier cache
            try:
                response = requests.get(f"{Config.SUPPLIER_SERVICE_URL}/suppliers", timeout=5)
                if response.status_code == 200:
                    suppliers = response.json().get('suppliers', [])
                    warm_cache_sync('supplier', suppliers, ttl=86400)
                    logger.info(f"Warmed {len(suppliers)} suppliers")
            except Exception as e:
                logger.warning(f"Could not warm supplier cache: {e}")
            
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


# fetch_entity_with_breaker moved to `procurement/routes.py`



def shutdown_handler(signum, frame):
    logger.info("Received shutdown signal, cleaning up...")
    if supervisor:
        supervisor.stop_all()
    logger.info("Shutdown complete")
    sys.exit(0)


def main():
    global event_publisher, supervisor
    
    logger.info("Starting Procurement Service...")
    app = create_app()
    
    warm_cache(app)
    
    event_publisher = EventPublisher()
    # expose to routes via current_app
    app.event_publisher = event_publisher

    supervisor = MultiProcessSupervisor()
    # expose supervisor to routes and health checks
    app.supervisor = supervisor
    supervisor.add_process(
        lambda: ProcurementEventConsumer(),
        max_retries=3,
        retry_delay=5,
        check_interval=5
    )
    supervisor.start_all()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    logger.info(f"Procurement Service ready on port {Config.SERVICE_PORT}")
    
    app.run(host='0.0.0.0', port=Config.SERVICE_PORT, debug=False)


if __name__ == '__main__':
    main()
