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

    flask_app.cache_warmed = False

    from routes import bp as customer_bp
    flask_app.register_blueprint(customer_bp)

    return flask_app


def main():
    logger.info("Starting Customer Service...")
    app = create_app()
    
    # Warm cache
    try:
        with app.app_context():
            logger.info("Starting cache warming for customers...")
            customers = Customer.query.all()
            customer_dicts = [c.to_dict() for c in customers]
            warm_cache_sync('customer', customer_dicts, ttl=86400)
            app.cache_warmed = True
            logger.info(f"Cache warming complete: {len(customer_dicts)} customers loaded")
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")
    
    app.event_publisher = EventPublisher()
    
    # Initialize and start supervisor
    app.supervisor = MultiProcessSupervisor()
    app.supervisor.add_process(
        lambda: CustomerEventConsumer(),
        max_retries=3,
        retry_delay=5,
        check_interval=5
    )
    app.supervisor.start_all()
    
    # Handle shutdown signals
    def shutdown_handler(signum, frame):
        logger.info("Received shutdown signal, cleaning up...")
        if hasattr(app, 'supervisor') and app.supervisor:
            app.supervisor.stop_all()
        logger.info("Shutdown complete")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)
    
    logger.info(f"Customer Service ready on port {Config.SERVICE_PORT}")
    
    app.run(host='0.0.0.0', port=Config.SERVICE_PORT, debug=False)


if __name__ == '__main__':
    main()
