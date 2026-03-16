# app/services/activity_service.py
import json
from app.models.activity_log import ActivityLog
from app import db
from app.utils.logger import get_logger

logger = get_logger('activity')


class ActivityService:

    @staticmethod
    def log(entity_type, entity_id, action, user_id=None, details=None):
        """Create an activity log entry."""
        try:
            details_str = json.dumps(details) if details and not isinstance(details, str) else details
            entry = ActivityLog(
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                user_id=user_id,
                details=details_str,
            )
            db.session.add(entry)
            db.session.commit()
            return entry.to_dict(), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error logging activity: {str(e)}')
            return {'error': f'Error logging activity: {str(e)}'}, 500

    @staticmethod
    def get_task_activity(task_id, page=1, per_page=20):
        """Get activity log for a specific task."""
        try:
            query = ActivityLog.query.filter_by(entity_type='task', entity_id=task_id)
            total = query.count()
            entries = (
                query.order_by(ActivityLog.created_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
                .all()
            )
            return {
                'activity': [e.to_dict() for e in entries],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page,
            }, 200

        except Exception as e:
            logger.error(f'Error fetching task activity for task {task_id}: {str(e)}')
            return {'error': f'Error fetching activity: {str(e)}'}, 500

    @staticmethod
    def get_project_activity(project_id, page=1, per_page=20):
        """Get activity log for a specific project."""
        try:
            query = ActivityLog.query.filter_by(entity_type='project', entity_id=project_id)
            total = query.count()
            entries = (
                query.order_by(ActivityLog.created_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
                .all()
            )
            return {
                'activity': [e.to_dict() for e in entries],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page,
            }, 200

        except Exception as e:
            logger.error(f'Error fetching project activity for project {project_id}: {str(e)}')
            return {'error': f'Error fetching activity: {str(e)}'}, 500

    @staticmethod
    def get_user_activity(user_id, page=1, per_page=20):
        """Get all activity performed by a specific user."""
        try:
            query = ActivityLog.query.filter_by(user_id=user_id)
            total = query.count()
            entries = (
                query.order_by(ActivityLog.created_at.desc())
                .offset((page - 1) * per_page)
                .limit(per_page)
                .all()
            )
            return {
                'activity': [e.to_dict() for e in entries],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page,
            }, 200

        except Exception as e:
            logger.error(f'Error fetching activity for user {user_id}: {str(e)}')
            return {'error': f'Error fetching activity: {str(e)}'}, 500
