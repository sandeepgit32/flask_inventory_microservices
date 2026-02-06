import sys
import os
import logging
import signal
import json
import requests
from flask import Flask, request, jsonify

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from db import db
from models import Storage
from message_queue.event_system import EventPublisher, EventConsumerProcess
from message_queue.cache import warm_cache_sync, cache_entity, get_cached_entity
from message_queue.circuit_breaker import CircuitBreaker
from message_queue.supervisor import MultiProcessSupervisor
from message_queue.redis_config import get_redis_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

event_publisher = None
supervisor = None
cache_warmed = False


class InventoryEventConsumer(EventConsumerProcess):
    """Consumer for stock in/out events"""
    
    def __init__(self, flask_app):
        super().__init__(
            channels=['procurement_stock_in', 'order_stock_out'],
            name='inventory_consumer'
        )
        self.flask_app = flask_app
    
    def _handle_message(self, message):
        """Handle inventory update messages"""
        try:
            channel = message['channel'].decode('utf-8')
            data_str = message['data'].decode('utf-8')
            event_data = json.loads(data_str)
            
            product_id = event_data.get('product_id')
            quantity = event_data.get('quantity')
            
            if not product_id or not quantity:
                logger.warning(f"Invalid inventory event: {event_data}")
                return
            
            with self.flask_app.app_context():
                storage = Storage.query.filter_by(product_id=product_id).first()
                
                if channel == 'procurement_stock_in':
                    if storage:
                        storage.quantity += quantity
                        logger.info(f"Added {quantity} to product {product_id}, new quantity: {storage.quantity}")
                    else:
                        storage = Storage(product_id=product_id, quantity=quantity)
                        db.session.add(storage)
                        logger.info(f"Created new storage for product {product_id} with quantity: {quantity}")
                    
                elif channel == 'order_stock_out':
                    if storage:
                        storage.quantity -= quantity
                        if storage.quantity < 0:
                            storage.quantity = 0
                        logger.info(f"Subtracted {quantity} from product {product_id}, new quantity: {storage.quantity}")
                        
                        if storage.quantity < Config.LOW_STOCK_THRESHOLD:
                            ep = EventPublisher()
                            ep.publish(
                                'inventory_alert',
                                'low_stock',
                                storage.id,
                                {
                                    'product_id': product_id,
                                    'quantity': storage.quantity,
                                    'threshold': Config.LOW_STOCK_THRESHOLD
                                }
                            )
                            logger.warning(f"Low stock alert for product {product_id}: {storage.quantity}")
                    else:
                        logger.warning(f"Cannot subtract stock: product {product_id} not in storage")
                        return
                
                db.session.commit()
                
        except Exception as e:
            logger.error(f"Error handling inventory message: {e}")
            db.session.rollback()


def create_app():
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)
    db.init_app(flask_app)

    # Attach runtime attributes available to routes
    flask_app.cache_warmed = False
    flask_app.product_breaker = CircuitBreaker(failure_threshold=5, timeout=30, name='product_service')

    # Register blueprint with inventory routes
    from routes import bp as inventory_bp
    flask_app.register_blueprint(inventory_bp)

    return flask_app


def main():
    logger.info("Starting Inventory Service...")
    app = create_app()
    
    # Warm cache
    try:
        with app.app_context():
            logger.info("Starting cache warming for inventory...")
            storages = Storage.query.all()
            storage_dicts = [s.to_dict() for s in storages]
            warm_cache_sync('storage', storage_dicts, ttl=86400)

            logger.info("Warming product cache...")
            try:
                response = requests.get(f"{Config.PRODUCT_SERVICE_URL}/products", timeout=5)
                if response.status_code == 200:
                    products = response.json().get('products', [])
                    warm_cache_sync('product', products, ttl=86400)
                    logger.info(f"Warmed {len(products)} products")
            except Exception as e:
                logger.warning(f"Could not warm product cache: {e}")

            app.cache_warmed = True
            logger.info(f"Cache warming complete: {len(storage_dicts)} storage records loaded")
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")
    
    app.event_publisher = EventPublisher()

    app.supervisor = MultiProcessSupervisor()
    app.supervisor.add_process(
        lambda: InventoryEventConsumer(app),
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
    
    logger.info(f"Inventory Service ready on port {Config.SERVICE_PORT}")
    
    app.run(host='0.0.0.0', port=Config.SERVICE_PORT, debug=False)


if __name__ == '__main__':
    main()
