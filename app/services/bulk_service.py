# app/services/bulk_service.py
from app.models.task import Task
from app.models.user import User
from app.models.enums import TaskStatus, TaskPriority, UserRole
from app import db
from app.utils.logger import get_logger

logger = get_logger('bulk')


class BulkService:

    @staticmethod
    def _get_tasks(task_ids, user_id):
        """Retrieve tasks and verify they exist."""
        tasks = Task.query.filter(Task.id.in_(task_ids)).all()
        found_ids = {t.id for t in tasks}
        missing = set(task_ids) - found_ids
        return tasks, missing

    @staticmethod
    def bulk_update(task_ids, updates, user_id):
        """Bulk update tasks with the given field values."""
        try:
            if not task_ids:
                return {'error': 'No task IDs provided'}, 400

            tasks, missing = BulkService._get_tasks(task_ids, user_id)
            if missing:
                logger.warning(f'Tasks not found during bulk update: {missing}')

            allowed_fields = ['status', 'priority', 'sprint_id', 'due_date', 'labels']
            updated = []
            for task in tasks:
                for field in allowed_fields:
                    if field in updates:
                        if field == 'status':
                            try:
                                task.status = TaskStatus[updates['status'].upper()]
                            except KeyError:
                                return {'error': f"Invalid status: {updates['status']}"}, 400
                        elif field == 'priority':
                            try:
                                task.priority = TaskPriority[updates['priority'].upper()]
                            except KeyError:
                                return {'error': f"Invalid priority: {updates['priority']}"}, 400
                        else:
                            setattr(task, field, updates[field])
                updated.append(task.id)

            db.session.commit()
            logger.info(f'Bulk updated {len(updated)} tasks by user {user_id}')
            return {
                'updated_count': len(updated),
                'updated_ids': updated,
                'missing_ids': list(missing),
            }, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error in bulk update by user {user_id}: {str(e)}')
            return {'error': f'Error in bulk update: {str(e)}'}, 500

    @staticmethod
    def bulk_delete(task_ids, user_id):
        """Bulk delete tasks. Creator or admin only."""
        try:
            if not task_ids:
                return {'error': 'No task IDs provided'}, 400

            requesting_user = User.query.get(user_id)
            is_admin = requesting_user and requesting_user.role == UserRole.ADMIN

            tasks, missing = BulkService._get_tasks(task_ids, user_id)
            deleted = []
            forbidden = []

            for task in tasks:
                if not is_admin and int(task.created_by_id) != int(user_id):
                    forbidden.append(task.id)
                    continue
                db.session.delete(task)
                deleted.append(task.id)

            db.session.commit()
            logger.info(f'Bulk deleted {len(deleted)} tasks by user {user_id}')
            return {
                'deleted_count': len(deleted),
                'deleted_ids': deleted,
                'missing_ids': list(missing),
                'forbidden_ids': forbidden,
            }, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error in bulk delete by user {user_id}: {str(e)}')
            return {'error': f'Error in bulk delete: {str(e)}'}, 500

    @staticmethod
    def bulk_assign(task_ids, assignee_id, user_id):
        """Bulk assign tasks to a user."""
        try:
            if not task_ids:
                return {'error': 'No task IDs provided'}, 400

            assignee = User.query.get(assignee_id)
            if not assignee:
                return {'error': 'Assignee user not found'}, 404

            tasks, missing = BulkService._get_tasks(task_ids, user_id)
            assigned = []
            for task in tasks:
                task.assigned_to_id = assignee_id
                assigned.append(task.id)

            db.session.commit()
            logger.info(f'Bulk assigned {len(assigned)} tasks to user {assignee_id} by user {user_id}')
            return {
                'assigned_count': len(assigned),
                'assigned_ids': assigned,
                'missing_ids': list(missing),
                'assignee': assignee.to_dict(),
            }, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error in bulk assign by user {user_id}: {str(e)}')
            return {'error': f'Error in bulk assign: {str(e)}'}, 500

    @staticmethod
    def bulk_change_status(task_ids, status, user_id):
        """Bulk change task status."""
        return BulkService.bulk_update(task_ids, {'status': status}, user_id)

    @staticmethod
    def bulk_change_priority(task_ids, priority, user_id):
        """Bulk change task priority."""
        return BulkService.bulk_update(task_ids, {'priority': priority}, user_id)
