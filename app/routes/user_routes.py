# app/routes/user_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.user import User
from app.models.enums import UserRole
from app.services.user_service import UserService
from app.utils.response import (
    success_response, error_response, not_found_response,
    validation_error_response, server_error_response, forbidden_response,
)
from app.utils.logger import get_logger

logger = get_logger('api.users')

user_bp = Blueprint('users', __name__, url_prefix='/api/users')


def _get_current_user():
    """Return (user_id, user_role) for the authenticated caller."""
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user_id, user.role if user else None


# ── List users ───────────────────────────────────────────────────────────────

@user_bp.route('', methods=['GET'])
@jwt_required()
def list_users():
    """List all users with pagination, search, and role filtering."""
    user_id, role = _get_current_user()
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search')
        role_filter = request.args.get('role')
        is_active = request.args.get('is_active')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')

        if is_active is not None:
            is_active = is_active.lower() == 'true'

        result, status_code = UserService.get_users(
            page=page, per_page=per_page, search=search,
            role=role_filter, is_active=is_active,
            sort_by=sort_by, sort_order=sort_order,
        )

        if status_code != 200:
            return error_response(result.get('error', 'Error fetching users'),
                                  status_code=status_code)

        return success_response("Users retrieved successfully", result)

    except Exception as e:
        logger.error(f"List users error: {e}")
        return server_error_response(f'Error fetching users: {str(e)}')


# ── Search users (autocomplete) ───────────────────────────────────────────────

@user_bp.route('/search', methods=['GET'])
@jwt_required()
def search_users():
    """Quick user search by name or email for autocomplete."""
    q = request.args.get('q', '').strip()
    if not q:
        return validation_error_response('Query parameter "q" is required')

    limit = request.args.get('limit', 10, type=int)
    result, status_code = UserService.search_users(q, limit=limit)

    if status_code != 200:
        return error_response(result.get('error', 'Search failed'), status_code=status_code)

    return success_response("Search results", result)


# ── Get single user ───────────────────────────────────────────────────────────

@user_bp.route('/<int:target_user_id>', methods=['GET'])
@jwt_required()
def get_user(target_user_id):
    """Get a user profile with optional activity stats."""
    include_stats = request.args.get('include_stats', 'false').lower() == 'true'
    result, status_code = UserService.get_user_by_id(target_user_id,
                                                     include_stats=include_stats)

    if status_code == 404:
        return not_found_response(result.get('error', 'User not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Error fetching user'),
                              status_code=status_code)

    return success_response("User retrieved successfully", result)


# ── Update user ───────────────────────────────────────────────────────────────

@user_bp.route('/<int:target_user_id>', methods=['PUT'])
@jwt_required()
def update_user(target_user_id):
    """Update user information and preferences."""
    user_id, role = _get_current_user()
    data = request.get_json() or {}

    result, status_code = UserService.update_user(
        user_id=target_user_id,
        data=data,
        requesting_user_id=user_id,
        requesting_user_role=role,
    )

    if status_code == 403:
        return forbidden_response(result.get('error', 'Forbidden'))
    if status_code == 404:
        return not_found_response(result.get('error', 'User not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Error updating user'),
                              status_code=status_code)

    return success_response("User updated successfully", result)


# ── Delete user (admin only) ──────────────────────────────────────────────────

@user_bp.route('/<int:target_user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(target_user_id):
    """Deactivate a user account (admin only)."""
    user_id, role = _get_current_user()

    result, status_code = UserService.delete_user(
        user_id=target_user_id,
        requesting_user_id=user_id,
        requesting_user_role=role,
    )

    if status_code == 403:
        return forbidden_response(result.get('error', 'Admin access required'))
    if status_code == 404:
        return not_found_response(result.get('error', 'User not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Error deleting user'),
                              status_code=status_code)

    return success_response(result.get('message', 'User deleted successfully'))


# ── Bulk operations ───────────────────────────────────────────────────────────

@user_bp.route('/bulk', methods=['PATCH'])
@jwt_required()
def bulk_update_users():
    """Bulk update users (admin only)."""
    user_id, role = _get_current_user()
    data = request.get_json() or {}

    user_ids = data.get('user_ids')
    updates = data.get('updates')

    if not user_ids or not isinstance(user_ids, list):
        return validation_error_response('user_ids must be a non-empty list')
    if not updates or not isinstance(updates, dict):
        return validation_error_response('updates must be a non-empty object')

    result, status_code = UserService.bulk_update_users(user_ids, updates, role)

    if status_code == 403:
        return forbidden_response(result.get('error', 'Admin access required'))
    if status_code != 200:
        return error_response(result.get('error', 'Bulk update failed'),
                              status_code=status_code)

    return success_response("Bulk update successful", result)
