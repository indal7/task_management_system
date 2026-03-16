# app/routes/member_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.member_service import MemberService
from app.utils.response import (
    success_response, error_response, created_response, not_found_response,
    validation_error_response, server_error_response, forbidden_response
)
from app.utils.logger import get_logger

member_bp = Blueprint('member', __name__, url_prefix='/api/projects')
logger = get_logger('api.members')


@member_bp.route('/<int:project_id>/members', methods=['GET'])
@jwt_required()
def get_members(project_id):
    """Get all members of a project."""
    try:
        result, status_code = MemberService.get_members(project_id)
        if status_code == 404:
            return not_found_response(result.get('error', 'Project not found'))
        if status_code != 200:
            return error_response(result.get('error', 'Error fetching members'), status_code=status_code)
        return success_response('Members retrieved successfully', result)
    except Exception as e:
        logger.error(f'Get members error: {str(e)}')
        return server_error_response(f'Error fetching members: {str(e)}')


@member_bp.route('/<int:project_id>/members', methods=['POST'])
@jwt_required()
def add_member(project_id):
    """Add a member to a project."""
    requesting_user_id = get_jwt_identity()
    data = request.get_json()
    if not data or not data.get('user_id'):
        return validation_error_response('user_id is required')
    try:
        user_id = int(data['user_id'])
        role = data.get('role')
        permissions = data.get('permissions')
        result, status_code = MemberService.add_member(
            project_id, user_id, role=role, permissions=permissions,
            requesting_user_id=requesting_user_id
        )
        if status_code == 403:
            return forbidden_response(result.get('error', 'Permission denied'))
        if status_code == 404:
            return not_found_response(result.get('error', 'Resource not found'))
        if status_code == 409:
            return error_response(result.get('error', 'Already a member'), status_code=409)
        if status_code != 201:
            return error_response(result.get('error', 'Error adding member'), status_code=status_code)
        return created_response('Member added successfully', result)
    except Exception as e:
        logger.error(f'Add member error: {str(e)}')
        return server_error_response(f'Error adding member: {str(e)}')


@member_bp.route('/<int:project_id>/members/<int:target_user_id>', methods=['PUT'])
@jwt_required()
def update_member(project_id, target_user_id):
    """Update a member's role or permissions."""
    requesting_user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return validation_error_response('No data provided')
    try:
        result, status_code = MemberService.update_member(
            project_id, target_user_id, data, requesting_user_id
        )
        if status_code == 403:
            return forbidden_response(result.get('error', 'Permission denied'))
        if status_code == 404:
            return not_found_response(result.get('error', 'Resource not found'))
        if status_code != 200:
            return error_response(result.get('error', 'Error updating member'), status_code=status_code)
        return success_response('Member updated successfully', result)
    except Exception as e:
        logger.error(f'Update member error: {str(e)}')
        return server_error_response(f'Error updating member: {str(e)}')


@member_bp.route('/<int:project_id>/members/<int:target_user_id>', methods=['DELETE'])
@jwt_required()
def remove_member(project_id, target_user_id):
    """Remove a member from a project."""
    requesting_user_id = get_jwt_identity()
    try:
        result, status_code = MemberService.remove_member(
            project_id, target_user_id, requesting_user_id
        )
        if status_code == 403:
            return forbidden_response(result.get('error', 'Permission denied'))
        if status_code == 404:
            return not_found_response(result.get('error', 'Resource not found'))
        if status_code == 400:
            return error_response(result.get('error', 'Bad request'), status_code=400)
        if status_code != 200:
            return error_response(result.get('error', 'Error removing member'), status_code=status_code)
        return success_response(result.get('message', 'Member removed'))
    except Exception as e:
        logger.error(f'Remove member error: {str(e)}')
        return server_error_response(f'Error removing member: {str(e)}')
