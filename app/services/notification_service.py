# app/services/notification_service.py
from app.models.notification import Notification
from app.models.user import User
from app.models.task import Task
from app import db
from app.utils.cache_utils import cache, cached_per_user, CacheKeys, invalidate_user_cache
from app.utils.logger import get_logger, log_db_query
from sqlalchemy import func

logger = get_logger('notifications')


class NotificationService:

    @staticmethod
    @cached_per_user(timeout=300, key_prefix=CacheKeys.USER_NOTIFICATIONS)
    def get_notification_summary(user_id):
        """Get notification summary with counts and recent notifications."""
        try:
            unread_count = Notification.query.filter_by(user_id=user_id, read=False).count()

            recent_notifications = Notification.query.filter_by(user_id=user_id)\
                .order_by(Notification.created_at.desc())\
                .limit(5)\
                .all()

            type_counts = db.session.query(
                Notification.type,
                func.count(Notification.id)
            ).filter(
                Notification.user_id == user_id,
                Notification.read == False
            ).group_by(Notification.type).all()

            type_summary = {nt.value: count for nt, count in type_counts}

            total_notifications = Notification.query.filter_by(user_id=user_id).count()

            logger.info(f"Fetched notification summary for user {user_id}: {unread_count} unread")
            return {
                'unread_count': unread_count,
                'recent_notifications': [n.to_dict() for n in recent_notifications],
                'type_summary': type_summary,
                'total_notifications': total_notifications
            }

        except Exception as e:
            logger.error(f"Error getting notification summary for user {user_id}: {str(e)}")
            return {'error': f'Error getting notification summary: {str(e)}'}, 500

    @staticmethod
    @cached_per_user(timeout=300, key_prefix=CacheKeys.USER_NOTIFICATIONS)
    def get_user_notifications(user_id, unread_only=False):
        """Get all notifications for a user, optionally unread only."""
        try:
            query = Notification.query.filter_by(user_id=user_id)
            if unread_only:
                query = query.filter_by(read=False)
            notifications = query.order_by(Notification.created_at.desc()).all()
            logger.info(f"Fetched {len(notifications)} notifications for user {user_id}")
            return [n.to_dict() for n in notifications]
        except Exception as e:
            logger.error(f"Error fetching notifications for user {user_id}: {str(e)}")
            return {'error': f'Error fetching notifications: {str(e)}'}, 500

    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Mark a single notification as read."""
        try:
            notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
            if not notification:
                logger.warning(f"Notification {notification_id} not found for user {user_id}")
                return {'error': 'Notification not found'}, 404

            notification.read = True
            db.session.commit()
            log_db_query("UPDATE", "notifications")
            logger.info(f"Notification {notification_id} marked as read for user {user_id}")

            # Invalidate user's notification cache
            invalidate_user_cache(user_id)

            return notification.to_dict()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking notification {notification_id} as read: {str(e)}")
            return {'error': f'Error updating notification: {str(e)}'}, 500

    @staticmethod
    def mark_all_notifications_as_read(user_id):
        """Mark all notifications as read for a user."""
        try:
            notifications = Notification.query.filter_by(user_id=user_id, read=False).all()
            for notification in notifications:
                notification.read = True

            db.session.commit()
            log_db_query("UPDATE", "notifications")
            logger.info(f"All notifications marked as read for user {user_id}")

            # Invalidate user's notification cache
            invalidate_user_cache(user_id)

            return {'message': 'All notifications marked as read'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error marking all notifications as read for user {user_id}: {str(e)}")
            return {'error': f'Error updating notifications: {str(e)}'}, 500

    @staticmethod
    def delete_notification(notification_id, user_id):
        """Delete a notification for a user."""
        try:
            notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
            if not notification:
                logger.warning(f"Notification {notification_id} not found for user {user_id}")
                return {'error': 'Notification not found'}, 404

            db.session.delete(notification)
            db.session.commit()
            log_db_query("DELETE", "notifications")
            logger.info(f"Notification {notification_id} deleted for user {user_id}")

            # Invalidate user's notification cache
            invalidate_user_cache(user_id)

            return {'message': 'Notification deleted successfully'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting notification {notification_id}: {str(e)}")
            return {'error': f'Error deleting notification: {str(e)}'}, 500
