# app/routes/user_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.user_service import UserService
from app.utils.response import (
    success_response, error_response, not_found_response,
    validation_error_response, server_error_response, forbidden_response
)
from app.utils.logger import get_logger

user_bp = Blueprint('user', __name__, url_prefix='/api/users')
logger = get_logger('api.users')


@user_bp.route('', methods=['GET'])
@jwt_required()
def list_users():
    """List users with optional filtering and pagination."""
    user_id = get_jwt_identity()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '').strip() or None
        role = request.args.get('role') or None
        is_active_param = request.args.get('is_active')
        is_active = None
        if is_active_param is not None:
            is_active = is_active_param.lower() in ('true', '1', 'yes')

        result, status_code = UserService.list_users(
            page=page, per_page=per_page, search=search, role=role, is_active=is_active
        )
        if status_code != 200:
            return error_response(result.get('error', 'Error listing users'), status_code=status_code)
        return success_response('Users retrieved successfully', result)
    except Exception as e:
        logger.error(f'List users error: {str(e)}')
        return server_error_response(f'Error listing users: {str(e)}')


@user_bp.route('/search', methods=['GET'])
@jwt_required()
def search_users():
    """Search users by name or email."""
    try:
        q = request.args.get('q', '').strip()
        if not q:
            return validation_error_response('Search query is required')
        limit = min(request.args.get('limit', 10, type=int), 50)
        result, status_code = UserService.search_users(q, limit=limit)
        if status_code != 200:
            return error_response(result.get('error', 'Error searching users'), status_code=status_code)
        return success_response('Users found', result)
    except Exception as e:
        logger.error(f'Search users error: {str(e)}')
        return server_error_response(f'Error searching users: {str(e)}')


@user_bp.route('/<int:target_user_id>', methods=['GET'])
@jwt_required()
def get_user(target_user_id):
    """Get a specific user's profile with statistics."""
    try:
        result, status_code = UserService.get_user(target_user_id)
        if status_code == 404:
            return not_found_response(result.get('error', 'User not found'))
        if status_code != 200:
            return error_response(result.get('error', 'Error fetching user'), status_code=status_code)
        return success_response('User retrieved successfully', result)
    except Exception as e:
        logger.error(f'Get user error: {str(e)}')
        return server_error_response(f'Error fetching user: {str(e)}')


@user_bp.route('/<int:target_user_id>', methods=['PUT'])
@jwt_required()
def update_user(target_user_id):
    """Update user information."""
    requesting_user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return validation_error_response('No data provided')
    try:
        result, status_code = UserService.update_user(target_user_id, data, requesting_user_id)
        if status_code == 403:
            return forbidden_response(result.get('error', 'Permission denied'))
        if status_code == 404:
            return not_found_response(result.get('error', 'User not found'))
        if status_code != 200:
            return error_response(result.get('error', 'Error updating user'), status_code=status_code)
        return success_response('User updated successfully', result)
    except Exception as e:
        logger.error(f'Update user error: {str(e)}')
        return server_error_response(f'Error updating user: {str(e)}')


@user_bp.route('/<int:target_user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(target_user_id):
    """Deactivate a user (admin only)."""
    requesting_user_id = get_jwt_identity()
    try:
        result, status_code = UserService.delete_user(target_user_id, requesting_user_id)
        if status_code == 403:
            return forbidden_response(result.get('error', 'Permission denied'))
        if status_code == 404:
            return not_found_response(result.get('error', 'User not found'))
        if status_code != 200:
            return error_response(result.get('error', 'Error deleting user'), status_code=status_code)
        return success_response(result.get('message', 'User deactivated'))
    except Exception as e:
        logger.error(f'Delete user error: {str(e)}')
        return server_error_response(f'Error deleting user: {str(e)}')


@user_bp.route('/<int:target_user_id>/activate', methods=['POST'])
@jwt_required()
def activate_user(target_user_id):
    """Activate a user account (admin only)."""
    requesting_user_id = get_jwt_identity()
    try:
        result, status_code = UserService.activate_user(target_user_id, requesting_user_id)
        if status_code == 403:
            return forbidden_response(result.get('error', 'Permission denied'))
        if status_code == 404:
            return not_found_response(result.get('error', 'User not found'))
        if status_code != 200:
            return error_response(result.get('error', 'Error activating user'), status_code=status_code)
        return success_response(result.get('message', 'User activated'))
    except Exception as e:
        logger.error(f'Activate user error: {str(e)}')
        return server_error_response(f'Error activating user: {str(e)}')
