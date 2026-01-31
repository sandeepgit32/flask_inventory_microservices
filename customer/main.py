import sys
import os
import logging
import signal
from flask import Flask, request, jsonify

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from db import db
from models import Customer
from message_queue.event_system import EventPublisher, EventConsumerProcess
from message_queue.cache import warm_cache_sync, cache_entity, delete_cache, invalidate_list_cache
from message_queue.supervisor import MultiProcessSupervisor

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

event_publisher = None
supervisor = None
cache_warmed = False


class CustomerEventConsumer(EventConsumerProcess):
    """Consumer for customer events"""
    
    def __init__(self):
        super().__init__(channels=['customer_events'], name='customer_consumer')
    
    def handle_updated(self, channel, entity_id, data):
        delete_cache('customer', entity_id)
        invalidate_list_cache('customer')
        logger.info(f"Invalidated cache for customer {entity_id}")
    
    def handle_deleted(self, channel, entity_id, data):
        delete_cache('customer', entity_id)
        invalidate_list_cache('customer')
        logger.info(f"Invalidated cache for customer {entity_id}")


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
            'consumer_running': consumer_running
        }), 200

    @app.route('/customers', methods=['GET'])
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

    @app.route('/customers/<int:customer_id>', methods=['GET'])
    def get_customer(customer_id):
        try:
            customer = Customer.query.get(customer_id)
            if not customer:
                return jsonify({'error': 'Customer not found'}), 404
            return jsonify(customer.to_dict()), 200
        except Exception as e:
            logger.error(f"Error getting customer {customer_id}: {e}")
            return jsonify({'error': 'Failed to fetch customer'}), 500

    @app.route('/customers', methods=['POST'])
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
            if event_publisher:
                event_publisher.publish('customer_events', 'created', customer.id, customer.to_dict())
            
            logger.info(f"Customer created: {customer.name} (ID: {customer.id})")
            return jsonify(customer.to_dict()), 201
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to create customer'}), 500

    @app.route('/customers/<int:customer_id>', methods=['PUT'])
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
            if event_publisher:
                event_publisher.publish('customer_events', 'updated', customer.id, customer.to_dict())
            
            logger.info(f"Customer updated: {customer.name} (ID: {customer.id})")
            return jsonify(customer.to_dict()), 200
        except Exception as e:
            logger.error(f"Error updating customer {customer_id}: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to update customer'}), 500

    @app.route('/customers/<int:customer_id>', methods=['DELETE'])
    def delete_customer(customer_id):
        try:
            customer = Customer.query.get(customer_id)
            if not customer:
                return jsonify({'error': 'Customer not found'}), 404
            
            customer_name = customer.name
            db.session.delete(customer)
            db.session.commit()
            
            if event_publisher:
                event_publisher.publish('customer_events', 'deleted', customer_id, {})
            
            logger.info(f"Customer deleted: {customer_name} (ID: {customer_id})")
            return jsonify({'message': 'Customer deleted successfully'}), 200
        except Exception as e:
            logger.error(f"Error deleting customer {customer_id}: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to delete customer'}), 500

    @app.route('/customers/city/<city>', methods=['GET'])
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


def warm_cache(app):
    global cache_warmed
    try:
        with app.app_context():
            logger.info("Starting cache warming for customers...")
            customers = Customer.query.all()
            customer_dicts = [c.to_dict() for c in customers]
            warm_cache_sync('customer', customer_dicts, ttl=86400)
            cache_warmed = True
            logger.info(f"Cache warming complete: {len(customer_dicts)} customers loaded")
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
    
    logger.info("Starting Customer Service...")
    app = create_app()
    
    warm_cache(app)
    
    event_publisher = EventPublisher()
    
    supervisor = MultiProcessSupervisor()
    supervisor.add_process(
        lambda: CustomerEventConsumer(),
        max_retries=3,
        retry_delay=5,
        check_interval=5
    )
    supervisor.start_all()
    
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    logger.info(f"Customer Service ready on port {Config.SERVICE_PORT}")
    
    app.run(host='0.0.0.0', port=Config.SERVICE_PORT, debug=False)


if __name__ == '__main__':
    main()
