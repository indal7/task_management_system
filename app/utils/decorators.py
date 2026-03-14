from functools import wraps
from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.logger import get_logger
from app.models.user import User

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
