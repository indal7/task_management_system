# app/services/sprint_service.py
from app.models.sprint import Sprint
from app.models.project import Project
from app.models.task import Task
from app.models.user import User
from app.models.notification import Notification
from app.models.enums import SprintStatus, NotificationType, TaskStatus
from app import db
from datetime import datetime
from app.utils.cache_utils import cache, cached_per_user, CacheKeys, invalidate_user_cache, invalidate_project_cache
from app.utils.logger import get_logger, log_db_query

logger = get_logger('sprints')


class SprintService:

    @staticmethod
    def create_sprint(data, user_id):
        """Create a new sprint with notifications and caching."""
        try:
            project = Project.query.get_or_404(data.get('project_id'))
            user = User.query.get_or_404(user_id)

            if not user.has_project_permission(project.id, 'manage_sprints') and project.owner_id != user_id:
                logger.warning(f"User {user_id} tried to create sprint without permission for project {project.id}")
                return {'error': 'Insufficient permissions to create sprint'}, 403

            start_date = datetime.fromisoformat(data.get('start_date').replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(data.get('end_date').replace('Z', '+00:00'))

            if start_date >= end_date:
                return {'error': 'Start date must be before end date'}, 400

            sprint = Sprint(
                name=data.get('name'),
                description=data.get('description'),
                project_id=project.id,
                start_date=start_date,
                end_date=end_date,
                goal=data.get('goal'),
                capacity_hours=data.get('capacity_hours'),
                velocity_points=data.get('velocity_points')
            )

            db.session.add(sprint)
            db.session.commit()
            log_db_query("INSERT", "sprints")
            logger.info(f"Sprint created: {sprint.id} by user {user_id}")

            # Notify project team members
            team_members = project.get_team_members()
            for member in team_members:
                if member.id != user_id:
                    Notification.create_notification(
                        user_id=member.id,
                        notification_type=NotificationType.SPRINT_STARTED,
                        title=f"New Sprint Created: {sprint.name}",
                        message=f"{user.name} created a new sprint '{sprint.name}' for project {project.name}",
                        related_user_id=user_id,
                        project_id=project.id,
                        sprint_id=sprint.id
                    )

            invalidate_project_cache(project.id)
            return sprint.to_dict(), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating sprint by user {user_id}: {str(e)}")
            return {'error': f'Error creating sprint: {str(e)}'}, 500

    @staticmethod
    @cached_per_user(timeout=300, key_prefix=CacheKeys.USER_SPRINTS)
    def get_sprint_by_id(sprint_id, include_tasks=False):
        """Get sprint by ID, optionally include tasks."""
        try:
            sprint = Sprint.query.get_or_404(sprint_id)
            logger.info(f"Fetched sprint {sprint_id}")
            return sprint.to_dict(include_tasks=include_tasks), 200
        except Exception as e:
            logger.error(f"Error fetching sprint {sprint_id}: {str(e)}")
            return {'error': f'Sprint not found: {str(e)}'}, 404

    @staticmethod
    def update_sprint(sprint_id, data, user_id):
        """Update sprint details with logging and notifications."""
        try:
            sprint = Sprint.query.get_or_404(sprint_id)
            user = User.query.get_or_404(user_id)

            if not user.has_project_permission(sprint.project_id, 'manage_sprints') and sprint.project.owner_id != user_id:
                logger.warning(f"User {user_id} tried to update sprint {sprint_id} without permission")
                return {'error': 'Insufficient permissions to update sprint'}, 403

            # Update fields
            for field in ['name', 'description', 'goal', 'capacity_hours', 'velocity_points']:
                if field in data:
                    setattr(sprint, field, data[field])

            if 'status' in data:
                try:
                    new_status = SprintStatus[data['status'].upper()]
                    old_status = sprint.status
                    sprint.status = new_status
                    if old_status != new_status:
                        SprintService._handle_status_change(sprint, old_status, new_status, user_id)
                except KeyError:
                    return {'error': 'Invalid sprint status'}, 400

            if 'start_date' in data:
                sprint.start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
            if 'end_date' in data:
                sprint.end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))

            if sprint.start_date >= sprint.end_date:
                return {'error': 'Start date must be before end date'}, 400

            db.session.commit()
            log_db_query("UPDATE", "sprints")
            logger.info(f"Sprint {sprint_id} updated by user {user_id}")

            invalidate_project_cache(sprint.project_id)
            return sprint.to_dict(), 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating sprint {sprint_id}: {str(e)}")
            return {'error': f'Error updating sprint: {str(e)}'}, 500

    @staticmethod
    def delete_sprint(sprint_id, user_id):
        """Delete a sprint, moving tasks back to backlog."""
        try:
            sprint = Sprint.query.get_or_404(sprint_id)
            user = User.query.get_or_404(user_id)

            if not user.has_project_permission(sprint.project_id, 'manage_sprints') and sprint.project.owner_id != user_id:
                logger.warning(f"User {user_id} tried to delete sprint {sprint_id} without permission")
                return {'error': 'Insufficient permissions to delete sprint'}, 403

            for task in sprint.tasks:
                task.sprint_id = None
                task.status = TaskStatus.BACKLOG

            db.session.delete(sprint)
            db.session.commit()
            log_db_query("DELETE", "sprints")
            logger.info(f"Sprint {sprint_id} deleted by user {user_id}")

            invalidate_project_cache(sprint.project_id)
            return {'message': 'Sprint deleted successfully'}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting sprint {sprint_id}: {str(e)}")
            return {'error': f'Error deleting sprint: {str(e)}'}, 500

    @staticmethod
    @cached_per_user(timeout=300, key_prefix=CacheKeys.USER_SPRINTS)
    def get_project_sprints(project_id, user_id):
        """Get all sprints for a project with caching."""
        try:
            project = Project.query.get_or_404(project_id)
            user = User.query.get_or_404(user_id)

            if not user.has_project_permission(project_id, 'create_tasks') and project.owner_id != user_id:
                return {'error': 'Insufficient permissions to view sprints'}, 403

            sprints = Sprint.query.filter_by(project_id=project_id).order_by(Sprint.start_date.desc()).all()
            logger.info(f"Fetched {len(sprints)} sprints for project {project_id}")
            return [sprint.to_dict() for sprint in sprints], 200

        except Exception as e:
            logger.error(f"Error fetching sprints for project {project_id}: {str(e)}")
            return {'error': f'Error fetching sprints: {str(e)}'}, 500

    @staticmethod
    def start_sprint(sprint_id, user_id):
        """Start a sprint and notify team members."""
        try:
            sprint = Sprint.query.get_or_404(sprint_id)
            user = User.query.get_or_404(user_id)

            if not user.has_project_permission(sprint.project_id, 'manage_sprints') and sprint.project.owner_id != user_id:
                return {'error': 'Insufficient permissions to start sprint'}, 403

            if sprint.status != SprintStatus.PLANNED:
                return {'error': 'Only planned sprints can be started'}, 400

            active_sprint = sprint.project.get_active_sprint()
            if active_sprint and active_sprint.id != sprint.id:
                return {'error': 'Another sprint is already active for this project'}, 400

            sprint.status = SprintStatus.ACTIVE
            db.session.commit()
            logger.info(f"Sprint {sprint_id} started by user {user_id}")

            # Notify team
            team_members = sprint.project.get_team_members()
            for member in team_members:
                if member.id != user_id:
                    Notification.create_notification(
                        user_id=member.id,
                        notification_type=NotificationType.SPRINT_STARTED,
                        title=f"Sprint Started: {sprint.name}",
                        message=f"{user.name} started sprint '{sprint.name}'",
                        related_user_id=user_id,
                        project_id=sprint.project_id,
                        sprint_id=sprint.id
                    )

            invalidate_project_cache(sprint.project_id)
            return sprint.to_dict(), 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error starting sprint {sprint_id}: {str(e)}")
            return {'error': f'Error starting sprint: {str(e)}'}, 500

    @staticmethod
    def complete_sprint(sprint_id, user_id):
        """Complete a sprint, move incomplete tasks back, notify team."""
        try:
            sprint = Sprint.query.get_or_404(sprint_id)
            user = User.query.get_or_404(user_id)

            if not user.has_project_permission(sprint.project_id, 'manage_sprints') and sprint.project.owner_id != user_id:
                return {'error': 'Insufficient permissions to complete sprint'}, 403

            if sprint.status != SprintStatus.ACTIVE:
                return {'error': 'Only active sprints can be completed'}, 400

            sprint.status = SprintStatus.COMPLETED
            incomplete_tasks = [task for task in sprint.tasks if task.status != TaskStatus.DONE]
            for task in incomplete_tasks:
                task.sprint_id = None
                task.status = TaskStatus.BACKLOG

            db.session.commit()
            logger.info(f"Sprint {sprint_id} completed by user {user_id}, {len(incomplete_tasks)} tasks moved back")

            # Notify team
            team_members = sprint.project.get_team_members()
            for member in team_members:
                if member.id != user_id:
                    Notification.create_notification(
                        user_id=member.id,
                        notification_type=NotificationType.SPRINT_COMPLETED,
                        title=f"Sprint Completed: {sprint.name}",
                        message=f"{user.name} completed sprint '{sprint.name}'. {len(incomplete_tasks)} tasks moved back to backlog.",
                        related_user_id=user_id,
                        project_id=sprint.project_id,
                        sprint_id=sprint.id
                    )

            invalidate_project_cache(sprint.project_id)
            return sprint.to_dict(), 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error completing sprint {sprint_id}: {str(e)}")
            return {'error': f'Error completing sprint: {str(e)}'}, 500

    @staticmethod
    def get_sprint_burndown(sprint_id, user_id):
        """Get burndown chart data with permission check."""
        try:
            sprint = Sprint.query.get_or_404(sprint_id)
            user = User.query.get_or_404(user_id)

            if not user.has_project_permission(sprint.project_id, 'create_tasks') and sprint.project.owner_id != user_id:
                return {'error': 'Insufficient permissions to view sprint data'}, 403

            return sprint.get_burndown_data(), 200

        except Exception as e:
            logger.error(f"Error fetching burndown for sprint {sprint_id}: {str(e)}")
            return {'error': f'Error fetching burndown data: {str(e)}'}, 500

    @staticmethod
    def add_task_to_sprint(sprint_id, task_id, user_id):
        """Add a task to a sprint with status adjustment."""
        try:
            sprint = Sprint.query.get_or_404(sprint_id)
            task = Task.query.get_or_404(task_id)
            user = User.query.get_or_404(user_id)

            if not user.has_project_permission(sprint.project_id, 'edit_tasks') and sprint.project.owner_id != user_id:
                return {'error': 'Insufficient permissions to modify sprint tasks'}, 403

            if task.project_id != sprint.project_id:
                return {'error': 'Task must belong to the same project as the sprint'}, 400

            task.sprint_id = sprint.id
            if task.status == TaskStatus.BACKLOG:
                task.status = TaskStatus.TODO

            db.session.commit()
            logger.info(f"Task {task_id} added to sprint {sprint_id} by user {user_id}")
            invalidate_project_cache(sprint.project_id)
            return task.to_dict(), 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding task {task_id} to sprint {sprint_id}: {str(e)}")
            return {'error': f'Error adding task to sprint: {str(e)}'}, 500

    @staticmethod
    def remove_task_from_sprint(sprint_id, task_id, user_id):
        """Remove a task from a sprint and move to backlog."""
        try:
            sprint = Sprint.query.get_or_404(sprint_id)
            task = Task.query.get_or_404(task_id)
            user = User.query.get_or_404(user_id)

            if not user.has_project_permission(sprint.project_id, 'edit_tasks') and sprint.project.owner_id != user_id:
                return {'error': 'Insufficient permissions to modify sprint tasks'}, 403

            task.sprint_id = None
            task.status = TaskStatus.BACKLOG

            db.session.commit()
            logger.info(f"Task {task_id} removed from sprint {sprint_id} by user {user_id}")
            invalidate_project_cache(sprint.project_id)
            return task.to_dict(), 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error removing task {task_id} from sprint {sprint_id}: {str(e)}")
            return {'error': f'Error removing task from sprint: {str(e)}'}, 500

    @staticmethod
    def _handle_status_change(sprint, old_status, new_status, user_id):
        """Handle sprint status change notifications with logging."""
        try:
            user = User.query.get(user_id)
            team_members = sprint.project.get_team_members()

            status_messages = {
                SprintStatus.ACTIVE: f"{user.name} started sprint '{sprint.name}'",
                SprintStatus.COMPLETED: f"{user.name} completed sprint '{sprint.name}'",
                SprintStatus.CANCELLED: f"{user.name} cancelled sprint '{sprint.name}'"
            }

            message = status_messages.get(new_status, f"{user.name} updated sprint '{sprint.name}' status to {new_status.value}")

            for member in team_members:
                if member.id != user_id:
                    notification_type = NotificationType.SPRINT_STARTED if new_status == SprintStatus.ACTIVE else NotificationType.SPRINT_COMPLETED
                    Notification.create_notification(
                        user_id=member.id,
                        notification_type=notification_type,
                        title=f"Sprint Status Updated: {sprint.name}",
                        message=message,
                        related_user_id=user_id,
                        project_id=sprint.project_id,
                        sprint_id=sprint.id
                    )

            logger.info(f"Sprint {sprint.id} status changed from {old_status} to {new_status} by user {user_id}")

        except Exception as e:
            logger.error(f"Error handling status change for sprint {sprint.id}: {str(e)}")
