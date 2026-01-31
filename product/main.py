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
supplier_breaker = CircuitBreaker(failure_threshold=5, timeout=30, name='supplier_service')


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
    register_routes(flask_app)
    return flask_app


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
            'supplier_breaker': supplier_breaker.get_state()
        }), 200

    @app.route('/products', methods=['GET'])
    def get_products():
        try:
            start = request.args.get('start', 0, type=int)
            limit = request.args.get('limit', 50, type=int)
            products = Product.query.offset(start).limit(limit).all()
            
            # Enrich with supplier data
            result = []
            for p in products:
                product_dict = p.to_dict()
                if p.supplier_id:
                    supplier = fetch_supplier_with_breaker(p.supplier_id)
                    if supplier:
                        product_dict['supplier'] = supplier
                result.append(product_dict)
            
            return jsonify({
                'products': result,
                'start': start,
                'limit': limit,
                'count': len(result)
            }), 200
        except Exception as e:
            logger.error(f"Error getting products: {e}")
            return jsonify({'error': 'Failed to fetch products'}), 500

    @app.route('/products/<int:product_id>', methods=['GET'])
    def get_product(product_id):
        try:
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            
            product_dict = product.to_dict()
            if product.supplier_id:
                supplier = fetch_supplier_with_breaker(product.supplier_id)
                if supplier:
                    product_dict['supplier'] = supplier
            
            return jsonify(product_dict), 200
        except Exception as e:
            logger.error(f"Error getting product {product_id}: {e}")
            return jsonify({'error': 'Failed to fetch product'}), 500

    @app.route('/products', methods=['POST'])
    def create_product():
        try:
            data = request.get_json()
            
            if not data.get('product_code') or not data.get('name'):
                return jsonify({'error': 'product_code and name are required'}), 400
            
            if Product.query.filter_by(product_code=data['product_code']).first():
                return jsonify({'error': 'Product code already exists'}), 409
            
            if Product.query.filter_by(name=data['name']).first():
                return jsonify({'error': 'Product name already exists'}), 409
            
            product = Product(
                product_code=data['product_code'],
                name=data['name'],
                category=data.get('category'),
                price_buy=data.get('price_buy'),
                price_sell=data.get('price_sell'),
                measure_unit=data.get('measure_unit'),
                supplier_id=data.get('supplier_id')
            )
            
            db.session.add(product)
            db.session.commit()
            
            cache_entity('product', product.id, product.to_dict(), ttl=86400)
            invalidate_list_cache('product')
            if event_publisher:
                event_publisher.publish('product_events', 'created', product.id, product.to_dict())
            
            logger.info(f"Product created: {product.name} (ID: {product.id})")
            return jsonify(product.to_dict()), 201
        except Exception as e:
            logger.error(f"Error creating product: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to create product'}), 500

    @app.route('/products/<int:product_id>', methods=['PUT'])
    def update_product(product_id):
        try:
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            
            data = request.get_json()
            
            if 'product_code' in data:
                product.product_code = data['product_code']
            if 'name' in data:
                product.name = data['name']
            if 'category' in data:
                product.category = data['category']
            if 'price_buy' in data:
                product.price_buy = data['price_buy']
            if 'price_sell' in data:
                product.price_sell = data['price_sell']
            if 'measure_unit' in data:
                product.measure_unit = data['measure_unit']
            if 'supplier_id' in data:
                product.supplier_id = data['supplier_id']
            
            db.session.commit()
            if event_publisher:
                event_publisher.publish('product_events', 'updated', product.id, product.to_dict())
            
            logger.info(f"Product updated: {product.name} (ID: {product.id})")
            return jsonify(product.to_dict()), 200
        except Exception as e:
            logger.error(f"Error updating product {product_id}: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to update product'}), 500

    @app.route('/products/<int:product_id>', methods=['DELETE'])
    def delete_product(product_id):
        try:
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Product not found'}), 404
            
            product_name = product.name
            db.session.delete(product)
            db.session.commit()
            
            if event_publisher:
                event_publisher.publish('product_events', 'deleted', product_id, {})
            
            logger.info(f"Product deleted: {product_name} (ID: {product_id})")
            return jsonify({'message': 'Product deleted successfully'}), 200
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to delete product'}), 500


def warm_cache(app):
    global cache_warmed
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
            
            cache_warmed = True
            logger.info(f"Cache warming complete: {len(product_dicts)} products loaded")
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")


def fetch_supplier_with_breaker(supplier_id):
    """Fetch supplier from cache or service with circuit breaker"""
    # Try cache first
    cached = get_cached_entity('supplier', supplier_id)
    if cached:
        return cached
    
    # Fetch from supplier service with circuit breaker
    def fetch_supplier():
        response = requests.get(
            f"{Config.SUPPLIER_SERVICE_URL}/suppliers/{supplier_id}",
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
        return None
    
    try:
        supplier = supplier_breaker.call(fetch_supplier)
        if supplier:
            cache_entity('supplier', supplier_id, supplier, ttl=86400)
        return supplier
    except Exception as e:
        logger.error(f"Failed to fetch supplier {supplier_id}: {e}")
        return None


def shutdown_handler(signum, frame):
    logger.info("Received shutdown signal, cleaning up...")
    if supervisor:
        supervisor.stop_all()
    logger.info("Shutdown complete")
    sys.exit(0)


def main():
    global event_publisher, supervisor
    
    logger.info("Starting Product Service...")
    app = create_app()
    
    warm_cache(app)
    
    event_publisher = EventPublisher()
    
    supervisor = MultiProcessSupervisor()
    supervisor.add_process(
        lambda: ProductEventConsumer(),
        max_retries=3,
        retry_delay=5,
        check_interval=5
    )
    supervisor.start_all()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    logger.info(f"Product Service ready on port {Config.SERVICE_PORT}")
    
    app.run(host='0.0.0.0', port=Config.SERVICE_PORT, debug=False)


if __name__ == '__main__':
    main()
