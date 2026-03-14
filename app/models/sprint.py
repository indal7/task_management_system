# app/models/sprint.py
from app import db
from datetime import datetime
from .enums import SprintStatus

class Sprint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.Enum(SprintStatus), nullable=False, default=SprintStatus.PLANNED)
    
    # Project relationship
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'), nullable=False)
    
    # Sprint duration
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    
    # Sprint goals and metrics
    goal = db.Column(db.Text)
    capacity_hours = db.Column(db.Float)
    velocity_points = db.Column(db.Integer)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = db.relationship('Project', back_populates='sprints')
    tasks = db.relationship('Task', back_populates='sprint')

    def to_dict(self, include_tasks=False):
        result = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status.value,
            'project_id': self.project_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'goal': self.goal,
            'capacity_hours': self.capacity_hours,
            'velocity_points': self.velocity_points,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'project': self.project.to_dict() if self.project else None,
            'tasks_count': len(self.tasks)
        }
        
        if include_tasks:
            result['tasks'] = [task.to_dict() for task in self.tasks]
            
        return result

    def get_completion_percentage(self):
        """Calculate sprint completion based on tasks."""
        if not self.tasks:
            return 0
        
        completed_tasks = sum(1 for task in self.tasks if task.status.value == 'DONE')
        return (completed_tasks / len(self.tasks)) * 100

    def get_total_story_points(self):
        """Get total story points for this sprint."""
        return sum(task.story_points or 0 for task in self.tasks)

    def get_completed_story_points(self):
        """Get completed story points for this sprint."""
        return sum(task.story_points or 0 for task in self.tasks if task.status.value == 'DONE')

    def get_burndown_data(self):
        """Get burndown chart data for this sprint."""
        # This would typically involve daily snapshots of remaining work
        # For now, we'll return a simple calculation
        total_points = self.get_total_story_points()
        completed_points = self.get_completed_story_points()
        remaining_points = total_points - completed_points
        
        return {
            'total_points': total_points,
            'completed_points': completed_points,
            'remaining_points': remaining_points,
            'completion_percentage': self.get_completion_percentage()
        }

    def is_active(self):
        """Check if sprint is currently active."""
        now = datetime.utcnow()
        return (self.status == SprintStatus.ACTIVE and 
                self.start_date <= now <= self.end_date)

    def days_remaining(self):
        """Get number of days remaining in sprint."""
        if self.status != SprintStatus.ACTIVE:
            return 0
        
        now = datetime.utcnow()
        if now > self.end_date:
            return 0
        
        return (self.end_date - now).days