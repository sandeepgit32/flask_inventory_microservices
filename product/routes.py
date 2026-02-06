import logging
import requests
from flask import Blueprint, request, jsonify, current_app
from db import db

from models import Product
from config import Config
from message_queue.cache import cache_entity, delete_cache, invalidate_list_cache, warm_cache_sync, get_cached_entity

logger = logging.getLogger(__name__)

bp = Blueprint('product', __name__) 


@bp.route('/health', methods=['GET'])
def health_check():
    consumer_running = getattr(current_app, 'supervisor', None) and len(current_app.supervisor.supervisors) > 0
    return jsonify({
        'status': 'healthy',
        'service': Config.SERVICE_NAME,
        'cache_warmed': getattr(current_app, 'cache_warmed', False),
        'consumer_running': bool(consumer_running),
        'supplier_breaker': current_app.supplier_breaker.get_state()
    }), 200


@bp.route('/products', methods=['GET'])
def get_products():
    try:
        start = request.args.get('start', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        products = Product.query.offset(start).limit(limit).all()
        result = []
        for p in products:
            product_dict = p.to_dict()
            if p.supplier_id:
                supplier = fetch_supplier_with_breaker(p.supplier_id)
                if supplier:
                    product_dict['supplier'] = supplier
            result.append(product_dict)
        return jsonify({'products': result, 'start': start, 'limit': limit, 'count': len(result)}), 200
    except Exception as e:
        logger.error(f"Error getting products: {e}")
        return jsonify({'error': 'Failed to fetch products'}), 500


@bp.route('/products/<int:product_id>', methods=['GET'])
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


@bp.route('/products', methods=['POST'])
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
        event_publisher = getattr(current_app, 'event_publisher', None)
        if event_publisher:
            event_publisher.publish('product_events', 'created', product.id, product.to_dict())
        logger.info(f"Product created: {product.name} (ID: {product.id})")
        return jsonify(product.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating product: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create product'}), 500


@bp.route('/products/<int:product_id>', methods=['PUT'])
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
        event_publisher = getattr(current_app, 'event_publisher', None)
        if event_publisher:
            event_publisher.publish('product_events', 'updated', product.id, product.to_dict())
        logger.info(f"Product updated: {product.name} (ID: {product.id})")
        return jsonify(product.to_dict()), 200
    except Exception as e:
        logger.error(f"Error updating product {product_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update product'}), 500


@bp.route('/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Product not found'}), 404
        product_name = product.name
        db.session.delete(product)
        db.session.commit()
        event_publisher = getattr(current_app, 'event_publisher', None)
        if event_publisher:
            event_publisher.publish('product_events', 'deleted', product_id, {})
        logger.info(f"Product deleted: {product_name} (ID: {product_id})")
        return jsonify({'message': 'Product deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting product {product_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete product'}), 500


# Helper moved here

def fetch_supplier_with_breaker(supplier_id):
    cached = get_cached_entity('supplier', supplier_id)
    if cached:
        return cached

    def fetch_supplier():
        response = requests.get(f"{Config.SUPPLIER_SERVICE_URL}/suppliers/{supplier_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None

    try:
        supplier = current_app.supplier_breaker.call(fetch_supplier)
        if supplier:
            cache_entity('supplier', supplier_id, supplier, ttl=86400)
        return supplier
    except Exception as e:
        logger.error(f"Failed to fetch supplier {supplier_id}: {e}")
        return None