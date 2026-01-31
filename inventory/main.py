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
product_breaker = CircuitBreaker(failure_threshold=5, timeout=30, name='product_service')


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
    register_routes(flask_app)
    return flask_app


def fetch_product_with_breaker(product_id):
    """Fetch product from cache or service with circuit breaker"""
    cached = get_cached_entity('product', product_id)
    if cached:
        return cached
    
    def fetch_product():
        response = requests.get(
            f"{Config.PRODUCT_SERVICE_URL}/products/{product_id}",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    
    try:
        product = product_breaker.call(fetch_product)
        if product:
            cache_entity('product', product_id, product, ttl=86400)
        return product
    except Exception as e:
        logger.error(f"Failed to fetch product {product_id}: {e}")
        return None


def register_routes(app):
    """Register all routes on the Flask app"""
    
    @app.route('/health', methods=['GET'])
    def health_check():
        consumer_running = supervisor and len(supervisor.supervisors) > 0
        return jsonify({
            'status': 'healthy',
            'service': Config.SERVICE_NAME,
            'cache_warmed': cache_warmed,
            'consumer_running': consumer_running,
            'product_breaker': product_breaker.get_state()
        }), 200

    @app.route('/storages', methods=['GET'])
    @app.route('/inventory', methods=['GET'])
    def get_storages():
        try:
            start = request.args.get('start', 0, type=int)
            limit = request.args.get('limit', 50, type=int)
            storages = Storage.query.offset(start).limit(limit).all()
            
            result = []
            for s in storages:
                storage_dict = s.to_dict()
                product = fetch_product_with_breaker(s.product_id)
                if product:
                    storage_dict['product'] = product
                result.append(storage_dict)
            
            return jsonify({
                'storages': result,
                'start': start,
                'limit': limit,
                'count': len(result)
            }), 200
        except Exception as e:
            logger.error(f"Error getting storages: {e}")
            return jsonify({'error': 'Failed to fetch storages'}), 500

    @app.route('/storages/<int:storage_id>', methods=['GET'])
    @app.route('/inventory/<int:storage_id>', methods=['GET'])
    def get_storage(storage_id):
        try:
            storage = Storage.query.get(storage_id)
            if not storage:
                return jsonify({'error': 'Storage not found'}), 404
            
            storage_dict = storage.to_dict()
            product = fetch_product_with_breaker(storage.product_id)
            if product:
                storage_dict['product'] = product
            
            return jsonify(storage_dict), 200
        except Exception as e:
            logger.error(f"Error getting storage {storage_id}: {e}")
            return jsonify({'error': 'Failed to fetch storage'}), 500

    @app.route('/storages', methods=['POST'])
    @app.route('/inventory', methods=['POST'])
    def create_storage():
        """Create new storage record"""
        try:
            data = request.get_json()
            
            if not data.get('product_id'):
                return jsonify({'error': 'product_id is required'}), 400
            
            existing = Storage.query.filter_by(product_id=data['product_id']).first()
            if existing:
                return jsonify({'error': 'Storage already exists for this product'}), 409
            
            storage = Storage(
                product_id=data['product_id'],
                quantity=data.get('quantity', 0)
            )
            
            db.session.add(storage)
            db.session.commit()
            
            logger.info(f"Storage created for product {storage.product_id}")
            return jsonify(storage.to_dict()), 201
        except Exception as e:
            logger.error(f"Error creating storage: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to create storage'}), 500

    @app.route('/storages/<int:storage_id>', methods=['PUT'])
    @app.route('/inventory/<int:storage_id>', methods=['PUT'])
    def update_storage(storage_id):
        """Update storage quantity manually"""
        try:
            storage = Storage.query.get(storage_id)
            if not storage:
                return jsonify({'error': 'Storage not found'}), 404
            
            data = request.get_json()
            
            if 'quantity' in data:
                storage.quantity = data['quantity']
            
            db.session.commit()
            
            logger.info(f"Storage updated: product {storage.product_id}, quantity: {storage.quantity}")
            return jsonify(storage.to_dict()), 200
        except Exception as e:
            logger.error(f"Error updating storage {storage_id}: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to update storage'}), 500

    @app.route('/storages/product/<int:product_id>', methods=['GET'])
    @app.route('/inventory/product/<int:product_id>', methods=['GET'])
    def get_storage_by_product(product_id):
        """Get storage for a specific product"""
        try:
            storage = Storage.query.filter_by(product_id=product_id).first()
            if not storage:
                return jsonify({'error': 'Storage not found for this product'}), 404
            
            storage_dict = storage.to_dict()
            product = fetch_product_with_breaker(product_id)
            if product:
                storage_dict['product'] = product
            
            return jsonify(storage_dict), 200
        except Exception as e:
            logger.error(f"Error getting storage for product {product_id}: {e}")
            return jsonify({'error': 'Failed to fetch storage'}), 500


def warm_cache(app):
    global cache_warmed
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
            
            cache_warmed = True
            logger.info(f"Cache warming complete: {len(storage_dicts)} storage records loaded")
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")


def shutdown_handler(signum, frame):
    logger.info("Received shutdown signal, cleaning up...")
    if supervisor:
        supervisor.stop_all()
    logger.info("Shutdown complete")
    sys.exit(0)


def main():
    global event_publisher, supervisor
    
    logger.info("Starting Inventory Service...")
    app = create_app()
    
    warm_cache(app)
    
    event_publisher = EventPublisher()
    
    supervisor = MultiProcessSupervisor()
    supervisor.add_process(
        lambda: InventoryEventConsumer(app),
        max_retries=3,
        retry_delay=5,
        check_interval=5
    )
    supervisor.start_all()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    logger.info(f"Inventory Service ready on port {Config.SERVICE_PORT}")
    
    app.run(host='0.0.0.0', port=Config.SERVICE_PORT, debug=False)


if __name__ == '__main__':
    main()
