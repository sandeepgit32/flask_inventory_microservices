import logging
from flask import Blueprint, request, jsonify, current_app
from db import db

from models import Storage
from config import Config
from message_queue.cache import cache_entity, get_cached_list, cache_list, get_cached_entity
import requests

logger = logging.getLogger(__name__)

bp = Blueprint('inventory', __name__)


def fetch_product_with_breaker(product_id):
    cached = get_cached_entity('product', product_id)
    if cached:
        return cached

    def fetch_product():
        response = requests.get(f"{Config.PRODUCT_SERVICE_URL}/products/{product_id}", timeout=5)
        if response.status_code == 200:
            return response.json()
        return None

    try:
        product = current_app.product_breaker.call(fetch_product)
        if product:
            cache_entity('product', product_id, product, ttl=86400)
        return product
    except Exception as e:
        logger.error(f"Failed to fetch product {product_id}: {e}")
        return None

@bp.route('/health', methods=['GET'])
def health_check():
    consumer_running = getattr(current_app, 'supervisor', None) and len(current_app.supervisor.supervisors) > 0
    return jsonify({
        'status': 'healthy',
        'service': Config.SERVICE_NAME,
        'cache_warmed': getattr(current_app, 'cache_warmed', False),
        'consumer_running': bool(consumer_running)
    }), 200


@bp.route('/inventory', methods=['GET'])
def get_storages():
    try:
        start = request.args.get('start', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        cache_key = f"page_{start}_limit_{limit}"
        cached = get_cached_list('storage', cache_key)
        if cached:
            return jsonify({'storages': cached, 'start': start, 'limit': limit, 'count': len(cached), 'cached': True}), 200
        storages = Storage.query.offset(start).limit(limit).all()
        result = [s.to_dict() for s in storages]
        cache_list('storage', cache_key, result, ttl=3600)
        return jsonify({'storages': result, 'start': start, 'limit': limit, 'count': len(result)}), 200
    except Exception as e:
        logger.error(f"Error getting storages: {e}")
        return jsonify({'error': 'Failed to fetch storages'}), 500


@bp.route('/inventory/<int:storage_id>', methods=['GET'])
def get_storage(storage_id):
    try:
        s = Storage.query.get(storage_id)
        if not s:
            return jsonify({'error': 'Storage not found'}), 404
        return jsonify(s.to_dict()), 200
    except Exception as e:
        logger.error(f"Error getting storage {storage_id}: {e}")
        return jsonify({'error': 'Failed to fetch storage'}), 500


@bp.route('/inventory', methods=['POST'])
def create_storage():
    try:
        data = request.get_json()
        if not data.get('product_id'):
            return jsonify({'error': 'product_id is required'}), 400
        storage = Storage(product_id=data['product_id'], quantity=data.get('quantity', 0))
        db.session.add(storage)
        db.session.commit()
        cache_entity('storage', storage.id, storage.to_dict(), ttl=3600)
        logger.info(f"Storage created: product {storage.product_id} qty {storage.quantity} (ID {storage.id})")
        return jsonify(storage.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating storage: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create storage'}), 500


@bp.route('/inventory/<int:storage_id>', methods=['PUT'])
def update_storage(storage_id):
    try:
        s = Storage.query.get(storage_id)
        if not s:
            return jsonify({'error': 'Storage not found'}), 404
        data = request.get_json()
        if 'quantity' in data:
            s.quantity = data['quantity']
        db.session.commit()
        logger.info(f"Storage updated: ID {s.id} qty {s.quantity}")
        return jsonify(s.to_dict()), 200
    except Exception as e:
        logger.error(f"Error updating storage {storage_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update storage'}), 500


@bp.route('/inventory/product/<int:product_id>', methods=['GET'])
def get_storages_by_product(product_id):
    try:
        storages = Storage.query.filter_by(product_id=product_id).all()
        return jsonify({'storages': [s.to_dict() for s in storages], 'product_id': product_id, 'count': len(storages)}), 200
    except Exception as e:
        logger.error(f"Error getting storages by product: {e}")
        return jsonify({'error': 'Failed to fetch storages'}), 500