# app/services/member_service.py
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.models.enums import UserRole
from app import db
from app.utils.logger import get_logger

logger = get_logger('members')


class MemberService:

    @staticmethod
    def get_members(project_id):
        """Get all members of a project."""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}, 404

            members = ProjectMember.query.filter_by(project_id=project_id).all()
            return [m.to_dict() for m in members], 200

        except Exception as e:
            logger.error(f'Error getting members for project {project_id}: {str(e)}')
            return {'error': f'Error fetching members: {str(e)}'}, 500

    @staticmethod
    def add_member(project_id, user_id, role=None, permissions=None, requesting_user_id=None):
        """Add a member to a project."""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}, 404

            # Only project owner or admin can add members
            requesting_user = User.query.get(requesting_user_id) if requesting_user_id else None
            is_owner = int(project.owner_id) == int(requesting_user_id) if requesting_user_id else False
            is_admin = requesting_user and requesting_user.role == UserRole.ADMIN
            if not (is_owner or is_admin):
                # Check if requesting user has manage_members permission
                existing_req_member = ProjectMember.query.filter_by(
                    project_id=project_id, user_id=requesting_user_id
                ).first()
                if not existing_req_member or not existing_req_member.can_manage_members:
                    return {'error': 'Permission denied'}, 403

            # Check if user exists
            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}, 404

            # Check if already a member
            existing = ProjectMember.query.filter_by(
                project_id=project_id, user_id=user_id
            ).first()
            if existing:
                return {'error': 'User is already a member of this project'}, 409

            member = ProjectMember(
                project_id=project_id,
                user_id=user_id,
                role=role,
            )
            if permissions:
                for perm, val in permissions.items():
                    if hasattr(member, f'can_{perm}'):
                        setattr(member, f'can_{perm}', val)

            db.session.add(member)
            db.session.commit()
            logger.info(f'User {user_id} added to project {project_id}')
            return member.to_dict(), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error adding member to project {project_id}: {str(e)}')
            return {'error': f'Error adding member: {str(e)}'}, 500

    @staticmethod
    def remove_member(project_id, user_id, requesting_user_id):
        """Remove a member from a project."""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}, 404

            if project.owner_id == user_id:
                return {'error': 'Cannot remove project owner'}, 400

            requesting_user = User.query.get(requesting_user_id)
            is_owner = int(project.owner_id) == int(requesting_user_id)
            is_admin = requesting_user and requesting_user.role == UserRole.ADMIN
            if not (is_owner or is_admin):
                existing_req_member = ProjectMember.query.filter_by(
                    project_id=project_id, user_id=requesting_user_id
                ).first()
                if not existing_req_member or not existing_req_member.can_manage_members:
                    return {'error': 'Permission denied'}, 403

            member = ProjectMember.query.filter_by(
                project_id=project_id, user_id=user_id
            ).first()
            if not member:
                return {'error': 'User is not a member of this project'}, 404

            db.session.delete(member)
            db.session.commit()
            logger.info(f'User {user_id} removed from project {project_id}')
            return {'message': 'Member removed successfully'}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error removing member from project {project_id}: {str(e)}')
            return {'error': f'Error removing member: {str(e)}'}, 500

    @staticmethod
    def update_member(project_id, user_id, data, requesting_user_id):
        """Update a member's role and/or permissions."""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}, 404

            requesting_user = User.query.get(requesting_user_id)
            is_owner = int(project.owner_id) == int(requesting_user_id)
            is_admin = requesting_user and requesting_user.role == UserRole.ADMIN
            if not (is_owner or is_admin):
                existing_req_member = ProjectMember.query.filter_by(
                    project_id=project_id, user_id=requesting_user_id
                ).first()
                if not existing_req_member or not existing_req_member.can_manage_members:
                    return {'error': 'Permission denied'}, 403

            member = ProjectMember.query.filter_by(
                project_id=project_id, user_id=user_id
            ).first()
            if not member:
                return {'error': 'User is not a member of this project'}, 404

            if 'role' in data:
                member.role = data['role']

            permission_fields = [
                'can_create_tasks', 'can_edit_tasks', 'can_delete_tasks',
                'can_manage_sprints', 'can_manage_members'
            ]
            for field in permission_fields:
                if field in data:
                    setattr(member, field, data[field])

            db.session.commit()
            logger.info(f'Member {user_id} updated in project {project_id}')
            return member.to_dict(), 200

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error updating member in project {project_id}: {str(e)}')
            return {'error': f'Error updating member: {str(e)}'}, 500
