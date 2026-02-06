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
from message_queue.cache import (
    warm_cache_sync,
    cache_entity,
    delete_cache,
    invalidate_list_cache,
)
from message_queue.supervisor import MultiProcessSupervisor

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global variables
event_publisher = None
supervisor = None
cache_warmed = False


class SupplierEventConsumer(EventConsumerProcess):
    """Consumer for supplier events (self-published for cache invalidation)"""

    def __init__(self):
        super().__init__(channels=["supplier_events"], name="supplier_consumer")

    def handle_updated(self, channel, entity_id, data):
        delete_cache("supplier", entity_id)
        invalidate_list_cache("supplier")
        logger.info(f"Invalidated cache for supplier {entity_id}")

    def handle_deleted(self, channel, entity_id, data):
        delete_cache("supplier", entity_id)
        invalidate_list_cache("supplier")
        logger.info(f"Invalidated cache for supplier {entity_id}")


def create_app():
    """Create and configure Flask application"""
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)

    # Initialize database
    db.init_app(flask_app)

    # Attach runtime attrs
    flask_app.cache_warmed = False

    # Register blueprint with supplier routes
    from routes import bp as supplier_bp

    flask_app.register_blueprint(supplier_bp)

    return flask_app


# Routes moved to `supplier/routes.py` using a Flask Blueprint
# See `supplier/routes.py` for all route handlers


def warm_cache(app):
    """Warm cache with all suppliers on startup"""
    try:
        with app.app_context():
            logger.info("Starting cache warming for suppliers...")
            suppliers = Supplier.query.all()
            supplier_dicts = [s.to_dict() for s in suppliers]

            warm_cache_sync("supplier", supplier_dicts, ttl=86400)

            app.cache_warmed = True
            logger.info(
                f"Cache warming complete: {len(supplier_dicts)} suppliers loaded"
            )
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
    # expose to routes via current_app
    app.event_publisher = event_publisher

    # Initialize supervisor with consumer process
    supervisor = MultiProcessSupervisor()
    # expose supervisor to routes and health checks
    app.supervisor = supervisor
    supervisor.add_process(
        lambda: SupplierEventConsumer(), max_retries=3, retry_delay=5, check_interval=5
    )
    supervisor.start_all()

    # Register signal handlers
    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    logger.info(f"Supplier Service ready on port {Config.SERVICE_PORT}")

    # Start Flask server
    app.run(host="0.0.0.0", port=Config.SERVICE_PORT, debug=False)


if __name__ == "__main__":
    main()
