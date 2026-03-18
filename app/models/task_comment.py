# app/models/task_comment.py
from app import db
from datetime import datetime
from app.utils.timezone_utils import ist_isoformat

class TaskComment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    comment = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task = db.relationship('Task', back_populates='comments')
    user = db.relationship('User', back_populates='task_comments')

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'comment': self.comment,
            'created_at': ist_isoformat(self.created_at),
            'updated_at': ist_isoformat(self.updated_at),
            'user': self.user.to_dict() if self.user else None
        }
