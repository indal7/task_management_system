# app/models/task_workflow_history.py
from datetime import datetime

from app import db
from app.utils.timezone_utils import ist_isoformat


class TaskWorkflowHistory(db.Model):
    __tablename__ = 'task_workflow_history'

    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False, index=True)

    from_status = db.Column(db.String(50), nullable=True)
    to_status = db.Column(db.String(50), nullable=True)

    from_stage = db.Column(db.String(100), nullable=True)
    to_stage = db.Column(db.String(100), nullable=True)

    from_sprint_id = db.Column(db.Integer, db.ForeignKey('sprint.id', ondelete='SET NULL'), nullable=True)
    to_sprint_id = db.Column(db.Integer, db.ForeignKey('sprint.id', ondelete='SET NULL'), nullable=True)

    from_assignee_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)
    to_assignee_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)

    changed_by_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True, index=True)
    change_reason = db.Column(db.String(255), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    task = db.relationship('Task', backref=db.backref('workflow_history', lazy='dynamic', cascade='all, delete-orphan'))
    changed_by = db.relationship('User', foreign_keys=[changed_by_id])

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'from_status': self.from_status,
            'to_status': self.to_status,
            'from_stage': self.from_stage,
            'to_stage': self.to_stage,
            'from_sprint_id': self.from_sprint_id,
            'to_sprint_id': self.to_sprint_id,
            'from_assignee_id': self.from_assignee_id,
            'to_assignee_id': self.to_assignee_id,
            'changed_by_id': self.changed_by_id,
            'change_reason': self.change_reason,
            'created_at': ist_isoformat(self.created_at),
            'changed_by': self.changed_by.to_dict() if self.changed_by else None,
        }
