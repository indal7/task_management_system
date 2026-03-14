# app/models/project_member.py
from app import db
from datetime import datetime

class ProjectMember(db.Model):
    __tablename__ = 'project_members'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(100))  # Role in this specific project
    
    # Permissions
    can_create_tasks = db.Column(db.Boolean, default=True)
    can_edit_tasks = db.Column(db.Boolean, default=True)
    can_delete_tasks = db.Column(db.Boolean, default=False)
    can_manage_sprints = db.Column(db.Boolean, default=False)
    can_manage_members = db.Column(db.Boolean, default=False)
    
    # Timestamps
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', back_populates='team_members')
    user = db.relationship('User', back_populates='project_memberships')

    # Unique constraint to prevent duplicate memberships
    __table_args__ = (db.UniqueConstraint('project_id', 'user_id', name='unique_project_member'),)

    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'role': self.role,
            'can_create_tasks': self.can_create_tasks,
            'can_edit_tasks': self.can_edit_tasks,
            'can_delete_tasks': self.can_delete_tasks,
            'can_manage_sprints': self.can_manage_sprints,
            'can_manage_members': self.can_manage_members,
            'joined_at': self.joined_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'project': self.project.to_dict() if self.project else None,
            'user': self.user.to_dict() if self.user else None
        }

    def has_permission(self, permission):
        """Check if user has specific permission."""
        permission_map = {
            'create_tasks': self.can_create_tasks,
            'edit_tasks': self.can_edit_tasks,
            'delete_tasks': self.can_delete_tasks,
            'manage_sprints': self.can_manage_sprints,
            'manage_members': self.can_manage_members
        }
        return permission_map.get(permission, False)

    def update_permissions(self, permissions):
        """Update user permissions for this project."""
        for permission, value in permissions.items():
            if hasattr(self, f'can_{permission}'):
                setattr(self, f'can_{permission}', value)
        
        db.session.commit()