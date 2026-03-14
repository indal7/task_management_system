# app/models/notification.py
from app import db
from datetime import datetime
from .enums import NotificationType

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=True)
    
    # Notification details
    type = db.Column(db.Enum(NotificationType), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Additional context
    related_user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=True)  # User who triggered the notification
    project_id = db.Column(db.Integer, db.ForeignKey('project.id', ondelete='CASCADE'), nullable=True)
    sprint_id = db.Column(db.Integer, db.ForeignKey('sprint.id', ondelete='CASCADE'), nullable=True)
    
    # Status
    read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', back_populates='notifications', foreign_keys=[user_id])
    task = db.relationship('Task', back_populates='notifications')
    related_user = db.relationship('User', foreign_keys=[related_user_id])
    project = db.relationship('Project')
    sprint = db.relationship('Sprint')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'task_id': self.task_id,
            'type': self.type.value,
            'title': self.title,
            'message': self.message,
            'related_user_id': self.related_user_id,
            'project_id': self.project_id,
            'sprint_id': self.sprint_id,
            'read': self.read,
            'read_at': self.read_at.isoformat() if self.read_at else None,
            'created_at': self.created_at.isoformat(),
            'task': self.task.to_dict() if self.task else None,
            'related_user': self.related_user.to_dict() if self.related_user else None,
            'project': self.project.to_dict() if self.project else None,
            'sprint': self.sprint.to_dict() if self.sprint else None
        }

    def mark_as_read(self):
        """Mark notification as read."""
        if not self.read:
            self.read = True
            self.read_at = datetime.utcnow()
            db.session.commit()

    def mark_as_unread(self):
        """Mark notification as unread."""
        if self.read:
            self.read = False
            self.read_at = None
            db.session.commit()

    @classmethod
    def create_notification(cls, user_id, notification_type, title, message, 
                          task_id=None, related_user_id=None, project_id=None, sprint_id=None):
        """Create a new notification."""
        notification = cls(
            user_id=user_id,
            task_id=task_id,
            type=notification_type,
            title=title,
            message=message,
            related_user_id=related_user_id,
            project_id=project_id,
            sprint_id=sprint_id
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @classmethod
    def get_unread_count(cls, user_id):
        """Get count of unread notifications for a user."""
        return cls.query.filter_by(user_id=user_id, read=False).count()

    @classmethod
    def mark_all_as_read(cls, user_id):
        """Mark all notifications as read for a user."""
        notifications = cls.query.filter_by(user_id=user_id, read=False).all()
        for notification in notifications:
            notification.read = True
            notification.read_at = datetime.utcnow()
        db.session.commit()
        return len(notifications)

    @classmethod
    def cleanup_old_notifications(cls, days=30):
        """Delete notifications older than specified days."""
        cutoff_date = datetime.utcnow() - datetime.timedelta(days=days)
        old_notifications = cls.query.filter(cls.created_at < cutoff_date).all()
        count = len(old_notifications)
        
        for notification in old_notifications:
            db.session.delete(notification)
        
        db.session.commit()
        return count
