import sys
import os
import logging
import signal
from flask import Flask, request, jsonify
import jwt
import bcrypt
from datetime import datetime, timedelta

# Add parent directory to path for shared modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from db import db
from models import User
from message_queue.event_system import EventPublisher
from message_queue.cache import warm_cache_sync, cache_entity

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables
event_publisher = None
cache_warmed = False


def create_app():
    """Create and configure Flask application"""
    flask_app = Flask(__name__)
    flask_app.config.from_object(Config)
    db.init_app(flask_app)

    # Attach runtime attrs used by routes
    flask_app.cache_warmed = False

    # Register blueprint with routes
    from routes import bp as auth_bp
    flask_app.register_blueprint(auth_bp)

    return flask_app


def main():
    """Main entry point"""
    logger.info("Starting Auth Service...")
    app = create_app()

    # Warm cache
    try:
        with app.app_context():
            logger.info("Starting cache warming for users...")
            users = User.query.all()
            user_dicts = [u.to_dict() for u in users]
            warm_cache_sync('user', user_dicts, ttl=86400)
            app.cache_warmed = True
            logger.info(f"Cache warming complete: {len(user_dicts)} users loaded")
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")

    app.event_publisher = EventPublisher()

    # Handle graceful shutdown
    def shutdown_handler(signum, frame):
        logger.info("Received shutdown signal, cleaning up...")
        logger.info("Shutdown complete")
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown_handler)
    signal.signal(signal.SIGINT, shutdown_handler)

    logger.info(f"Auth Service ready on port {Config.SERVICE_PORT}")

    app.run(
        host='0.0.0.0',
        port=Config.SERVICE_PORT,
        debug=False
    )


if __name__ == '__main__':
    main()
