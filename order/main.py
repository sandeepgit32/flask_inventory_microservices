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
from models import CustomerTransaction
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
            'customer_breaker': customer_breaker.get_state(),
            'product_breaker': product_breaker.get_state()
        }), 200

    @app.route('/orders', methods=['GET'])
    @app.route('/customertransactions', methods=['GET'])
    def get_orders():
        try:
            start = request.args.get('start', 0, type=int)
            limit = request.args.get('limit', 50, type=int)
            
            # Check cache first
            cache_key = f"page_{start}_limit_{limit}"
            cached = get_cached_list('order', cache_key)
            if cached:
                return jsonify({
                    'orders': cached,
                    'start': start,
                    'limit': limit,
                    'count': len(cached),
                    'cached': True
                }), 200
            
            transactions = CustomerTransaction.query.offset(start).limit(limit).all()
            
            # Enrich with customer and product data
            result = []
            for t in transactions:
                tx_dict = t.to_dict()
                
                if t.customer_id:
                    customer = fetch_entity_with_breaker(
                        'customer', t.customer_id, 
                        Config.CUSTOMER_SERVICE_URL, customer_breaker
                    )
                    if customer:
                        tx_dict['customer'] = customer
                
                if t.product_id:
                    product = fetch_entity_with_breaker(
                        'product', t.product_id,
                        Config.PRODUCT_SERVICE_URL, product_breaker
                    )
                    if product:
                        tx_dict['product'] = product
                
                # Cache individual enriched record
                cache_entity('order', t.id, tx_dict, ttl=3600)
                result.append(tx_dict)
            
            # Cache the list
            cache_list('order', cache_key, result, ttl=3600)
            
            return jsonify({
                'orders': result,
                'start': start,
                'limit': limit,
                'count': len(result)
            }), 200
        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return jsonify({'error': 'Failed to fetch orders'}), 500

    @app.route('/orders', methods=['POST'])
    @app.route('/customertransactions', methods=['POST'])
    def create_order():
        try:
            data = request.get_json()
            
            if not data.get('customer_id') or not data.get('product_id'):
                return jsonify({'error': 'customer_id and product_id are required'}), 400
            
            # Fetch customer and product data for denormalization
            customer = fetch_entity_with_breaker(
                'customer', data['customer_id'],
                Config.CUSTOMER_SERVICE_URL, customer_breaker
            )
            product = fetch_entity_with_breaker(
                'product', data['product_id'],
                Config.PRODUCT_SERVICE_URL, product_breaker
            )
            
            if not customer or not product:
                return jsonify({'error': 'Invalid customer_id or product_id'}), 400
            
            # Create transaction with denormalized data
            transaction = CustomerTransaction(
                customer_id=data['customer_id'],
                product_id=data['product_id'],
                customer_name=customer.get('name'),
                city=customer.get('city'),
                zipcode=customer.get('zipcode'),
                contact_person=customer.get('contact_person'),
                phone=customer.get('phone'),
                email=customer.get('email'),
                product_code=product.get('product_code'),
                product_name=product.get('name'),
                product_category=product.get('category'),
                unit_price=data.get('unit_price'),
                quantity=data.get('quantity'),
                total_cost=data.get('quantity', 0) * data.get('unit_price', 0),
                measure_unit=product.get('measure_unit')
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            # Publish stock-out event to inventory service
            if event_publisher:
                event_publisher.publish(
                    'order_stock_out',
                    'stock_out',
                    transaction.id,
                    {
                        'product_id': transaction.product_id,
                        'quantity': transaction.quantity
                    }
                )
            
            logger.info(f"Order created: ID {transaction.id}, product {transaction.product_id}, qty {transaction.quantity}")
            
            return jsonify(transaction.to_dict(
                include_relations=True,
                customer_data=customer,
                product_data=product
            )), 201
            
        except Exception as e:
            logger.error(f"Error creating order: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to create order'}), 500

    @app.route('/orders/product/<int:product_id>', methods=['GET'])
    @app.route('/customertransactions/product/<int:product_id>', methods=['GET'])
    def get_orders_by_product(product_id):
        try:
            transactions = CustomerTransaction.query.filter_by(product_id=product_id).all()
            return jsonify({
                'orders': [t.to_dict() for t in transactions],
                'product_id': product_id,
                'count': len(transactions)
            }), 200
        except Exception as e:
            logger.error(f"Error getting orders by product: {e}")
            return jsonify({'error': 'Failed to fetch orders'}), 500

    @app.route('/orders/customer/<int:customer_id>', methods=['GET'])
    @app.route('/customertransactions/customer/<int:customer_id>', methods=['GET'])
    def get_orders_by_customer(customer_id):
        try:
            transactions = CustomerTransaction.query.filter_by(customer_id=customer_id).all()
            return jsonify({
                'orders': [t.to_dict() for t in transactions],
                'customer_id': customer_id,
                'count': len(transactions)
            }), 200
        except Exception as e:
            logger.error(f"Error getting orders by customer: {e}")
            return jsonify({'error': 'Failed to fetch orders'}), 500


def warm_cache(app):
    global cache_warmed
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
            
            cache_warmed = True
            logger.info("Cache warming complete")
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")


def fetch_entity_with_breaker(entity_type, entity_id, service_url, breaker):
    """Fetch entity from cache or service with circuit breaker"""
    cached = get_cached_entity(entity_type, entity_id)
    if cached:
        return cached
    
    def fetch():
        response = requests.get(f"{service_url}/{entity_type}s/{entity_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None
    
    try:
        entity = breaker.call(fetch)
        if entity:
            cache_entity(entity_type, entity_id, entity, ttl=86400)
        return entity
    except Exception as e:
        logger.error(f"Failed to fetch {entity_type} {entity_id}: {e}")
        return None


def shutdown_handler(signum, frame):
    logger.info("Received shutdown signal, cleaning up...")
    if supervisor:
        supervisor.stop_all()
    logger.info("Shutdown complete")
    sys.exit(0)


def main():
    global event_publisher, supervisor
    
    logger.info("Starting Order Service...")
    app = create_app()
    
    warm_cache(app)
    
    event_publisher = EventPublisher()
    
    supervisor = MultiProcessSupervisor()
    supervisor.add_process(
        lambda: OrderEventConsumer(),
        max_retries=3,
        retry_delay=5,
        check_interval=5
    )
    supervisor.start_all()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    logger.info(f"Order Service ready on port {Config.SERVICE_PORT}")
    
    app.run(host='0.0.0.0', port=Config.SERVICE_PORT, debug=False)


if __name__ == '__main__':
    main()
