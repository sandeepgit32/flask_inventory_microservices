import logging
from flask import Blueprint, request, jsonify, current_app
from db import db

from models import Supplier
from config import Config
from message_queue.cache import cache_entity, delete_cache, invalidate_list_cache, warm_cache_sync

logger = logging.getLogger(__name__)

bp = Blueprint('supplier', __name__)


@bp.route('/health', methods=['GET'])
def health_check():
    consumer_running = getattr(current_app, 'supervisor', None) and len(current_app.supervisor.supervisors) > 0
    return jsonify({
        'status': 'healthy',
        'service': Config.SERVICE_NAME,
        'cache_warmed': getattr(current_app, 'cache_warmed', False),
        'consumer_running': bool(consumer_running)
    }), 200


@bp.route('/suppliers', methods=['GET'])
def get_suppliers():
    try:
        start = request.args.get('start', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        suppliers = Supplier.query.offset(start).limit(limit).all()
        return jsonify({
            'suppliers': [s.to_dict() for s in suppliers],
            'start': start,
            'limit': limit,
            'count': len(suppliers)
        }), 200
    except Exception as e:
        logger.error(f"Error getting suppliers: {e}")
        return jsonify({'error': 'Failed to fetch suppliers'}), 500


@bp.route('/suppliers/<int:supplier_id>', methods=['GET'])
def get_supplier(supplier_id):
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({'error': 'Supplier not found'}), 404
        return jsonify(supplier.to_dict()), 200
    except Exception as e:
        logger.error(f"Error getting supplier {supplier_id}: {e}")
        return jsonify({'error': 'Failed to fetch supplier'}), 500


@bp.route('/suppliers', methods=['POST'])
def create_supplier():
    try:
        data = request.get_json()
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        if Supplier.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Supplier name already exists'}), 409
        supplier = Supplier(
            name=data['name'],
            city=data.get('city'),
            zipcode=data.get('zipcode'),
            contact_person=data.get('contact_person'),
            phone=data.get('phone'),
            email=data.get('email')
        )
        db.session.add(supplier)
        db.session.commit()
        cache_entity('supplier', supplier.id, supplier.to_dict(), ttl=86400)
        invalidate_list_cache('supplier')
        event_publisher = getattr(current_app, 'event_publisher', None)
        if event_publisher:
            event_publisher.publish('supplier_events', 'created', supplier.id, supplier.to_dict())
        logger.info(f"Supplier created: {supplier.name} (ID: {supplier.id})")
        return jsonify(supplier.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating supplier: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create supplier'}), 500


@bp.route('/suppliers/<int:supplier_id>', methods=['PUT'])
def update_supplier(supplier_id):
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({'error': 'Supplier not found'}), 404
        data = request.get_json()
        if 'name' in data:
            supplier.name = data['name']
        if 'city' in data:
            supplier.city = data['city']
        if 'zipcode' in data:
            supplier.zipcode = data['zipcode']
        if 'contact_person' in data:
            supplier.contact_person = data['contact_person']
        if 'phone' in data:
            supplier.phone = data['phone']
        if 'email' in data:
            supplier.email = data['email']
        db.session.commit()
        event_publisher = getattr(current_app, 'event_publisher', None)
        if event_publisher:
            event_publisher.publish('supplier_events', 'updated', supplier.id, supplier.to_dict())
        logger.info(f"Supplier updated: {supplier.name} (ID: {supplier.id})")
        return jsonify(supplier.to_dict()), 200
    except Exception as e:
        logger.error(f"Error updating supplier {supplier_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update supplier'}), 500


@bp.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
def delete_supplier(supplier_id):
    try:
        supplier = Supplier.query.get(supplier_id)
        if not supplier:
            return jsonify({'error': 'Supplier not found'}), 404
        supplier_name = supplier.name
        db.session.delete(supplier)
        db.session.commit()
        event_publisher = getattr(current_app, 'event_publisher', None)
        if event_publisher:
            event_publisher.publish('supplier_events', 'deleted', supplier_id, {})
        logger.info(f"Supplier deleted: {supplier_name} (ID: {supplier_id})")
        return jsonify({'message': 'Supplier deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting supplier {supplier_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete supplier'}), 500


@bp.route('/suppliers/city/<city>', methods=['GET'])
def get_suppliers_by_city(city):
    try:
        suppliers = Supplier.query.filter_by(city=city).all()
        return jsonify({
            'suppliers': [s.to_dict() for s in suppliers],
            'city': city,
            'count': len(suppliers)
        }), 200
    except Exception as e:
        logger.error(f"Error getting suppliers by city: {e}")
        return jsonify({'error': 'Failed to fetch suppliers'}), 500
