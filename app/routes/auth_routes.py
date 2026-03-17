# app/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.auth_service import AuthService
from app.services.activity_service import ActivityService
from app.utils.response import (
    success_response, error_response, created_response,
    not_found_response, validation_error_response, server_error_response,
    unauthorized_response
)
from app.utils.cache_utils import cache, user_cache_key
from app.utils.logger import get_logger, log_auth_event, log_cache_operation
from app.utils.decorators import log_request
from app import limiter
import json
from datetime import datetime


auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')
logger = get_logger('auth')
PRESENCE_TTL_SECONDS = 180


def _presence_cache_key(user_id):
    return f"presence:user:{user_id}"


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("10 per hour")
def register():
    data = request.get_json()
    username = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "DEVELOPER")  # Default role

    logger.debug(f"Register attempt | Email: {email} | Name: {username}")

    if not username or not email or not password:
        logger.warning(f"Register failed: Missing required fields | Email: {email}")
        return validation_error_response('Missing required fields')

    result = AuthService.register_user(username, email, password, role)

    if 'error' in result:
        logger.error(f"Register failed for {email}: {result['error']}")
        return error_response(result['error'])

    logger.info(f"User registered successfully | Email: {email}")
    return created_response("User registered successfully", result)


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("20 per minute")
@log_request
def login():

    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Check cache first
    cache_key = f"login:{email}"
    cached_result = cache.get(cache_key)
    log_cache_operation("GET", cache_key, hit=bool(cached_result))

    if cached_result:
        logger.info(f"Login fetched from cache | Email: {email}")
        log_auth_event("Login", email=email, success=True)
        return success_response("Login successful (from cache)", json.loads(cached_result))

    # Authenticate user
    result = AuthService.login_user(email, password)
    if not result["success"]:
        logger.warning(f"Login failed for {email}: {result['error']}")
        log_auth_event("Login", email=email, success=False)
        return unauthorized_response(result["error"])

    # Cache login result for 5 minutes
    cache.set(cache_key, json.dumps(result), timeout=300)
    log_cache_operation("SET", cache_key)

    logger.info(f"Login successful and cached | Email: {email}")
    log_auth_event("Login", user_id=result.get("user_id"), email=email, success=True)
    return success_response("Login successful", result)


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    user = AuthService.validate_token()
    logger.info(f"Profile fetched | User: {get_jwt_identity()}")
    return success_response("User profile retrieved successfully", user)


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    data = request.get_json()
    user_id = get_jwt_identity()

    updatable_fields = {
        'name',
        'email',
        'password',
        'bio',
        'skills',
        'github_username',
        'linkedin_url',
        'phone',
        'timezone',
        'daily_work_hours',
        'hourly_rate'
    }

    if not data or not any(field in data for field in updatable_fields):
        logger.warning(f"Profile update failed: No fields to update | User: {user_id}")
        return validation_error_response('No fields to update')

    result = AuthService.update_profile(user_id, data)

    if result and 'error' not in result:
        logger.info(f"Profile updated successfully | User: {user_id}")
        return success_response("Profile updated successfully", result)

    if result and 'error' in result:
        logger.error(f"Profile update failed | User: {user_id} | Error: {result['error']}")
        return error_response(result['error'])

    logger.error(f"Profile update failed | User: {user_id}")
    return error_response('Failed to update profile')


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
@limiter.limit("5 per hour")
def update_password():
    data = request.get_json()
    user_id = get_jwt_identity()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        logger.warning(f"Change password failed: Missing fields | User: {user_id}")
        return validation_error_response('Missing required fields')

    result = AuthService.change_password(user_id, new_password)

    if 'error' in result:
        logger.error(f"Change password failed | User: {user_id}: {result['error']}")
        return error_response(result['error'])

    logger.info(f"Password changed successfully | User: {user_id}")
    return success_response("Password changed successfully", result)


@auth_bp.route('/ping', methods=['GET'])
def test():
    logger.info("Ping request received")
    return success_response("Auth API is working!")

@auth_bp.route('/refresh', methods=['POST'])
def refresh_token():
    """Generate a new access token using a valid refresh token."""
    from flask_jwt_extended import decode_token, create_access_token, create_refresh_token
    try:
        # Accept refresh token from body OR Authorization header
        data = request.get_json() or {}
        body_token = data.get('refresh_token')

        # Try Authorization header first, then fall back to body
        auth_header = request.headers.get('Authorization', '')
        header_token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None

        token = header_token or body_token

        if not token:
            logger.warning("Token refresh failed: no refresh token provided")
            return validation_error_response('No refresh token provided')

        # Decode and validate the refresh token
        decoded = decode_token(token)
        if decoded.get('type') != 'refresh':
            return unauthorized_response('Not a refresh token')

        user_id = decoded['sub']
        from app.models.user import User
        user = User.query.get_or_404(user_id)

        new_access_token = create_access_token(identity=str(user.id))
        new_refresh_token = create_refresh_token(identity=str(user.id))

        logger.info(f"Token refreshed successfully | User: {user.id}")
        return success_response("Token refreshed successfully", {
            'access_token': new_access_token,
            'refresh_token': new_refresh_token,
            'user': user.to_dict()
        })
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        return unauthorized_response('Invalid or expired refresh token')

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    users = AuthService.get_all_users_ids_and_names()
    return success_response("Users retrieved successfully", users)


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Record a logout event.

    Supports standard authenticated API calls and sendBeacon payloads
    where the token is sent in request body as { token: "..." }.
    """
    from flask_jwt_extended import decode_token
    from app.models.user import User

    data = request.get_json(silent=True) or {}
    reason = data.get('reason', 'manual_logout')
    source = data.get('source', 'api')

    auth_header = request.headers.get('Authorization', '')
    header_token = auth_header.replace('Bearer ', '') if auth_header.startswith('Bearer ') else None
    body_token = data.get('token')
    token = header_token or body_token

    if not token:
        logger.info("Logout called without token; returning success without activity log")
        return success_response("Logout processed")

    try:
        decoded = decode_token(token)
        user_id = decoded.get('sub')
        user = User.query.get(user_id) if user_id else None

        if user:
            ActivityService.log(
                entity_type='auth',
                entity_id=user.id,
                action='LOGOUT',
                user_id=user.id,
                details={'reason': reason, 'source': source}
            )
            logger.info(f"Logout recorded | User: {user.id} | Source: {source}")
        else:
            logger.warning("Logout token decoded but user not found")

        return success_response("Logout processed")

    except Exception as e:
        logger.warning(f"Logout token decode failed: {str(e)}")
        # Client still should be able to clear local session even if token is stale.
        return success_response("Logout processed")


@auth_bp.route('/presence/heartbeat', methods=['POST'])
@jwt_required()
def presence_heartbeat():
    """Update transient online presence for the current user."""
    user_id = get_jwt_identity()
    now_iso = datetime.utcnow().isoformat()

    cache.set(_presence_cache_key(user_id), now_iso, timeout=PRESENCE_TTL_SECONDS)
    return success_response("Presence heartbeat recorded", {
        'user_id': int(user_id),
        'last_seen_at': now_iso,
        'ttl_seconds': PRESENCE_TTL_SECONDS
    })


@auth_bp.route('/presence/status/<int:target_user_id>', methods=['GET'])
@jwt_required()
def presence_status(target_user_id):
    """Return online/offline presence status for a user based on heartbeat TTL."""
    last_seen_at = cache.get(_presence_cache_key(target_user_id))
    is_online = bool(last_seen_at)

    return success_response("Presence status retrieved", {
        'user_id': target_user_id,
        'is_online': is_online,
        'last_seen_at': last_seen_at
    })

