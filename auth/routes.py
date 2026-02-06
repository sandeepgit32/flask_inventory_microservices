import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, current_app
from db import db
import jwt
import bcrypt

from models import User
from config import Config
from message_queue.cache import cache_entity, warm_cache_sync

logger = logging.getLogger(__name__)

bp = Blueprint('auth', __name__)


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def generate_token(user_id: int, username: str, role: str) -> str:
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRY_HOURS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, Config.JWT_SECRET_KEY, algorithm=Config.JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, Config.JWT_SECRET_KEY, algorithms=[Config.JWT_ALGORITHM])
        return {'valid': True, 'payload': payload}
    except jwt.ExpiredSignatureError:
        return {'valid': False, 'error': 'Token has expired'}
    except jwt.InvalidTokenError as e:
        return {'valid': False, 'error': str(e)}


@bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'service': Config.SERVICE_NAME,
        'cache_warmed': getattr(current_app, 'cache_warmed', False),
        'timestamp': datetime.utcnow().isoformat()
    }), 200


@bp.route('/auth/register', methods=['POST'])
def register():
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
        event_publisher = getattr(current_app, 'event_publisher', None)
        if event_publisher:
            event_publisher.publish('user_events', 'created', user.id, user.to_dict())
        logger.info(f"User registered: {username} (ID: {user.id})")
        return jsonify({'message': 'User registered successfully', 'user': user.to_dict()}), 201
    except Exception as e:
        logger.error(f"Registration error: {e}")
        db.session.rollback()
        return jsonify({'error': 'Registration failed'}), 500


@bp.route('/auth/login', methods=['POST'])
def login():
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
        return jsonify({'message': 'Login successful', 'token': token, 'user': user.to_dict()}), 200
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500


@bp.route('/auth/validate', methods=['POST'])
def validate_token():
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