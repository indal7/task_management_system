# app/models/activity_log.py
from app import db
from datetime import datetime


class ActivityLog(db.Model):
    __tablename__ = 'activity_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)

    # What entity was affected
    entity_type = db.Column(db.String(50), nullable=False)  # 'task', 'project', 'sprint', etc.
    entity_id = db.Column(db.Integer, nullable=False)

    # What happened
    action = db.Column(db.String(100), nullable=False)  # 'created', 'updated', 'deleted', etc.
    details = db.Column(db.Text)  # JSON string with change details

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='activity_logs', foreign_keys=[user_id])

    def to_dict(self):
        import json
        details_data = None
        if self.details:
            try:
                details_data = json.loads(self.details)
            except (json.JSONDecodeError, TypeError):
                details_data = self.details

        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': {'id': self.user.id, 'name': self.user.name, 'email': self.user.email} if self.user else None,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'action': self.action,
            'details': details_data,
            'created_at': self.created_at.isoformat(),
        }
