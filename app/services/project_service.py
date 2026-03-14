# app/services/project_service.py
from app.models.project import Project
from app.models.user import User
from app import db
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
