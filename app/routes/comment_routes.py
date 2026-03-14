# app/routes/comment_routes.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.comment_service import CommentService
from app.utils.response import (
    success_response, error_response, created_response, 
    not_found_response, validation_error_response, server_error_response,
    forbidden_response
)

comment_bp = Blueprint('comment', __name__, url_prefix='/api/tasks')

from app.utils.logger import get_logger, log_request, log_cache_operation

logger = get_logger('tasks')  # Or 'comments', if you prefer a separate logger

@comment_bp.route('/<int:task_id>/comments', methods=['GET'])
@jwt_required()
@log_request  # Logs API path, user, IP
def get_comments(task_id):
    logger.debug(f"Fetching comments | Task ID: {task_id} | User: {get_jwt_identity()}")
    result = CommentService.get_comments_by_task(task_id)
    return success_response("Comments retrieved successfully", result)


@comment_bp.route('/comments/<int:comment_id>', methods=['PUT'])
@jwt_required()
@log_request
def update_comment(comment_id):
    data = request.get_json()
    user_id = get_jwt_identity()
    logger.debug(f"Update comment attempt | Comment ID: {comment_id} | User: {user_id}")

    if not data.get('comment'):
        logger.warning(f"Update failed: No comment text | Comment ID: {comment_id} | User: {user_id}")
        return validation_error_response('Comment text is required')

    result = CommentService.update_comment(comment_id, user_id, data.get('comment'))

    if 'error' in result:
        logger.warning(f"Update forbidden | Comment ID: {comment_id} | User: {user_id}")
        return forbidden_response(result['error'])

    logger.info(f"Comment updated successfully | Comment ID: {comment_id} | User: {user_id}")
    return success_response("Comment updated successfully", result)


@comment_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
@jwt_required()
@log_request
def delete_comment(comment_id):
    user_id = get_jwt_identity()
    logger.debug(f"Delete comment attempt | Comment ID: {comment_id} | User: {user_id}")

    result = CommentService.delete_comment(comment_id, user_id)

    if 'error' in result:
        logger.warning(f"Delete forbidden | Comment ID: {comment_id} | User: {user_id}")
        return forbidden_response(result['error'])

    logger.info(f"Comment deleted successfully | Comment ID: {comment_id} | User: {user_id}")
    return success_response("Comment deleted successfully", result)
