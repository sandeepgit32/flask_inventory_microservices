import sys
import os
import logging
import signal
from flask import Flask, request, jsonify

# Add parent directory to path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from db import db
from models import Supplier
from message_queue.event_system import EventPublisher, EventConsumerProcess
from message_queue.cache import warm_cache_sync, cache_entity, delete_cache, invalidate_list_cache
from message_queue.supervisor import MultiProcessSupervisor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
event_publisher = None
supervisor = None
cache_warmed = False


class SupplierEventConsumer(EventConsumerProcess):
    """Consumer for supplier events (self-published for cache invalidation)"""
    
    def __init__(self):
        super().__init__(channels=['supplier_events'], name='supplier_consumer')
    
    def handle_updated(self, channel, entity_id, data):
        delete_cache('supplier', entity_id)
        invalidate_list_cache('supplier')
        logger.info(f"Invalidated cache for supplier {entity_id}")
    
    def handle_deleted(self, channel, entity_id, data):
        delete_cache('supplier', entity_id)
        invalidate_list_cache('supplier')
        logger.info(f"Invalidated cache for supplier {entity_id}")


def create_app():
    """Create and configure Flask application"""
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)
    
    # Initialize database
    db.init_app(flask_app)
    
    # Register routes
    register_routes(flask_app)
    
    return flask_app


def register_routes(app):
    """Register all routes on the Flask app"""
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        consumer_running = supervisor and len(supervisor.supervisors) > 0
        return jsonify({
            'status': 'healthy',
            'service': Config.SERVICE_NAME,
            'cache_warmed': cache_warmed,
            'consumer_running': consumer_running
        }), 200

    @app.route('/suppliers', methods=['GET'])
    def get_suppliers():
        """Get all suppliers with pagination"""
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

    @app.route('/suppliers/<int:supplier_id>', methods=['GET'])
    def get_supplier(supplier_id):
        """Get single supplier"""
        try:
            supplier = Supplier.query.get(supplier_id)
            
            if not supplier:
                return jsonify({'error': 'Supplier not found'}), 404
            
            return jsonify(supplier.to_dict()), 200
            
        except Exception as e:
            logger.error(f"Error getting supplier {supplier_id}: {e}")
            return jsonify({'error': 'Failed to fetch supplier'}), 500

    @app.route('/suppliers', methods=['POST'])
    def create_supplier():
        """Create new supplier"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('name'):
                return jsonify({'error': 'Name is required'}), 400
            
            # Check if supplier exists
            if Supplier.query.filter_by(name=data['name']).first():
                return jsonify({'error': 'Supplier name already exists'}), 409
            
            # Create supplier
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
            
            # Cache supplier
            cache_entity('supplier', supplier.id, supplier.to_dict(), ttl=86400)
            invalidate_list_cache('supplier')
            
            # Publish event
            if event_publisher:
                event_publisher.publish('supplier_events', 'created', supplier.id, supplier.to_dict())
            
            logger.info(f"Supplier created: {supplier.name} (ID: {supplier.id})")
            
            return jsonify(supplier.to_dict()), 201
            
        except Exception as e:
            logger.error(f"Error creating supplier: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to create supplier'}), 500

    @app.route('/suppliers/<int:supplier_id>', methods=['PUT'])
    def update_supplier(supplier_id):
        """Update supplier"""
        try:
            supplier = Supplier.query.get(supplier_id)
            
            if not supplier:
                return jsonify({'error': 'Supplier not found'}), 404
            
            data = request.get_json()
            
            # Update fields
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
            
            # Publish event for cache invalidation
            if event_publisher:
                event_publisher.publish('supplier_events', 'updated', supplier.id, supplier.to_dict())
            
            logger.info(f"Supplier updated: {supplier.name} (ID: {supplier.id})")
            
            return jsonify(supplier.to_dict()), 200
            
        except Exception as e:
            logger.error(f"Error updating supplier {supplier_id}: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to update supplier'}), 500

    @app.route('/suppliers/<int:supplier_id>', methods=['DELETE'])
    def delete_supplier(supplier_id):
        """Delete supplier"""
        try:
            supplier = Supplier.query.get(supplier_id)
            
            if not supplier:
                return jsonify({'error': 'Supplier not found'}), 404
            
            supplier_name = supplier.name
            
            db.session.delete(supplier)
            db.session.commit()
            
            # Publish event for cache invalidation
            if event_publisher:
                event_publisher.publish('supplier_events', 'deleted', supplier_id, {})
            
            logger.info(f"Supplier deleted: {supplier_name} (ID: {supplier_id})")
            
            return jsonify({'message': 'Supplier deleted successfully'}), 200
            
        except Exception as e:
            logger.error(f"Error deleting supplier {supplier_id}: {e}")
            db.session.rollback()
            return jsonify({'error': 'Failed to delete supplier'}), 500

    @app.route('/suppliers/city/<city>', methods=['GET'])
    def get_suppliers_by_city(city):
        """Get suppliers by city"""
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


def warm_cache(app):
    """Warm cache with all suppliers on startup"""
    global cache_warmed
    
    try:
        with app.app_context():
            logger.info("Starting cache warming for suppliers...")
            suppliers = Supplier.query.all()
            supplier_dicts = [s.to_dict() for s in suppliers]
            
            warm_cache_sync('supplier', supplier_dicts, ttl=86400)
            
            cache_warmed = True
            logger.info(f"Cache warming complete: {len(supplier_dicts)} suppliers loaded")
        
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")


def shutdown_handler(signum, frame):
    """Handle graceful shutdown"""
    logger.info("Received shutdown signal, cleaning up...")
    
    if supervisor:
        supervisor.stop_all()
    
    logger.info("Shutdown complete")
    sys.exit(0)


def main():
    """Main entry point"""
    global event_publisher, supervisor
    
    logger.info("Starting Supplier Service...")
    
    # Create Flask app
    app = create_app()
    
    # Warm cache
    warm_cache(app)
    
    # Initialize event publisher
    event_publisher = EventPublisher()
    
    # Initialize supervisor with consumer process
    supervisor = MultiProcessSupervisor()
    supervisor.add_process(
        lambda: SupplierEventConsumer(),
        max_retries=3,
        retry_delay=5,
        check_interval=5
    )
    supervisor.start_all()
    
    # Register signal handlers
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    logger.info(f"Supplier Service ready on port {Config.SERVICE_PORT}")
    
    # Start Flask server
    app.run(
        host='0.0.0.0',
        port=Config.SERVICE_PORT,
        debug=False
    )


if __name__ == '__main__':
    main()
