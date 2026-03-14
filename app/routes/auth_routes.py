# app/routes/auth_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.auth_service import AuthService
from app.utils.response import (
    success_response, error_response, created_response, 
    not_found_response, validation_error_response, server_error_response,
    unauthorized_response
)
from app.utils.cache_utils import cache, user_cache_key
from app.utils.logger import get_logger, log_auth_event, log_cache_operation
import json
from app.utils.logger import log_request


auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/auth')
logger = get_logger('auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get("name")
    email = data.get("email")
    password = data.get("password")
    role = data.get("role", "EMPLOYEE")  # Default role is "user"

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
@log_request
def login():

    data = request.get_json()
    user_ip = request.remote_addr
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
    logger.info(f"Authentication result for {email}: {result}")
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

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name and not email and not password:
        logger.warning(f"Profile update failed: No fields to update | User: {user_id}")
        return validation_error_response('No fields to update')

    result = AuthService.update_profile(user_id, data)

    if result:
        logger.info(f"Profile updated successfully | User: {user_id}")
        return success_response("Profile updated successfully", result)
    
    logger.error(f"Profile update failed | User: {user_id}")
    return error_response('Failed to update profile')


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
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

@auth_bp.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    users = AuthService.get_all_users_ids_and_names()
    # logger.info(f"Fetched users list | Count: {len(users)}")
    return success_response("Users retrieved successfully", users)
