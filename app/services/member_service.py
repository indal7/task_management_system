# app/services/member_service.py
from app.models.project_member import ProjectMember
from app.models.project import Project
from app.models.user import User
from app import db
from app.utils.logger import get_logger
from app.utils.cache_utils import cache

logger = get_logger('member_service')


class ProjectMemberService:

    @staticmethod
    def get_members(project_id):
        """Get all members of a project."""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}, 404

            members = ProjectMember.query.filter_by(project_id=project_id).all()
            data = []
            for m in members:
                member_dict = m.to_dict()
                # Remove recursive project nesting
                member_dict.pop('project', None)
                data.append(member_dict)

            return {
                'project_id': project_id,
                'members': data,
                'total': len(data),
            }, 200

        except Exception as e:
            logger.error(f"Error fetching members for project {project_id}: {e}")
            return {'error': f'Error fetching members: {str(e)}'}, 500

    @staticmethod
    def add_member(project_id, user_id, role=None, permissions=None,
                   requesting_user_id=None):
        """Add a user to a project."""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}, 404

            user = User.query.get(user_id)
            if not user:
                return {'error': 'User not found'}, 404

            # Check if already a member
            existing = ProjectMember.query.filter_by(
                project_id=project_id, user_id=user_id
            ).first()
            if existing:
                return {'error': 'User is already a member of this project'}, 409

            perms = permissions or {}
            member = ProjectMember(
                project_id=project_id,
                user_id=user_id,
                role=role,
                can_create_tasks=perms.get('can_create_tasks', True),
                can_edit_tasks=perms.get('can_edit_tasks', True),
                can_delete_tasks=perms.get('can_delete_tasks', False),
                can_manage_sprints=perms.get('can_manage_sprints', False),
                can_manage_members=perms.get('can_manage_members', False),
            )

            db.session.add(member)
            db.session.commit()

            # Invalidate project cache
            cache.delete(f"projects:{project_id}")
            cache.delete("projects:all")

            logger.info(
                f"User {user_id} added to project {project_id} "
                f"by {requesting_user_id}"
            )

            result = member.to_dict()
            result.pop('project', None)
            return result, 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding member to project {project_id}: {e}")
            return {'error': f'Error adding member: {str(e)}'}, 500

    @staticmethod
    def update_member(project_id, user_id, data, requesting_user_id=None):
        """Update a project member's role or permissions."""
        try:
            member = ProjectMember.query.filter_by(
                project_id=project_id, user_id=user_id
            ).first()
            if not member:
                return {'error': 'Member not found'}, 404

            if 'role' in data:
                member.role = data['role']

            permission_fields = [
                'can_create_tasks', 'can_edit_tasks', 'can_delete_tasks',
                'can_manage_sprints', 'can_manage_members',
            ]
            for field in permission_fields:
                if field in data:
                    setattr(member, field, bool(data[field]))

            db.session.commit()
            cache.delete(f"projects:{project_id}")

            logger.info(
                f"Member {user_id} in project {project_id} updated "
                f"by {requesting_user_id}"
            )

            result = member.to_dict()
            result.pop('project', None)
            return result, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating member in project {project_id}: {e}")
            return {'error': f'Error updating member: {str(e)}'}, 500

    @staticmethod
    def remove_member(project_id, user_id, requesting_user_id=None):
        """Remove a user from a project."""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}, 404

            # Cannot remove the project owner
            if project.owner_id == user_id:
                return {'error': 'Cannot remove the project owner'}, 400

            member = ProjectMember.query.filter_by(
                project_id=project_id, user_id=user_id
            ).first()
            if not member:
                return {'error': 'Member not found'}, 404

            db.session.delete(member)
            db.session.commit()

            cache.delete(f"projects:{project_id}")
            cache.delete("projects:all")

            logger.info(
                f"User {user_id} removed from project {project_id} "
                f"by {requesting_user_id}"
            )
            return {'message': 'Member removed successfully'}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error removing member from project {project_id}: {e}")
            return {'error': f'Error removing member: {str(e)}'}, 500

    @staticmethod
    def bulk_add_members(project_id, members_data, requesting_user_id=None):
        """Add multiple members to a project at once."""
        try:
            project = Project.query.get(project_id)
            if not project:
                return {'error': 'Project not found'}, 404

            added = []
            errors = []

            for item in members_data:
                uid = item.get('user_id')
                if not uid:
                    errors.append({'item': item, 'error': 'user_id is required'})
                    continue

                user = User.query.get(uid)
                if not user:
                    errors.append({'user_id': uid, 'error': 'User not found'})
                    continue

                existing = ProjectMember.query.filter_by(
                    project_id=project_id, user_id=uid
                ).first()
                if existing:
                    errors.append({'user_id': uid, 'error': 'Already a member'})
                    continue

                perms = item.get('permissions', {})
                member = ProjectMember(
                    project_id=project_id,
                    user_id=uid,
                    role=item.get('role'),
                    can_create_tasks=perms.get('can_create_tasks', True),
                    can_edit_tasks=perms.get('can_edit_tasks', True),
                    can_delete_tasks=perms.get('can_delete_tasks', False),
                    can_manage_sprints=perms.get('can_manage_sprints', False),
                    can_manage_members=perms.get('can_manage_members', False),
                )
                db.session.add(member)
                added.append(uid)

            db.session.commit()
            cache.delete(f"projects:{project_id}")
            cache.delete("projects:all")

            logger.info(
                f"Bulk added {len(added)} members to project {project_id}"
            )
            return {'added': added, 'errors': errors}, 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Bulk add members error for project {project_id}: {e}")
            return {'error': f'Bulk add error: {str(e)}'}, 500
