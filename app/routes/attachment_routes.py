# app/routes/attachment_routes.py
import os
from flask import Blueprint, request, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.attachment_service import AttachmentService
from app.utils.response import (
    success_response, error_response, created_response, not_found_response,
    validation_error_response, server_error_response, forbidden_response
)
from app.utils.logger import get_logger

attachment_bp = Blueprint('attachment', __name__, url_prefix='/api/tasks')
logger = get_logger('api.attachments')


@attachment_bp.route('/<int:task_id>/attachments', methods=['GET'])
@jwt_required()
def get_attachments(task_id):
    """Get all attachments for a task."""
    try:
        result, status_code = AttachmentService.get_attachments(task_id)
        if status_code == 404:
            return not_found_response(result.get('error', 'Task not found'))
        if status_code != 200:
            return error_response(result.get('error', 'Error fetching attachments'), status_code=status_code)
        return success_response('Attachments retrieved successfully', result)
    except Exception as e:
        logger.error(f'Get attachments error: {str(e)}')
        return server_error_response(f'Error fetching attachments: {str(e)}')


@attachment_bp.route('/<int:task_id>/attachments', methods=['POST'])
@jwt_required()
def upload_attachment(task_id):
    """Upload a file attachment to a task."""
    user_id = get_jwt_identity()
    try:
        if 'file' not in request.files:
            return validation_error_response('No file provided in request')
        file = request.files['file']
        result, status_code = AttachmentService.upload_attachment(task_id, user_id, file)
        if status_code == 400:
            return error_response(result.get('error', 'Upload error'), status_code=400)
        if status_code == 404:
            return not_found_response(result.get('error', 'Task not found'))
        if status_code != 201:
            return error_response(result.get('error', 'Error uploading file'), status_code=status_code)
        return created_response('File uploaded successfully', result)
    except Exception as e:
        logger.error(f'Upload attachment error: {str(e)}')
        return server_error_response(f'Error uploading file: {str(e)}')


@attachment_bp.route('/attachments/<int:attachment_id>', methods=['GET'])
@jwt_required()
def get_attachment(attachment_id):
    """Get attachment metadata."""
    try:
        result, status_code = AttachmentService.get_attachment(attachment_id)
        if status_code == 404:
            return not_found_response(result.get('error', 'Attachment not found'))
        if status_code != 200:
            return error_response(result.get('error', 'Error fetching attachment'), status_code=status_code)
        return success_response('Attachment retrieved successfully', result)
    except Exception as e:
        logger.error(f'Get attachment error: {str(e)}')
        return server_error_response(f'Error fetching attachment: {str(e)}')


@attachment_bp.route('/attachments/<int:attachment_id>/download', methods=['GET'])
@jwt_required()
def download_attachment(attachment_id):
    """Download an attachment file."""
    try:
        from app.models.task_attachment import TaskAttachment
        attachment = TaskAttachment.query.get(attachment_id)
        if not attachment:
            return not_found_response('Attachment not found')
        if not os.path.exists(attachment.file_path):
            return not_found_response('File not found on server')
        return send_file(
            attachment.file_path,
            download_name=attachment.original_filename,
            as_attachment=True,
            mimetype=attachment.mime_type or 'application/octet-stream',
        )
    except Exception as e:
        logger.error(f'Download attachment error: {str(e)}')
        return server_error_response(f'Error downloading file: {str(e)}')


@attachment_bp.route('/attachments/<int:attachment_id>', methods=['DELETE'])
@jwt_required()
def delete_attachment(attachment_id):
    """Delete an attachment."""
    user_id = get_jwt_identity()
    try:
        result, status_code = AttachmentService.delete_attachment(attachment_id, user_id)
        if status_code == 403:
            return forbidden_response(result.get('error', 'Permission denied'))
        if status_code == 404:
            return not_found_response(result.get('error', 'Attachment not found'))
        if status_code != 200:
            return error_response(result.get('error', 'Error deleting attachment'), status_code=status_code)
        return success_response(result.get('message', 'Attachment deleted'))
    except Exception as e:
        logger.error(f'Delete attachment error: {str(e)}')
        return server_error_response(f'Error deleting attachment: {str(e)}')
