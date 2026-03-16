# app/routes/member_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.project import Project
from app.models.user import User
from app.services.member_service import ProjectMemberService
from app.utils.response import (
    success_response, error_response, created_response, not_found_response,
    validation_error_response, server_error_response, forbidden_response,
)
from app.utils.logger import get_logger

logger = get_logger('api.members')

member_bp = Blueprint('members', __name__, url_prefix='/api/projects')


def _can_manage(project_id, user_id):
    """Return True if user is the project owner or has manage_members permission."""
    project = Project.query.get(project_id)
    if not project:
        return False, None
    if project.owner_id == int(user_id):
        return True, project
    from app.models.project_member import ProjectMember
    m = ProjectMember.query.filter_by(
        project_id=project_id, user_id=int(user_id)
    ).first()
    return (m is not None and m.can_manage_members), project


# ── Get members ───────────────────────────────────────────────────────────────

@member_bp.route('/<int:project_id>/members', methods=['GET'])
@jwt_required()
def get_members(project_id):
    """Get project members with roles and permissions."""
    result, status_code = ProjectMemberService.get_members(project_id)

    if status_code == 404:
        return not_found_response(result.get('error', 'Project not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Error fetching members'),
                              status_code=status_code)

    return success_response("Project members retrieved successfully", result)


# ── Add member ────────────────────────────────────────────────────────────────

@member_bp.route('/<int:project_id>/members', methods=['POST'])
@jwt_required()
def add_member(project_id):
    """Add a member to the project."""
    requesting_user_id = get_jwt_identity()
    can, project = _can_manage(project_id, requesting_user_id)
    if project is None:
        return not_found_response('Project not found')
    if not can:
        return forbidden_response('You do not have permission to manage members')

    data = request.get_json() or {}
    user_id = data.get('user_id')
    if not user_id:
        return validation_error_response('user_id is required')

    result, status_code = ProjectMemberService.add_member(
        project_id=project_id,
        user_id=user_id,
        role=data.get('role'),
        permissions=data.get('permissions'),
        requesting_user_id=requesting_user_id,
    )

    if status_code == 409:
        return error_response(result.get('error', 'Conflict'), status_code=409)
    if status_code == 404:
        return not_found_response(result.get('error', 'Not found'))
    if status_code != 201:
        return error_response(result.get('error', 'Error adding member'),
                              status_code=status_code)

    return created_response("Member added successfully", result)


# ── Update member ─────────────────────────────────────────────────────────────

@member_bp.route('/<int:project_id>/members/<int:target_user_id>', methods=['PUT'])
@jwt_required()
def update_member(project_id, target_user_id):
    """Update a project member's role or permissions."""
    requesting_user_id = get_jwt_identity()
    can, project = _can_manage(project_id, requesting_user_id)
    if project is None:
        return not_found_response('Project not found')
    if not can:
        return forbidden_response('You do not have permission to manage members')

    data = request.get_json() or {}
    result, status_code = ProjectMemberService.update_member(
        project_id=project_id,
        user_id=target_user_id,
        data=data,
        requesting_user_id=requesting_user_id,
    )

    if status_code == 404:
        return not_found_response(result.get('error', 'Member not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Error updating member'),
                              status_code=status_code)

    return success_response("Member updated successfully", result)


# ── Remove member ─────────────────────────────────────────────────────────────

@member_bp.route('/<int:project_id>/members/<int:target_user_id>', methods=['DELETE'])
@jwt_required()
def remove_member(project_id, target_user_id):
    """Remove a member from the project."""
    requesting_user_id = get_jwt_identity()
    can, project = _can_manage(project_id, requesting_user_id)
    if project is None:
        return not_found_response('Project not found')
    if not can:
        return forbidden_response('You do not have permission to manage members')

    result, status_code = ProjectMemberService.remove_member(
        project_id=project_id,
        user_id=target_user_id,
        requesting_user_id=requesting_user_id,
    )

    if status_code == 404:
        return not_found_response(result.get('error', 'Member not found'))
    if status_code == 400:
        return error_response(result.get('error', 'Bad request'), status_code=400)
    if status_code != 200:
        return error_response(result.get('error', 'Error removing member'),
                              status_code=status_code)

    return success_response(result.get('message', 'Member removed successfully'))


# ── Bulk add members ──────────────────────────────────────────────────────────

@member_bp.route('/<int:project_id>/members/bulk', methods=['POST'])
@jwt_required()
def bulk_add_members(project_id):
    """Add multiple members to the project at once."""
    requesting_user_id = get_jwt_identity()
    can, project = _can_manage(project_id, requesting_user_id)
    if project is None:
        return not_found_response('Project not found')
    if not can:
        return forbidden_response('You do not have permission to manage members')

    data = request.get_json() or {}
    members_data = data.get('members')

    if not members_data or not isinstance(members_data, list):
        return validation_error_response('members must be a non-empty list')

    result, status_code = ProjectMemberService.bulk_add_members(
        project_id=project_id,
        members_data=members_data,
        requesting_user_id=requesting_user_id,
    )

    if status_code not in (200, 201):
        return error_response(result.get('error', 'Bulk add failed'),
                              status_code=status_code)

    return created_response("Bulk add completed", result)
