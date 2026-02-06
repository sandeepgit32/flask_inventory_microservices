from flask import Blueprint, request, jsonify, current_app
import logging
import requests
from db import db
from models import Orders
from config import Config
from message_queue.cache import (cache_entity, get_cached_entity,
                                  cache_list, get_cached_list)

logger = logging.getLogger(__name__)

bp = Blueprint('order', __name__)

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

@bp.route('/health', methods=['GET'])
def health_check():
    supervisor = getattr(current_app, 'supervisor', None)
    consumer_running = supervisor and len(supervisor.supervisors) > 0
    return jsonify({
        'status': 'healthy',
        'service': Config.SERVICE_NAME,
        'cache_warmed': getattr(current_app, 'cache_warmed', False),
        'consumer_running': consumer_running,
        'customer_breaker': current_app.customer_breaker.get_state(),
        'product_breaker': current_app.product_breaker.get_state()
    }), 200

@bp.route('/orders', methods=['GET'])
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
        
        transactions = Orders.query.offset(start).limit(limit).all()
        
        # Enrich with customer and product data
        result = []
        for t in transactions:
            tx_dict = t.to_dict()
            
            if t.customer_id:
                customer = fetch_entity_with_breaker(
                    'customer', t.customer_id, 
                    Config.CUSTOMER_SERVICE_URL, current_app.customer_breaker
                )
                if customer:
                    tx_dict['customer'] = customer
            
            if t.product_id:
                product = fetch_entity_with_breaker(
                    'product', t.product_id,
                    Config.PRODUCT_SERVICE_URL, current_app.product_breaker
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

@bp.route('/orders', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        
        if not data.get('customer_id') or not data.get('product_id'):
            return jsonify({'error': 'customer_id and product_id are required'}), 400
        
        # Fetch customer and product data for denormalization
        customer = fetch_entity_with_breaker(
            'customer', data['customer_id'],
            Config.CUSTOMER_SERVICE_URL, current_app.customer_breaker
        )
        product = fetch_entity_with_breaker(
            'product', data['product_id'],
            Config.PRODUCT_SERVICE_URL, current_app.product_breaker
        )
        
        if not customer or not product:
            return jsonify({'error': 'Invalid customer_id or product_id'}), 400
        
        quantity = data.get('quantity', 0)
        unit_price = product.get('price_sell', 0)
        
        # Create normalized transaction (store foreign keys only)
        transaction = Orders(
            customer_id=data['customer_id'],
            product_id=data['product_id'],
            quantity=quantity,
            total_cost=quantity * unit_price
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        # Publish stock-out event to inventory service
        event_publisher = getattr(current_app, 'event_publisher', None)
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

@bp.route('/orders/product/<int:product_id>', methods=['GET'])
def get_orders_by_product(product_id):
    try:
        transactions = Orders.query.filter_by(product_id=product_id).all()
        return jsonify({
            'orders': [t.to_dict() for t in transactions],
            'product_id': product_id,
            'count': len(transactions)
        }), 200
    except Exception as e:
        logger.error(f"Error getting orders by product: {e}")
        return jsonify({'error': 'Failed to fetch orders'}), 500

@bp.route('/orders/customer/<int:customer_id>', methods=['GET'])
def get_orders_by_customer(customer_id):
    try:
        transactions = Orders.query.filter_by(customer_id=customer_id).all()
        return jsonify({
            'orders': [t.to_dict() for t in transactions],
            'customer_id': customer_id,
            'count': len(transactions)
        }), 200
    except Exception as e:
        logger.error(f"Error getting orders by customer: {e}")
        return jsonify({'error': 'Failed to fetch orders'}), 500
