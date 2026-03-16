# app/services/bulk_service.py
from app.models.task import Task
from app.models.user import User
from app.models.enums import TaskStatus, TaskPriority, UserRole
from app import db
from app.utils.logger import get_logger
from app.utils.cache_utils import invalidate_user_cache

logger = get_logger('bulk_service')

_ALLOWED_BULK_STATUS_FIELDS = {
    'status': (TaskStatus, 'status'),
    'priority': (TaskPriority, 'priority'),
}


class BulkOperationService:

    @staticmethod
    def bulk_update_tasks(task_ids, updates, requesting_user_id, requesting_user_role):
        """
        Bulk update multiple tasks.

        Allowed updates:
        - status: new TaskStatus value
        - priority: new TaskPriority value
        - assigned_to_id: user id (or null to unassign)
        - sprint_id: sprint id (or null to remove from sprint)
        """
        try:
            if not task_ids:
                return {'error': 'task_ids is required'}, 400

            tasks = Task.query.filter(Task.id.in_(task_ids)).all()
            if not tasks:
                return {'error': 'No tasks found with provided IDs'}, 404

            is_admin = requesting_user_role == UserRole.ADMIN
            updated_ids = []
            requesting_user_int = int(requesting_user_id)

            for task in tasks:
                # Non-admins can only update tasks they own or are assigned to
                if not is_admin:
                    if (task.created_by_id != requesting_user_int and
                            task.assigned_to_id != requesting_user_int):
                        continue

                if 'status' in updates:
                    try:
                        task.status = TaskStatus[updates['status'].upper()]
                    except KeyError:
                        return {'error': f"Invalid status: {updates['status']}"}, 400

                if 'priority' in updates:
                    try:
                        task.priority = TaskPriority[updates['priority'].upper()]
                    except KeyError:
                        return {
                            'error': f"Invalid priority: {updates['priority']}"
                        }, 400

                if 'assigned_to_id' in updates:
                    val = updates['assigned_to_id']
                    if val is None:
                        task.assigned_to_id = None
                    else:
                        task.assigned_to_id = int(val)

                if 'sprint_id' in updates:
                    val = updates['sprint_id']
                    task.sprint_id = None if val is None else int(val)

                updated_ids.append(task.id)

            db.session.commit()
            logger.info(
                f"Bulk updated {len(updated_ids)} tasks by user {requesting_user_id}"
            )
            return {
                'updated_count': len(updated_ids),
                'updated_ids': updated_ids,
                'skipped_count': len(task_ids) - len(updated_ids),
            }, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk task update error: {e}")
            return {'error': f'Bulk update error: {str(e)}'}, 500

    @staticmethod
    def bulk_delete_tasks(task_ids, requesting_user_id, requesting_user_role):
        """Bulk delete tasks (admin can delete any; others only their own)."""
        try:
            if not task_ids:
                return {'error': 'task_ids is required'}, 400

            tasks = Task.query.filter(Task.id.in_(task_ids)).all()
            if not tasks:
                return {'error': 'No tasks found with provided IDs'}, 404

            is_admin = requesting_user_role == UserRole.ADMIN
            deleted_ids = []
            requesting_user_int = int(requesting_user_id)

            for task in tasks:
                if not is_admin and task.created_by_id != requesting_user_int:
                    continue
                db.session.delete(task)
                deleted_ids.append(task.id)

            db.session.commit()
            logger.info(
                f"Bulk deleted {len(deleted_ids)} tasks by user {requesting_user_id}"
            )
            return {
                'deleted_count': len(deleted_ids),
                'deleted_ids': deleted_ids,
                'skipped_count': len(task_ids) - len(deleted_ids),
            }, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk task delete error: {e}")
            return {'error': f'Bulk delete error: {str(e)}'}, 500

    @staticmethod
    def bulk_assign_tasks(task_ids, assignee_id, requesting_user_id,
                          requesting_user_role):
        """Assign multiple tasks to a user."""
        try:
            if not task_ids:
                return {'error': 'task_ids is required'}, 400

            assignee = User.query.get(assignee_id)
            if not assignee:
                return {'error': 'Assignee not found'}, 404

            tasks = Task.query.filter(Task.id.in_(task_ids)).all()
            if not tasks:
                return {'error': 'No tasks found with provided IDs'}, 404

            is_admin = requesting_user_role == UserRole.ADMIN
            assigned_ids = []
            requesting_user_int = int(requesting_user_id)

            for task in tasks:
                if not is_admin and task.created_by_id != requesting_user_int:
                    continue
                task.assigned_to_id = assignee_id
                assigned_ids.append(task.id)

            db.session.commit()
            invalidate_user_cache(assignee_id)
            logger.info(
                f"Bulk assigned {len(assigned_ids)} tasks to user {assignee_id}"
            )
            return {
                'assigned_count': len(assigned_ids),
                'assigned_ids': assigned_ids,
                'assignee_id': assignee_id,
                'skipped_count': len(task_ids) - len(assigned_ids),
            }, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk task assign error: {e}")
            return {'error': f'Bulk assign error: {str(e)}'}, 500

    @staticmethod
    def bulk_change_sprint(task_ids, sprint_id, requesting_user_id,
                           requesting_user_role):
        """Move multiple tasks to a sprint (or remove from sprint if None)."""
        try:
            if not task_ids:
                return {'error': 'task_ids is required'}, 400

            if sprint_id is not None:
                from app.models.sprint import Sprint
                sprint = Sprint.query.get(sprint_id)
                if not sprint:
                    return {'error': 'Sprint not found'}, 404

            tasks = Task.query.filter(Task.id.in_(task_ids)).all()
            if not tasks:
                return {'error': 'No tasks found with provided IDs'}, 404

            is_admin = requesting_user_role == UserRole.ADMIN
            updated_ids = []
            requesting_user_int = int(requesting_user_id)

            for task in tasks:
                if not is_admin and task.created_by_id != requesting_user_int:
                    continue
                task.sprint_id = sprint_id
                updated_ids.append(task.id)

            db.session.commit()
            logger.info(
                f"Bulk moved {len(updated_ids)} tasks to sprint {sprint_id}"
            )
            return {
                'updated_count': len(updated_ids),
                'updated_ids': updated_ids,
                'sprint_id': sprint_id,
                'skipped_count': len(task_ids) - len(updated_ids),
            }, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk sprint change error: {e}")
            return {'error': f'Bulk sprint change error: {str(e)}'}, 500
