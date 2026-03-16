# app/services/activity_service.py
from app.models.activity_log import ActivityLog
from app.models.task import Task
from app.models.project import Project
from app import db
from app.utils.logger import get_logger

logger = get_logger('activity_service')


class ActivityService:

    @staticmethod
    def get_task_activity(task_id, page=1, per_page=20):
        """Get activity timeline for a specific task."""
        try:
            task = Task.query.get(task_id)
            if not task:
                return {'error': 'Task not found'}, 404

            query = ActivityLog.query.filter_by(
                entity_type='task', entity_id=task_id
            ).order_by(ActivityLog.created_at.desc())

            total = query.count()
            logs = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'task_id': task_id,
                'data': [log.to_dict() for log in logs],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page,
            }, 200

        except Exception as e:
            logger.error(f"Error fetching task activity for task {task_id}: {e}")
            return {'error': f'Error fetching activity: {str(e)}'}, 500

    @staticmethod
    def get_project_activity(project_id, page=1, per_page=20):
        """Get activity feed for a project (includes tasks/sprints within it)."""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}, 404

            # Include activity on the project itself and all its tasks
            task_ids = [t.id for t in project.tasks]

            query = ActivityLog.query.filter(
                db.or_(
                    db.and_(
                        ActivityLog.entity_type == 'project',
                        ActivityLog.entity_id == project_id,
                    ),
                    db.and_(
                        ActivityLog.entity_type == 'task',
                        ActivityLog.entity_id.in_(task_ids),
                    ),
                )
            ).order_by(ActivityLog.created_at.desc())

            total = query.count()
            logs = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'project_id': project_id,
                'data': [log.to_dict() for log in logs],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page,
            }, 200

        except Exception as e:
            logger.error(f"Error fetching project activity for {project_id}: {e}")
            return {'error': f'Error fetching activity: {str(e)}'}, 500

    @staticmethod
    def get_user_activity(user_id, page=1, per_page=20):
        """Get action history for a specific user."""
        try:
            query = ActivityLog.query.filter_by(
                user_id=user_id
            ).order_by(ActivityLog.created_at.desc())

            total = query.count()
            logs = query.offset((page - 1) * per_page).limit(per_page).all()

            return {
                'user_id': user_id,
                'data': [log.to_dict() for log in logs],
                'total': total,
                'page': page,
                'per_page': per_page,
                'total_pages': (total + per_page - 1) // per_page,
            }, 200

        except Exception as e:
            logger.error(f"Error fetching user activity for {user_id}: {e}")
            return {'error': f'Error fetching activity: {str(e)}'}, 500

    @staticmethod
    def get_recent_activity(limit=50, entity_type=None):
        """Get the most recent activity across all entities."""
        try:
            query = ActivityLog.query

            if entity_type:
                query = query.filter_by(entity_type=entity_type)

            query = query.order_by(ActivityLog.created_at.desc()).limit(limit)
            logs = query.all()

            return {
                'data': [log.to_dict() for log in logs],
                'total': len(logs),
            }, 200

        except Exception as e:
            logger.error(f"Error fetching recent activity: {e}")
            return {'error': f'Error fetching activity: {str(e)}'}, 500

    @staticmethod
    def log_activity(user_id, entity_type, entity_id, action,
                     description=None, field_name=None, old_value=None,
                     new_value=None, ip_address=None):
        """Persist an activity log entry. Commits immediately."""
        try:
            entry = ActivityLog(
                user_id=user_id,
                entity_type=entity_type,
                entity_id=entity_id,
                action=action,
                description=description,
                field_name=field_name,
                old_value=str(old_value) if old_value is not None else None,
                new_value=str(new_value) if new_value is not None else None,
                ip_address=ip_address,
            )
            db.session.add(entry)
            db.session.commit()
            return entry.to_dict(), 201
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error logging activity: {e}")
            return {'error': f'Error logging activity: {str(e)}'}, 500
