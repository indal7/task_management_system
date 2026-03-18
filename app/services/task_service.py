from app.models.task import Task
from app.models.task_comment import TaskComment
from app.models.user import User
from app.models.project import Project
from app.models.sprint import Sprint
from app.models.notification import Notification
from app.models.time_log import TimeLog
from app.models.task_workflow_history import TaskWorkflowHistory
from app import db
from app.models.enums import TaskStatus, TaskPriority, TaskType, NotificationType
from datetime import datetime, timedelta
import json
from app.utils.cache_utils import cache, cached_per_user, CacheKeys, invalidate_user_cache, invalidate_project_cache
from app.utils.logger import get_logger, log_db_query, log_api_request

# Initialize logger for this module
logger = get_logger('tasks')


class TaskService:
    @staticmethod
    def _extract_workflow_stage(labels_value):
        """Extract sprint board stage marker from labels list/json."""
        labels = []

        if isinstance(labels_value, str):
            try:
                labels = json.loads(labels_value)
            except Exception:
                labels = []
        elif isinstance(labels_value, list):
            labels = labels_value

        for label in labels:
            if isinstance(label, str) and label.startswith('__workflow_stage:'):
                return label.split(':', 1)[1]
        return None

    @staticmethod
    def _create_workflow_history(
        task_id,
        changed_by_id,
        from_status=None,
        to_status=None,
        from_stage=None,
        to_stage=None,
        from_sprint_id=None,
        to_sprint_id=None,
        from_assignee_id=None,
        to_assignee_id=None,
        change_reason=None,
    ):
        entry = TaskWorkflowHistory(
            task_id=task_id,
            changed_by_id=changed_by_id,
            from_status=from_status,
            to_status=to_status,
            from_stage=from_stage,
            to_stage=to_stage,
            from_sprint_id=from_sprint_id,
            to_sprint_id=to_sprint_id,
            from_assignee_id=from_assignee_id,
            to_assignee_id=to_assignee_id,
            change_reason=change_reason,
        )
        db.session.add(entry)

    @staticmethod
    def create_task(dto, user_id):
        """Create a new task with enhanced IT features."""
        try:
            user = User.query.get_or_404(user_id)

            project_id = dto.get('project_id')
            if project_id:
                project = Project.query.get_or_404(project_id)
                if not user.has_project_permission(project_id, 'create_tasks') and project.owner_id != user_id:
                    return {'error': 'Insufficient permissions to create task in this project'}, 403

            try:
                logger.info(f"Creating new task for user {user_id}")
                priority = TaskPriority[dto.get('priority', 'MEDIUM').upper()]
                task_type = TaskType[dto.get('task_type', 'FEATURE').upper()]
                status = TaskStatus[dto.get('status', 'BACKLOG').upper()]
            except KeyError as e:
                return {'error': f'Invalid enum value: {str(e)}'}, 400

            due_date = datetime.fromisoformat(dto['due_date'].replace('Z', '+00:00')) if dto.get('due_date') else None
            start_date = datetime.fromisoformat(dto['start_date'].replace('Z', '+00:00')) if dto.get('start_date') else None

            labels = dto.get('labels', [])
            labels_json = json.dumps(labels) if labels else None

            task = Task(
                title=dto.get('title'),
                description=dto.get('description'),
                priority=priority,
                task_type=task_type,
                status=status,
                project_id=project_id,
                sprint_id=dto.get('sprint_id'),
                due_date=due_date,
                start_date=start_date,
                estimated_hours=dto.get('estimated_hours'),
                story_points=dto.get('story_points'),
                acceptance_criteria=dto.get('acceptance_criteria'),
                parent_task_id=dto.get('parent_task_id'),
                labels=labels_json,
                team_key=(dto.get('team_key') or None),
                created_by_id=user.id,
                assigned_to_id=dto.get('assigned_to_id')
            )

            db.session.add(task)
            db.session.flush()

            # Initial workflow snapshot
            TaskService._create_workflow_history(
                task_id=task.id,
                changed_by_id=user_id,
                from_status=None,
                to_status=task.status.value,
                from_stage=None,
                to_stage=TaskService._extract_workflow_stage(labels_json),
                from_sprint_id=None,
                to_sprint_id=task.sprint_id,
                from_assignee_id=None,
                to_assignee_id=task.assigned_to_id,
                change_reason='Task created'
            )
            db.session.commit()
            logger.info(f"Task created successfully: {task.id} - '{task.title}' by user {user_id}")
            log_db_query("INSERT", "tasks")

            invalidate_user_cache(user_id, CacheKeys.USER_TASKS)
            if project_id:
                invalidate_project_cache(project_id)

            if task.assigned_to_id and task.assigned_to_id != user_id:
                Notification.create_notification(
                    user_id=task.assigned_to_id,
                    notification_type=NotificationType.TASK_ASSIGNED,
                    title=f"New Task Assigned: {task.title}",
                    message=f"{user.name} assigned you a new {task.task_type.value.lower()} task",
                    task_id=task.id,
                    related_user_id=user_id,
                    project_id=project_id
                )

            return task.to_dict(), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Task creation failed for user {user_id}: {str(e)}")
            return {'error': f'Error creating task: {str(e)}'}, 500

    @staticmethod
    def update_task(task_id, dto, user_id):
        """Update task with enhanced features."""
        try:
            logger.info(f"Updating task {task_id} by user {user_id}")
            task = Task.query.get_or_404(task_id)
            user = User.query.get_or_404(user_id)

            if task.project_id:
                if not user.has_project_permission(task.project_id, 'edit_tasks') and task.project.owner_id != user_id and task.created_by_id != user_id:
                    return {'error': 'Insufficient permissions to update this task'}, 403

            old_assignee_id = task.assigned_to_id
            old_status = task.status
            old_sprint_id = task.sprint_id
            old_stage = TaskService._extract_workflow_stage(task.labels)

            # Basic updates
            for field in ['title', 'description', 'acceptance_criteria', 'team_key']:
                if field in dto:
                    setattr(task, field, dto[field])

            # Enum updates
            if 'priority' in dto:
                try:
                    task.priority = TaskPriority[dto['priority'].upper()]
                except KeyError:
                    return {'error': 'Invalid priority'}, 400

            if 'task_type' in dto:
                try:
                    task.task_type = TaskType[dto['task_type'].upper()]
                except KeyError:
                    return {'error': 'Invalid task type'}, 400

            if 'status' in dto:
                try:
                    new_status = TaskStatus[dto['status'].upper()]
                    task.status = new_status
                    if new_status == TaskStatus.DONE and old_status != TaskStatus.DONE:
                        task.completion_date = datetime.utcnow()
                    elif new_status != TaskStatus.DONE:
                        task.completion_date = None
                except KeyError:
                    return {'error': 'Invalid status'}, 400

            for date_field in ['due_date', 'start_date']:
                if date_field in dto:
                    value = dto[date_field]
                    setattr(task, date_field, datetime.fromisoformat(value.replace('Z', '+00:00')) if value else None)

            # Other updates
            for field in ['estimated_hours', 'story_points', 'assigned_to_id', 'project_id', 'sprint_id']:
                if field in dto:
                    setattr(task, field, dto[field])

            if 'labels' in dto:
                labels = dto['labels']
                task.labels = json.dumps(labels) if labels else None

            new_stage = TaskService._extract_workflow_stage(task.labels)

            status_changed = task.status != old_status
            sprint_changed = task.sprint_id != old_sprint_id
            assignee_changed = task.assigned_to_id != old_assignee_id
            stage_changed = old_stage != new_stage

            if status_changed or sprint_changed or assignee_changed or stage_changed:
                TaskService._create_workflow_history(
                    task_id=task.id,
                    changed_by_id=user_id,
                    from_status=old_status.value if old_status else None,
                    to_status=task.status.value if task.status else None,
                    from_stage=old_stage,
                    to_stage=new_stage,
                    from_sprint_id=old_sprint_id,
                    to_sprint_id=task.sprint_id,
                    from_assignee_id=old_assignee_id,
                    to_assignee_id=task.assigned_to_id,
                    change_reason='Task updated'
                )

            db.session.commit()
            logger.info(f"Task updated successfully: {task.id} - status: {task.status.value}")
            log_db_query("UPDATE", "tasks")

            if task.assigned_to_id:
                invalidate_user_cache(task.assigned_to_id, CacheKeys.USER_TASKS)
            if old_assignee_id and old_assignee_id != task.assigned_to_id:
                invalidate_user_cache(old_assignee_id, CacheKeys.USER_TASKS)
            if task.project_id:
                invalidate_project_cache(task.project_id)

            TaskService._handle_task_update_notifications(task, user_id, old_assignee_id, old_status)

            return task.to_dict(), 200

        except Exception as e:
            db.session.rollback()
            return {'error': f'Error updating task: {str(e)}'}, 500

    @staticmethod
    def delete_task(task_id, user_id):
        """Delete a task."""
        try:
            task = Task.query.get_or_404(task_id)
            user = User.query.get_or_404(user_id)

            if task.project_id:
                is_project_owner = task.project.owner_id == user_id
                is_task_assignee = task.assigned_to_id == user_id
                has_delete_permission = user.has_project_permission(task.project_id, 'delete_tasks')
                is_privileged_role = user.role.value in ['ADMIN', 'PROJECT_MANAGER']

                if not (is_project_owner or is_task_assignee or has_delete_permission or is_privileged_role):
                    return {'error': 'Insufficient permissions to delete this task'}, 403

            db.session.delete(task)
            db.session.commit()
            return {"message": "Task deleted successfully", "task_id": task_id}, 200

        except Exception as e:
            db.session.rollback()
            return {'error': f'Error deleting task: {str(e)}'}, 500

    @staticmethod
    def assign_task(task_id, user_id, assigner_id):
        """Assign a task to a user."""
        try:
            task = Task.query.get_or_404(task_id)
            user = User.query.get_or_404(user_id)
            assigner = User.query.get_or_404(assigner_id)

            if task.project_id:
                if not assigner.has_project_permission(task.project_id, 'edit_tasks') and task.project.owner_id != assigner_id:
                    return {'error': 'Insufficient permissions to assign this task'}, 403

            old_assignee_id = task.assigned_to_id
            task.assigned_to_id = user_id
            db.session.commit()

            if user_id != assigner_id:
                Notification.create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.TASK_ASSIGNED,
                    title=f"Task Assigned: {task.title}",
                    message=f"{assigner.name} assigned you to task '{task.title}'",
                    task_id=task.id,
                    related_user_id=assigner_id,
                    project_id=task.project_id
                )

            return task.to_dict(), 200

        except Exception as e:
            db.session.rollback()
            return {'error': f'Error assigning task: {str(e)}'}, 500

    @staticmethod
    def get_task_by_id(task_id, user_id):
        """Get task by ID with permission check."""
        try:
            task = Task.query.get_or_404(task_id)
            user = User.query.get_or_404(user_id)

            if task.project_id:
                if not user.has_project_permission(task.project_id, 'create_tasks') and task.project.owner_id != user_id:
                    return {'error': 'Insufficient permissions to view this task'}, 403

            return task.to_dict(include_subtasks=True), 200

        except Exception as e:
            return {'error': f'Error fetching task: {str(e)}'}, 500

    @staticmethod
    def get_tasks_by_filters(user_id, filters=None):
        """Get tasks with advanced filtering."""
        try:
            user = User.query.get_or_404(user_id)
            query = Task.query

            if filters:
                if filters.get('project_id'):
                    project_id = filters['project_id']
                    project = Project.query.get_or_404(project_id)
                    if not user.has_project_permission(project_id, 'create_tasks') and project.owner_id != user_id:
                        return {'error': 'Insufficient permissions to view tasks in this project'}, 403
                    query = query.filter(Task.project_id == project_id)

                if filters.get('sprint_id'):
                    query = query.filter(Task.sprint_id == filters['sprint_id'])

                if filters.get('team_key'):
                    query = query.filter(Task.team_key == filters['team_key'])

                if filters.get('assigned_to_id'):
                    query = query.filter(Task.assigned_to_id == filters['assigned_to_id'])

                if filters.get('created_by_id'):
                    query = query.filter(Task.created_by_id == filters['created_by_id'])

                for field, enum_class in [('status', TaskStatus), ('priority', TaskPriority), ('task_type', TaskType)]:
                    if filters.get(field):
                        raw_value = filters[field]
                        if isinstance(raw_value, str):
                            raw_items = [item.strip() for item in raw_value.split(',') if item.strip()]
                        elif isinstance(raw_value, list):
                            raw_items = [str(item).strip() for item in raw_value if str(item).strip()]
                        else:
                            raw_items = [str(raw_value).strip()]

                        enum_values = []
                        for item in raw_items:
                            try:
                                enum_values.append(enum_class[item.upper()])
                            except KeyError:
                                return {'error': f'Invalid {field} filter: {item}'}, 400

                        if len(enum_values) == 1:
                            query = query.filter(getattr(Task, field) == enum_values[0])
                        elif len(enum_values) > 1:
                            query = query.filter(getattr(Task, field).in_(enum_values))

                if filters.get('start_date'):
                    try:
                        start_date = datetime.fromisoformat(str(filters['start_date']))
                        query = query.filter(Task.due_date >= start_date)
                    except ValueError:
                        return {'error': 'Invalid start_date format. Expected YYYY-MM-DD'}, 400

                if filters.get('end_date'):
                    try:
                        end_date = datetime.fromisoformat(str(filters['end_date'])) + timedelta(days=1)
                        query = query.filter(Task.due_date < end_date)
                    except ValueError:
                        return {'error': 'Invalid end_date format. Expected YYYY-MM-DD'}, 400

                if filters.get('overdue'):
                    query = query.filter(Task.due_date < datetime.utcnow(), Task.status != TaskStatus.DONE)

                if filters.get('parent_task_id'):
                    query = query.filter(Task.parent_task_id == filters['parent_task_id'])

            if not filters or not filters.get('project_id'):
                query = query.filter(db.or_(Task.assigned_to_id == user_id, Task.created_by_id == user_id))

            query = query.order_by(Task.priority.desc(), Task.due_date.asc())
            tasks = query.all()

            return [task.to_dict() for task in tasks], 200

        except Exception as e:
            return {'error': f'Error fetching tasks: {str(e)}'}, 500

    @staticmethod
    def add_comment(task_id, user_id, comment_text):
        """Add a comment to a task."""
        try:
            task = Task.query.get_or_404(task_id)
            user = User.query.get_or_404(user_id)

            if task.project_id:
                if not user.has_project_permission(task.project_id, 'create_tasks') and task.project.owner_id != user_id:
                    return {'error': 'Insufficient permissions to comment on this task'}, 403

            new_comment = TaskComment(task_id=task_id, user_id=user_id, comment=comment_text)
            db.session.add(new_comment)
            db.session.commit()

            notification_users = set()
            if task.assigned_to_id and task.assigned_to_id != user_id:
                notification_users.add(task.assigned_to_id)
            if task.created_by_id and task.created_by_id != user_id:
                notification_users.add(task.created_by_id)

            for notify_user_id in notification_users:
                Notification.create_notification(
                    user_id=notify_user_id,
                    notification_type=NotificationType.COMMENT_ADDED,
                    title=f"New Comment on: {task.title}",
                    message=f"{user.name} added a comment to task '{task.title}'",
                    task_id=task.id,
                    related_user_id=user_id,
                    project_id=task.project_id
                )

            return {
                "id": new_comment.id,
                "text": new_comment.comment,
                "author": {"id": user.id, "name": user.name},
                "createdAt": new_comment.created_at.isoformat()
            }, 201

        except Exception as e:
            db.session.rollback()
            return {"error": str(e)}, 500

    @staticmethod
    def log_time(task_id, user_id, hours, description, work_date=None):
        """Log time spent on a task."""
        try:
            task = Task.query.get_or_404(task_id)
            user = User.query.get_or_404(user_id)

            if task.project_id:
                if not user.has_project_permission(task.project_id, 'create_tasks') and task.project.owner_id != user_id:
                    return {'error': 'Insufficient permissions to log time on this task'}, 403

            work_date = datetime.fromisoformat(work_date).date() if work_date else datetime.utcnow().date()
            time_log = TimeLog(task_id=task_id, user_id=user_id, hours=hours, description=description, work_date=work_date)
            time_log.validate_hours()

            db.session.add(time_log)
            task.actual_hours = (task.actual_hours or 0) + hours
            db.session.commit()

            return time_log.to_dict(), 201

        except ValueError as e:
            return {'error': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            return {'error': f'Error logging time: {str(e)}'}, 500

    @staticmethod
    def get_task_time_logs(task_id, user_id):
        """Get time logs for a task."""
        try:
            task = Task.query.get_or_404(task_id)
            user = User.query.get_or_404(user_id)

            if task.project_id:
                if not user.has_project_permission(task.project_id, 'create_tasks') and task.project.owner_id != user_id:
                    return {'error': 'Insufficient permissions to view time logs for this task'}, 403

            time_logs = TimeLog.query.filter_by(task_id=task_id).order_by(TimeLog.work_date.desc()).all()
            return [log.to_dict() for log in time_logs], 200

        except Exception as e:
            return {'error': f'Error fetching time logs: {str(e)}'}, 500

    @staticmethod
    def update_time_log(task_id, time_log_id, user_id, hours=None, description=None, work_date=None):
        """Update a time log for a task."""
        try:
            task = Task.query.get_or_404(task_id)
            user = User.query.get_or_404(user_id)
            time_log = TimeLog.query.filter_by(id=time_log_id, task_id=task_id, user_id=user_id).first()

            if not time_log:
                return {'error': 'Time log not found'}, 404

            if task.project_id:
                if not user.has_project_permission(task.project_id, 'create_tasks') and task.project.owner_id != user_id:
                    return {'error': 'Insufficient permissions to update time on this task'}, 403

            previous_hours = time_log.hours or 0

            if hours is not None:
                if hours <= 0:
                    return {'error': 'Valid hours (> 0) are required'}, 400
                time_log.hours = hours

            if description is not None:
                time_log.description = description

            if work_date:
                time_log.work_date = datetime.fromisoformat(work_date).date()

            time_log.validate_hours()
            task.actual_hours = max(0, (task.actual_hours or 0) - previous_hours + (time_log.hours or 0))
            db.session.commit()

            return time_log.to_dict(), 200

        except ValueError as e:
            db.session.rollback()
            return {'error': str(e)}, 400
        except Exception as e:
            db.session.rollback()
            return {'error': f'Error updating time log: {str(e)}'}, 500

    @staticmethod
    def delete_time_log(task_id, time_log_id, user_id):
        """Delete a time log for a task."""
        try:
            task = Task.query.get_or_404(task_id)
            user = User.query.get_or_404(user_id)
            time_log = TimeLog.query.filter_by(id=time_log_id, task_id=task_id, user_id=user_id).first()

            if not time_log:
                return {'error': 'Time log not found'}, 404

            if task.project_id:
                if not user.has_project_permission(task.project_id, 'create_tasks') and task.project.owner_id != user_id:
                    return {'error': 'Insufficient permissions to delete time on this task'}, 403

            task.actual_hours = max(0, (task.actual_hours or 0) - (time_log.hours or 0))
            db.session.delete(time_log)
            db.session.commit()

            return {'message': 'Time log deleted successfully'}, 200

        except Exception as e:
            db.session.rollback()
            return {'error': f'Error deleting time log: {str(e)}'}, 500

    @staticmethod
    def get_overdue_tasks(user_id):
        """Get overdue tasks for a user."""
        try:
            user = User.query.get_or_404(user_id)
            overdue_tasks = Task.query.filter(
                Task.due_date < datetime.utcnow(),
                Task.status != TaskStatus.DONE,
                db.or_(Task.assigned_to_id == user_id, Task.created_by_id == user_id)
            ).order_by(Task.due_date.asc()).all()
            return [task.to_dict() for task in overdue_tasks], 200

        except Exception as e:
            return {'error': f'Error fetching overdue tasks: {str(e)}'}, 500

    @staticmethod
    def _handle_task_update_notifications(task, user_id, old_assignee_id, old_status):
        """Handle notifications for task updates."""
        user = User.query.get(user_id)

        if task.assigned_to_id != old_assignee_id and task.assigned_to_id != user_id:
            Notification.create_notification(
                user_id=task.assigned_to_id,
                notification_type=NotificationType.TASK_ASSIGNED,
                title=f"Task Assigned: {task.title}",
                message=f"{user.name} assigned you to task '{task.title}'",
                task_id=task.id,
                related_user_id=user_id,
                project_id=task.project_id
            )

        if task.status != old_status:
            notification_users = set()
            if task.assigned_to_id and task.assigned_to_id != user_id:
                notification_users.add(task.assigned_to_id)
            if task.created_by_id and task.created_by_id != user_id:
                notification_users.add(task.created_by_id)

            for notify_user_id in notification_users:
                if task.status == TaskStatus.DONE:
                    notification_type = NotificationType.TASK_COMPLETED
                    message = f"{user.name} marked task '{task.title}' as completed"
                else:
                    notification_type = NotificationType.TASK_UPDATED
                    message = f"{user.name} updated task '{task.title}' status to {task.status.value}"

                Notification.create_notification(
                    user_id=notify_user_id,
                    notification_type=notification_type,
                    title=f"Task Updated: {task.title}",
                    message=message,
                    task_id=task.id,
                    related_user_id=user_id,
                    project_id=task.project_id
                )

    @staticmethod
    def get_user_time_logs(user_id, start_date=None, end_date=None, limit=50):
        """Get time logs for a user with optional date filtering."""
        try:
            user = User.query.get_or_404(user_id)
            query = TimeLog.query.filter_by(user_id=user_id)

            if start_date:
                try:
                    query = query.filter(TimeLog.work_date >= datetime.fromisoformat(start_date).date())
                except ValueError:
                    return {'error': 'Invalid start_date format. Use YYYY-MM-DD'}, 400
            if end_date:
                try:
                    query = query.filter(TimeLog.work_date <= datetime.fromisoformat(end_date).date())
                except ValueError:
                    return {'error': 'Invalid end_date format. Use YYYY-MM-DD'}, 400

            time_logs = query.order_by(TimeLog.work_date.desc(), TimeLog.logged_at.desc()).limit(limit).all()
            total_hours = sum(log.hours for log in time_logs)

            daily_breakdown = {}
            for log in time_logs:
                date_str = log.work_date.isoformat()
                if date_str not in daily_breakdown:
                    daily_breakdown[date_str] = {'date': date_str, 'total_hours': 0, 'logs': []}
                daily_breakdown[date_str]['total_hours'] += log.hours
                daily_breakdown[date_str]['logs'].append(log.to_dict())

            return {
                'time_logs': [log.to_dict() for log in time_logs],
                'total_hours': total_hours,
                'total_entries': len(time_logs),
                'daily_breakdown': list(daily_breakdown.values()),
                'user': user.to_dict()
            }, 200

        except Exception as e:
            return {'error': f'Error fetching user time logs: {str(e)}'}, 500

    @staticmethod
    def get_task_history(task_id, user_id):
        """Return task workflow transition history ordered by newest first."""
        try:
            task = Task.query.get_or_404(task_id)
            user = User.query.get_or_404(user_id)

            if task.project_id:
                if not user.has_project_permission(task.project_id, 'create_tasks') and task.project.owner_id != user_id:
                    return {'error': 'Insufficient permissions to view task history'}, 403

            history = (
                TaskWorkflowHistory.query
                .filter_by(task_id=task_id)
                .order_by(TaskWorkflowHistory.created_at.desc())
                .all()
            )

            return [entry.to_dict() for entry in history], 200
        except Exception as e:
            return {'error': f'Error fetching task history: {str(e)}'}, 500
