from functools import wraps
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.logger import get_logger
from app.models.user import User

logger = get_logger('auth')


def admin_required(fn):
    """Decorator to restrict access to admin users."""
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or user.role != 'admin':
            logger.warning(f"Unauthorized admin access attempt by User {user_id} on {fn.__name__}")
            return jsonify({'error': 'Admin access required'}), 403

        return fn(*args, **kwargs)
    return wrapper


def log_request(func):
    """Decorator to log incoming API requests."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        api_logger = get_logger('api')
        endpoint = request.path
        method = request.method
        user_ip = request.remote_addr
        data = request.get_json(silent=True)
        email = data.get('email') if data else None

        api_logger.info(
            f"API called | Endpoint: {endpoint} | Method: {method} "
            f"| Email: {email} | IP: {user_ip}"
        )

        return func(*args, **kwargs)
    return wrapper
