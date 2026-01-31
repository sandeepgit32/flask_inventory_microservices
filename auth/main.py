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
    register_routes(flask_app)
    return flask_app


def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def generate_token(user_id: int, username: str, role: str) -> str:
    """Generate JWT token with 6-hour expiry"""
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRY_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Decode and validate JWT token"""
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
        return {'valid': True, 'payload': payload}
    except jwt.ExpiredSignatureError:
        return {'valid': False, 'error': 'Token has expired'}
    except jwt.InvalidTokenError as e:
        return {'valid': False, 'error': str(e)}


def register_routes(app):
    """Register all routes on the Flask app"""
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'service': Config.SERVICE_NAME,
            'cache_warmed': cache_warmed,
            'timestamp': datetime.utcnow().isoformat()
        }), 200

    @app.route('/auth/register', methods=['POST'])
    def register():
        """Register new user"""
        try:
            data = request.get_json()
            
            username = data.get('username')
            password = data.get('password')
            email = data.get('email')
            role = data.get('role', 'user')
            
            if not username or not password or not email:
                return jsonify({'error': 'Username, password, and email are required'}), 400
            
            if User.query.filter_by(username=username).first():
                return jsonify({'error': 'Username already exists'}), 409
            
            if User.query.filter_by(email=email).first():
                return jsonify({'error': 'Email already exists'}), 409
            
            password_hash = hash_password(password)
            user = User(
                username=username,
                password_hash=password_hash,
                email=email,
                role=role
            )
            
            db.session.add(user)
            db.session.commit()
            
            cache_entity('user', user.id, user.to_dict(), ttl=86400)
            
            if event_publisher:
                event_publisher.publish('user_events', 'created', user.id, user.to_dict())
            
            logger.info(f"User registered: {username} (ID: {user.id})")
            
            return jsonify({
                'message': 'User registered successfully',
                'user': user.to_dict()
            }), 201
            
        except Exception as e:
            logger.error(f"Registration error: {e}")
            db.session.rollback()
            return jsonify({'error': 'Registration failed'}), 500

    @app.route('/auth/login', methods=['POST'])
    def login():
        """Authenticate user and return JWT token"""
        try:
            data = request.get_json()
            
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({'error': 'Username and password are required'}), 400
            
            user = User.query.filter_by(username=username).first()
            
            if not user or not verify_password(password, user.password_hash):
                return jsonify({'error': 'Invalid username or password'}), 401
            
            token = generate_token(user.id, user.username, user.role)
            
            logger.info(f"User logged in: {username}")
            
            return jsonify({
                'message': 'Login successful',
                'token': token,
                'user': user.to_dict()
            }), 200
            
        except Exception as e:
            logger.error(f"Login error: {e}")
            return jsonify({'error': 'Login failed'}), 500

    @app.route('/auth/validate', methods=['POST'])
    def validate_token():
        """Validate JWT token"""
        try:
            data = request.get_json()
            token = data.get('token')
            
            if not token:
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
            
            if not token:
                return jsonify({'valid': False, 'error': 'Token is required'}), 400
            
            result = decode_token(token)
            
            if result['valid']:
                return jsonify(result), 200
            else:
                return jsonify(result), 401
                
        except Exception as e:
            logger.error(f"Token validation error: {e}")
            return jsonify({'valid': False, 'error': 'Validation failed'}), 500


def warm_cache(app):
    """Warm cache with all users on startup"""
    global cache_warmed
    
    try:
        with app.app_context():
            logger.info("Starting cache warming for users...")
            users = User.query.all()
            user_dicts = [u.to_dict() for u in users]
            warm_cache_sync('user', user_dicts, ttl=86400)
            cache_warmed = True
            logger.info(f"Cache warming complete: {len(user_dicts)} users loaded")
    except Exception as e:
        logger.error(f"Failed to warm cache: {e}")


def shutdown_handler(signum, frame):
    """Handle graceful shutdown"""
    logger.info("Received shutdown signal, cleaning up...")
    logger.info("Shutdown complete")
    sys.exit(0)


def main():
    """Main entry point"""
    global event_publisher
    
    logger.info("Starting Auth Service...")
    
    app = create_app()
    
    warm_cache(app)
    
    event_publisher = EventPublisher()
    
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
