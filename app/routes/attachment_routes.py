# app/routes/attachment_routes.py
import os

from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models.user import User
from app.services.attachment_service import AttachmentService
from app.utils.response import (
    success_response, error_response, created_response, not_found_response,
    validation_error_response, server_error_response, forbidden_response,
)
from app.utils.logger import get_logger

logger = get_logger('api.attachments')

attachment_bp = Blueprint('attachments', __name__, url_prefix='/api/tasks')


def _get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user_id, user.role if user else None


# ── List task attachments ─────────────────────────────────────────────────────

@attachment_bp.route('/<int:task_id>/attachments', methods=['GET'])
@jwt_required()
def get_attachments(task_id):
    """Get all attachments for a task."""
    user_id, _ = _get_current_user()
    result, status_code = AttachmentService.get_task_attachments(task_id, user_id)

    if status_code == 404:
        return not_found_response(result.get('error', 'Task not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Error fetching attachments'),
                              status_code=status_code)

    return success_response("Attachments retrieved successfully", result)


# ── Upload attachment ─────────────────────────────────────────────────────────

@attachment_bp.route('/<int:task_id>/attachments', methods=['POST'])
@jwt_required()
def upload_attachment(task_id):
    """Upload a file attachment to a task."""
    user_id, _ = _get_current_user()

    if 'file' not in request.files:
        return validation_error_response('No file part in request')

    file = request.files['file']
    result, status_code = AttachmentService.upload_attachment(task_id, user_id, file)

    if status_code == 404:
        return not_found_response(result.get('error', 'Task not found'))
    if status_code == 400:
        return error_response(result.get('error', 'Bad request'), status_code=400)
    if status_code != 201:
        return error_response(result.get('error', 'Error uploading attachment'),
                              status_code=status_code)

    return created_response("Attachment uploaded successfully", result)


# ── Get single attachment metadata ────────────────────────────────────────────

@attachment_bp.route('/attachments/<int:attachment_id>', methods=['GET'])
@jwt_required()
def get_attachment(attachment_id):
    """Get metadata for a specific attachment."""
    user_id, _ = _get_current_user()
    result, status_code = AttachmentService.get_attachment(attachment_id, user_id)

    if status_code == 404:
        return not_found_response(result.get('error', 'Attachment not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Error fetching attachment'),
                              status_code=status_code)

    return success_response("Attachment retrieved successfully", result)


# ── Download attachment ───────────────────────────────────────────────────────

@attachment_bp.route('/attachments/<int:attachment_id>/download', methods=['GET'])
@jwt_required()
def download_attachment(attachment_id):
    """Download an attachment file."""
    user_id, _ = _get_current_user()
    result, status_code = AttachmentService.get_attachment(attachment_id, user_id)

    if status_code == 404:
        return not_found_response(result.get('error', 'Attachment not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Error fetching attachment'),
                              status_code=status_code)

    file_path = result.get('file_path')
    if not file_path or not os.path.exists(file_path):
        return not_found_response('File not found on server')

    return send_file(
        file_path,
        mimetype=result.get('mime_type', 'application/octet-stream'),
        as_attachment=True,
        download_name=result.get('original_filename', 'download'),
    )


# ── Delete attachment ─────────────────────────────────────────────────────────

@attachment_bp.route('/attachments/<int:attachment_id>', methods=['DELETE'])
@jwt_required()
def delete_attachment(attachment_id):
    """Delete an attachment."""
    user_id, role = _get_current_user()
    result, status_code = AttachmentService.delete_attachment(
        attachment_id, user_id, role
    )

    if status_code == 403:
        return forbidden_response(result.get('error', 'Permission denied'))
    if status_code == 404:
        return not_found_response(result.get('error', 'Attachment not found'))
    if status_code != 200:
        return error_response(result.get('error', 'Error deleting attachment'),
                              status_code=status_code)

    return success_response(result.get('message', 'Attachment deleted'))
