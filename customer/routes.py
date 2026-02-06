import logging
from flask import Blueprint, request, jsonify, current_app
from db import db

from models import Customer
from config import Config
from message_queue.cache import cache_entity, delete_cache, invalidate_list_cache, warm_cache_sync

logger = logging.getLogger(__name__)

bp = Blueprint('customer', __name__)


@bp.route('/health', methods=['GET'])
def health_check():
    consumer_running = getattr(current_app, 'supervisor', None) and len(current_app.supervisor.supervisors) > 0
    return jsonify({
        'status': 'healthy',
        'service': Config.SERVICE_NAME,
        'cache_warmed': getattr(current_app, 'cache_warmed', False),
        'consumer_running': bool(consumer_running)
    }), 200


@bp.route('/customers', methods=['GET'])
def get_customers():
    try:
        start = request.args.get('start', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        customers = Customer.query.offset(start).limit(limit).all()
        return jsonify({
            'customers': [c.to_dict() for c in customers],
            'start': start,
            'limit': limit,
            'count': len(customers)
        }), 200
    except Exception as e:
        logger.error(f"Error getting customers: {e}")
        return jsonify({'error': 'Failed to fetch customers'}), 500


@bp.route('/customers/<int:customer_id>', methods=['GET'])
def get_customer(customer_id):
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        return jsonify(customer.to_dict()), 200
    except Exception as e:
        logger.error(f"Error getting customer {customer_id}: {e}")
        return jsonify({'error': 'Failed to fetch customer'}), 500


@bp.route('/customers', methods=['POST'])
def create_customer():
    try:
        data = request.get_json()
        if not data.get('name'):
            return jsonify({'error': 'Name is required'}), 400
        if Customer.query.filter_by(name=data['name']).first():
            return jsonify({'error': 'Customer name already exists'}), 409
        customer = Customer(
            name=data['name'],
            city=data.get('city'),
            zipcode=data.get('zipcode'),
            contact_person=data.get('contact_person'),
            phone=data.get('phone'),
            email=data.get('email')
        )
        db.session.add(customer)
        db.session.commit()
        cache_entity('customer', customer.id, customer.to_dict(), ttl=86400)
        invalidate_list_cache('customer')
        event_publisher = getattr(current_app, 'event_publisher', None)
        if event_publisher:
            event_publisher.publish('customer_events', 'created', customer.id, customer.to_dict())
        logger.info(f"Customer created: {customer.name} (ID: {customer.id})")
        return jsonify(customer.to_dict()), 201
    except Exception as e:
        logger.error(f"Error creating customer: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to create customer'}), 500


@bp.route('/customers/<int:customer_id>', methods=['PUT'])
def update_customer(customer_id):
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        data = request.get_json()
        if 'name' in data:
            customer.name = data['name']
        if 'city' in data:
            customer.city = data['city']
        if 'zipcode' in data:
            customer.zipcode = data['zipcode']
        if 'contact_person' in data:
            customer.contact_person = data['contact_person']
        if 'phone' in data:
            customer.phone = data['phone']
        if 'email' in data:
            customer.email = data['email']
        db.session.commit()
        event_publisher = getattr(current_app, 'event_publisher', None)
        if event_publisher:
            event_publisher.publish('customer_events', 'updated', customer.id, customer.to_dict())
        logger.info(f"Customer updated: {customer.name} (ID: {customer.id})")
        return jsonify(customer.to_dict()), 200
    except Exception as e:
        logger.error(f"Error updating customer {customer_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update customer'}), 500


@bp.route('/customers/<int:customer_id>', methods=['DELETE'])
def delete_customer(customer_id):
    try:
        customer = Customer.query.get(customer_id)
        if not customer:
            return jsonify({'error': 'Customer not found'}), 404
        customer_name = customer.name
        db.session.delete(customer)
        db.session.commit()
        event_publisher = getattr(current_app, 'event_publisher', None)
        if event_publisher:
            event_publisher.publish('customer_events', 'deleted', customer_id, {})
        logger.info(f"Customer deleted: {customer_name} (ID: {customer_id})")
        return jsonify({'message': 'Customer deleted successfully'}), 200
    except Exception as e:
        logger.error(f"Error deleting customer {customer_id}: {e}")
        db.session.rollback()
        return jsonify({'error': 'Failed to delete customer'}), 500


@bp.route('/customers/city/<city>', methods=['GET'])
def get_customers_by_city(city):
    try:
        customers = Customer.query.filter_by(city=city).all()
        return jsonify({
            'customers': [c.to_dict() for c in customers],
            'city': city,
            'count': len(customers)
        }), 200
    except Exception as e:
        logger.error(f"Error getting customers by city: {e}")
        return jsonify({'error': 'Failed to fetch customers'}), 500