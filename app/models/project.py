# app/models/project.py
from app import db
from datetime import datetime

from app.models.project_member import ProjectMember
from .enums import ProjectStatus

class Project(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum(ProjectStatus), nullable=False, default=ProjectStatus.PLANNING)
    
    # Project details
    repository_url = db.Column(db.String(500))
    documentation_url = db.Column(db.String(500))
    technology_stack = db.Column(db.Text)  # JSON string of technologies
    
    # Time tracking
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    estimated_hours = db.Column(db.Float)
    
    # Ownership
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    
    # Client information
    client_name = db.Column(db.String(200))
    client_email = db.Column(db.String(120))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = db.relationship('User', back_populates='owned_projects')
    tasks = db.relationship('Task', back_populates='project', cascade='all, delete-orphan')
    sprints = db.relationship('Sprint', back_populates='project', cascade='all, delete-orphan')
    team_members = db.relationship('ProjectMember', back_populates='project', cascade='all, delete-orphan')

    def to_dict(self, include_tasks=False, include_sprints=False):
        import json
        
        # Parse technology stack from JSON string
        tech_stack = []
        if self.technology_stack:
            try:
                tech_stack = json.loads(self.technology_stack)
            except json.JSONDecodeError:
                tech_stack = []

        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'repository_url': self.repository_url,
            'documentation_url': self.documentation_url,
            'technology_stack': tech_stack,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'estimated_hours': self.estimated_hours,
            'client_name': self.client_name,
            'client_email': self.client_email,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'owner': self.owner.to_dict() if self.owner else None,
            'tasks_count': len(self.tasks),
            'sprints_count': len(self.sprints),
            'team_members_count': len(self.team_members)
        }
        
        if include_tasks:
            result['tasks'] = [task.to_dict() for task in self.tasks]
            
        if include_sprints:
            result['sprints'] = [sprint.to_dict() for sprint in self.sprints]
            
        return result

    def get_completion_percentage(self):
        """Calculate project completion based on tasks."""
        if not self.tasks:
            return 0
        
        completed_tasks = sum(1 for task in self.tasks if task.status.value == 'DONE')
        return (completed_tasks / len(self.tasks)) * 100

    def get_team_members(self):
        """Get all team members for this project."""
        return [member.user for member in self.team_members]

    def add_team_member(self, user_id, role=None):
        """Add a team member to the project."""
        existing_member = ProjectMember.query.filter_by(
            project_id=self.id, 
            user_id=user_id
        ).first()
        
        if not existing_member:
            member = ProjectMember(
                project_id=self.id,
                user_id=user_id,
                role=role
            )
            db.session.add(member)
            db.session.commit()

    def remove_team_member(self, user_id):
        """Remove a team member from the project."""
        member = ProjectMember.query.filter_by(
            project_id=self.id, 
            user_id=user_id
        ).first()
        
        if member:
            db.session.delete(member)
            db.session.commit()

    def get_active_sprint(self):
        """Get the currently active sprint for this project."""
        from .sprint import Sprint
        from .enums import SprintStatus
        return Sprint.query.filter_by(
            project_id=self.id, 
            status=SprintStatus.ACTIVE
        ).first()

    def add_technology(self, technology):
        """Add a technology to the project stack."""
        import json
        tech_stack = []
        if self.technology_stack:
            try:
                tech_stack = json.loads(self.technology_stack)
            except json.JSONDecodeError:
                tech_stack = []
        
        if technology not in tech_stack:
            tech_stack.append(technology)
            self.technology_stack = json.dumps(tech_stack)

    def remove_technology(self, technology):
        """Remove a technology from the project stack."""
        import json
        tech_stack = []
        if self.technology_stack:
            try:
                tech_stack = json.loads(self.technology_stack)
            except json.JSONDecodeError:
                return
        
        if technology in tech_stack:
            tech_stack.remove(technology)
            self.technology_stack = json.dumps(tech_stack)
