# app/models/task.py
from app import db
from datetime import datetime
from .enums import TaskStatus, TaskPriority, TaskType, EstimationUnit
from app.utils.logger import get_logger

logger = get_logger('task')


class Task(db.Model):
    __tablename__ = 'task'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    status = db.Column(db.Enum(TaskStatus), nullable=False, default=TaskStatus.BACKLOG)
    priority = db.Column(db.Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    task_type = db.Column(db.Enum(TaskType), nullable=False, default=TaskType.FEATURE)
    
    # User relationships
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    
    # Project and Sprint relationships
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'), nullable=True)
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprint.id', ondelete='SET NULL'), nullable=True)
    
    # Time tracking
    due_date = db.Column(db.DateTime)
    start_date = db.Column(db.DateTime)
    completion_date = db.Column(db.DateTime)
    
    # Estimation and tracking
    estimated_hours = db.Column(db.Float)
    actual_hours = db.Column(db.Float, default=0)
    story_points = db.Column(db.Integer)
    estimation_unit = db.Column(db.Enum(EstimationUnit), default=EstimationUnit.HOURS)
    
    # Additional fields
    labels = db.Column(db.Text)  # JSON string of labels
    acceptance_criteria = db.Column(db.Text)
    
    # Dependencies
    parent_task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='SET NULL'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    assignee = db.relationship('User', foreign_keys=[assigned_to_id], back_populates='assigned_tasks')
    creator = db.relationship('User', foreign_keys=[created_by_id], back_populates='created_tasks')
    project = db.relationship('Project', back_populates='tasks')
    sprint = db.relationship('Sprint', back_populates='tasks')
    
    # Self-referential relationship for parent/child tasks
    parent_task = db.relationship('Task', remote_side=[id], backref='subtasks')
    
    # Child relationships
    comments = db.relationship('TaskComment', back_populates='task', cascade='all, delete-orphan')
    notifications = db.relationship('Notification', back_populates='task', cascade='all, delete-orphan')
    attachments = db.relationship('TaskAttachment', back_populates='task', cascade='all, delete-orphan')
    time_logs = db.relationship('TimeLog', back_populates='task', cascade='all, delete-orphan')

    def to_dict(self, include_subtasks=False):
        import json
        
        # Parse labels from JSON string
        labels_list = []
        if self.labels:
            try:
                labels_list = json.loads(self.labels)
            except json.JSONDecodeError:
                labels_list = []

        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'status': self.status.value,
            'priority': self.priority.value,
            'task_type': self.task_type.value,
            'assigned_to': self.assignee.to_dict() if self.assignee else None,
            'created_by': self.creator.to_dict() if self.creator else None,
            'project': self.project.to_dict() if self.project else None,
            'sprint': self.sprint.to_dict() if self.sprint else None,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'estimated_hours': self.estimated_hours,
            'actual_hours': self.actual_hours,
            'story_points': self.story_points,
            'estimation_unit': self.estimation_unit.value if self.estimation_unit else None,
            'labels': labels_list,
            'acceptance_criteria': self.acceptance_criteria,
            'parent_task_id': self.parent_task_id,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'comments_count': len(self.comments),
            'attachments_count': len(self.attachments),
            'time_logs_count': len(self.time_logs)
        }
        
        if include_subtasks:
            result['subtasks'] = [subtask.to_dict() for subtask in self.subtasks]
            
        return result

    def get_progress_percentage(self):
        """Calculate task progress based on subtasks or time logged."""
        try:
            if self.subtasks:
                completed_subtasks = sum(1 for subtask in self.subtasks if subtask.status == TaskStatus.DONE)
                progress = (completed_subtasks / len(self.subtasks)) * 100
            elif self.estimated_hours and self.actual_hours:
                progress = min((self.actual_hours / self.estimated_hours) * 100, 100)
            else:
                progress = 0 if self.status != TaskStatus.DONE else 100
            return round(progress, 2)
        except Exception as e:
            logger.error(f"Error calculating progress for task {self.id}: {str(e)}")
            return 0

    def is_overdue(self):
        """Check if task is overdue."""
        if not self.due_date:
            return False
        return datetime.utcnow() > self.due_date and self.status not in [TaskStatus.DONE, TaskStatus.CANCELLED]

    def get_time_spent(self):
        """Get total time spent on this task from time logs."""
        try:
            return sum(log.hours for log in self.time_logs)
        except Exception as e:
            logger.error(f"Error calculating time spent for task {self.id}: {str(e)}")
            return 0

    def add_label(self, label):
        """Add a label to the task."""
        import json
        try:
            labels = json.loads(self.labels) if self.labels else []
            if label not in labels:
                labels.append(label)
                self.labels = json.dumps(labels)
        except Exception as e:
            logger.error(f"Error adding label '{label}' to task {self.id}: {str(e)}")

    def remove_label(self, label):
        """Remove a label from the task."""
        import json
        try:
            labels = json.loads(self.labels) if self.labels else []
            if label in labels:
                labels.remove(label)
                self.labels = json.dumps(labels)
        except Exception as e:
            logger.error(f"Error removing label '{label}' from task {self.id}: {str(e)}")
