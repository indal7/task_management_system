# app/services/project_service.py
from app.models.project import Project
from app.models.user import User
from app import db
from datetime import datetime
from app.utils.cache_utils import cache, cached_per_user, CacheKeys, invalidate_user_cache, invalidate_project_cache
from app.utils.logger import get_logger, log_db_query

logger = get_logger('projects')


class ProjectService:

    @staticmethod
    def create_project(data, user_id):
        """Creates a new project."""
        try:
            owner = User.query.get_or_404(user_id)

            project = Project(
                name=data.get('name'),
                description=data.get('description'),
                owner_id=owner.id,
                status=data.get('status', 'active')
            )

            db.session.add(project)
            db.session.commit()
            log_db_query("INSERT", "projects")
            logger.info(f"Project {project.id} created by user {user_id}")

            # Invalidate user's project cache
            invalidate_user_cache(user_id)

            return project.to_dict()

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating project by user {user_id}: {str(e)}")
            return {'error': f'Error creating project: {str(e)}'}, 500

    @staticmethod
    @cached_per_user(timeout=300, key_prefix=CacheKeys.USER_PROJECTS)
    def get_all_projects():
        """Gets all projects."""
        try:
            projects = Project.query.all()
            logger.info(f"Fetched all projects: {len(projects)}")
            return [project.to_dict() for project in projects]
        except Exception as e:
            logger.error(f"Error fetching all projects: {str(e)}")
            return {'error': f'Error fetching projects: {str(e)}'}, 500

    @staticmethod
    @cached_per_user(timeout=300, key_prefix=CacheKeys.USER_PROJECTS)
    def get_project_by_id(project_id):
        """Gets a specific project by ID."""
        try:
            project = Project.query.get_or_404(project_id)
            logger.info(f"Fetched project {project_id}")
            return project.to_dict()
        except Exception as e:
            logger.error(f"Error fetching project {project_id}: {str(e)}")
            return {'error': f'Error fetching project: {str(e)}'}, 404

    @staticmethod
    def update_project(project_id, data):
        """Updates an existing project."""
        try:
            project = Project.query.get_or_404(project_id)

            for field in ['name', 'description', 'status']:
                if field in data:
                    setattr(project, field, data[field])

            db.session.commit()
            log_db_query("UPDATE", "projects")
            logger.info(f"Project {project_id} updated")

            # Invalidate project cache
            invalidate_project_cache(project_id)

            return project.to_dict()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating project {project_id}: {str(e)}")
            return {'error': f'Error updating project: {str(e)}'}, 500

    @staticmethod
    def delete_project(project_id):
        """Deletes a project."""
        try:
            project = Project.query.get_or_404(project_id)
            db.session.delete(project)
            db.session.commit()
            log_db_query("DELETE", "projects")
            logger.info(f"Project {project_id} deleted")

            # Invalidate project cache
            invalidate_project_cache(project_id)

            return {'message': 'Project deleted successfully'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting project {project_id}: {str(e)}")
            return {'error': f'Error deleting project: {str(e)}'}, 500

    @staticmethod
    @cached_per_user(timeout=300, key_prefix=CacheKeys.USER_PROJECTS)
    def get_recent_projects():
        """Gets the most recently updated projects."""
        try:
            projects = Project.query.order_by(Project.updated_at.desc()).limit(5).all()
            logger.info(f"Fetched {len(projects)} recent projects")
            return [project.to_dict() for project in projects]
        except Exception as e:
            logger.error(f"Error fetching recent projects: {str(e)}")
            return {'error': f'Error fetching recent projects: {str(e)}'}, 500

    @staticmethod
    def get_project_stats(project_id):
        """Gets statistics for a project."""
        try:
            from app.models.task import Task
            from app.models.enums import TaskStatus
            from app.models.time_log import TimeLog
            from sqlalchemy import func

            project = Project.query.get_or_404(project_id)
            tasks = project.tasks
            now = datetime.utcnow()

            total_tasks = len(tasks)
            completed_tasks = sum(1 for t in tasks if t.status == TaskStatus.DONE)
            in_progress_tasks = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
            overdue_tasks = sum(
                1 for t in tasks
                if t.due_date and t.due_date < now and t.status != TaskStatus.DONE
            )
            completion_percentage = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0

            total_hours = db.session.query(func.sum(TimeLog.hours)).join(Task).filter(
                Task.project_id == project_id
            ).scalar() or 0

            active_sprint = project.get_active_sprint()

            logger.info(f"Project stats fetched for project {project_id}")
            return {
                'project_id': project.id,
                'project_name': project.name,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'in_progress_tasks': in_progress_tasks,
                'overdue_tasks': overdue_tasks,
                'completion_percentage': completion_percentage,
                'total_sprints': len(project.sprints),
                'active_sprint_id': active_sprint.id if active_sprint else None,
                'active_sprint_name': active_sprint.name if active_sprint else None,
                'team_members_count': len(project.team_members),
                'total_hours_logged': float(total_hours),
                'estimated_hours': project.estimated_hours or 0
            }
        except Exception as e:
            logger.error(f"Error fetching project stats {project_id}: {str(e)}")
            return {'error': f'Error fetching project stats: {str(e)}'}, 500

    @staticmethod
    def get_project_progress(project_id):
        """Gets progress timeline for a project."""
        try:
            from app.models.task import Task
            from app.models.enums import TaskStatus

            project = Project.query.get_or_404(project_id)
            tasks = project.tasks
            total_tasks = len(tasks)
            completed_tasks = sum(1 for t in tasks if t.status == TaskStatus.DONE)
            completion_percentage = round((completed_tasks / total_tasks * 100), 2) if total_tasks > 0 else 0

            # Sprint progress
            sprint_progress = []
            for sprint in project.sprints:
                sprint_tasks = sprint.tasks
                sprint_total = len(sprint_tasks)
                sprint_done = sum(1 for t in sprint_tasks if t.status == TaskStatus.DONE)
                sprint_progress.append({
                    'sprint_id': sprint.id,
                    'sprint_name': sprint.name,
                    'status': sprint.status.value,
                    'total_tasks': sprint_total,
                    'completed_tasks': sprint_done,
                    'completion_percentage': round((sprint_done / sprint_total * 100), 2) if sprint_total > 0 else 0
                })

            logger.info(f"Project progress fetched for project {project_id}")
            return {
                'project_id': project.id,
                'project_name': project.name,
                'overall_completion': completion_percentage,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'sprint_progress': sprint_progress
            }
        except Exception as e:
            logger.error(f"Error fetching project progress {project_id}: {str(e)}")
            return {'error': f'Error fetching project progress: {str(e)}'}, 500
