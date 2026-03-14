# app/routes/notification_routes.py
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.services.notification_service import NotificationService
from app.utils.response import (
    success_response, error_response, not_found_response, server_error_response
)
from app.utils.logger import get_logger, log_cache_operation
from app.utils.cache_utils import cache

notification_bp = Blueprint('notification', __name__, url_prefix='/api/notifications')
logger = get_logger('api')  # You can also use 'notification' for a separate logger


def cache_notifications(key, fetch_func, timeout=300):
    """Helper to fetch notifications from cache or load fresh"""
    cached_data = cache.get(key)
    log_cache_operation("GET", key, hit=bool(cached_data))
    if cached_data:
        logger.info(f"Cache hit for {key}")
        return cached_data
    data = fetch_func()
    cache.set(key, data, timeout=timeout)
    log_cache_operation("SET", key)
    logger.info(f"Cache set for {key}")
    return data


@notification_bp.route('/summary', methods=['GET'])
@jwt_required()
def get_notification_summary():
    """Get notification summary for dashboard."""
    user_id = get_jwt_identity()
    cache_key = f"notifications:summary:{user_id}"

    try:
        result = cache_notifications(cache_key, lambda: NotificationService.get_notification_summary(user_id))
        logger.info(f"Notification summary retrieved for user {user_id}")
        return success_response("Notification summary retrieved successfully", result)
    except Exception as e:
        logger.error(f"Error fetching notification summary for user {user_id}: {e}", exc_info=True)
        return server_error_response(f'Error fetching notification summary: {str(e)}')


@notification_bp.route('', methods=['GET'])
@jwt_required()
def get_notifications():
    user_id = get_jwt_identity()
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    cache_key = f"notifications:{user_id}:unread={unread_only}"

    try:
        result = cache_notifications(
            cache_key,
            lambda: NotificationService.get_user_notifications(user_id, unread_only)
        )
        message = "Unread notifications retrieved successfully" if unread_only else "Notifications retrieved successfully"
        logger.info(f"{message} | User: {user_id}")
        return success_response(message, result)
    except Exception as e:
        logger.error(f"Error fetching notifications for user {user_id}: {e}", exc_info=True)
        return server_error_response(f'Error fetching notifications: {str(e)}')


@notification_bp.route('/<int:notification_id>/read', methods=['POST'])
@jwt_required()
def mark_as_read(notification_id):
    user_id = get_jwt_identity()
    try:
        result = NotificationService.mark_as_read(notification_id, user_id)
        if 'error' in result:
            logger.warning(f"Mark as read failed | Notification: {notification_id} | User: {user_id}")
            return not_found_response(result['error'])
        logger.info(f"Notification marked as read | Notification: {notification_id} | User: {user_id}")
        cache.delete(f"notifications:summary:{user_id}")  # Invalidate summary cache
        return success_response("Notification marked as read", result)
    except Exception as e:
        logger.error(f"Error marking notification as read | Notification: {notification_id} | User: {user_id}: {e}", exc_info=True)
        return server_error_response(f'Error marking notification as read: {str(e)}')


@notification_bp.route('/read-all', methods=['POST'])
@jwt_required()
def mark_all_as_read():
    user_id = get_jwt_identity()
    try:
        result = NotificationService.mark_all_notifications_as_read(user_id)
        logger.info(f"All notifications marked as read | User: {user_id}")
        cache.delete(f"notifications:summary:{user_id}")  # Invalidate summary cache
        return success_response("All notifications marked as read", result)
    except Exception as e:
        logger.error(f"Error marking all notifications as read | User: {user_id}: {e}", exc_info=True)
        return server_error_response(f'Error marking all notifications as read: {str(e)}')


@notification_bp.route('/<int:notification_id>', methods=['DELETE'])
@jwt_required()
def delete(notification_id):
    user_id = get_jwt_identity()
    try:
        result = NotificationService.delete_notification(notification_id, user_id)
        if 'error' in result:
            logger.warning(f"Delete notification failed | Notification: {notification_id} | User: {user_id}")
            return not_found_response(result['error'])
        logger.info(f"Notification deleted | Notification: {notification_id} | User: {user_id}")
        cache.delete(f"notifications:summary:{user_id}")  # Invalidate summary cache
        return success_response("Notification deleted successfully")
    except Exception as e:
        logger.error(f"Error deleting notification | Notification: {notification_id} | User: {user_id}: {e}", exc_info=True)
        return server_error_response(f'Error deleting notification: {str(e)}')
