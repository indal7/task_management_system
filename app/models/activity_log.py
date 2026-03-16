# app/models/activity_log.py
from app import db
from datetime import datetime


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)

    # Who performed the action
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='SET NULL'), nullable=True)

    # What was acted upon
    entity_type = db.Column(db.String(50), nullable=False)   # 'task', 'project', 'sprint', etc.
    entity_id = db.Column(db.Integer, nullable=False)

    # What action was taken
    action = db.Column(db.String(100), nullable=False)        # 'created', 'updated', 'deleted', etc.
    field_name = db.Column(db.String(100))                    # Which field changed (for updates)
    old_value = db.Column(db.Text)                            # Previous value (JSON serialized)
    new_value = db.Column(db.Text)                            # New value (JSON serialized)

    # Human-readable description
    description = db.Column(db.Text)

    # Context
    ip_address = db.Column(db.String(45))

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref='activity_logs')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'action': self.action,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'description': self.description,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
        }

    @classmethod
    def log(cls, user_id, entity_type, entity_id, action,
            description=None, field_name=None, old_value=None,
            new_value=None, ip_address=None):
        """Convenience method to create and persist an activity log entry."""
        entry = cls(
            user_id=user_id,
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            description=description,
            field_name=field_name,
            old_value=str(old_value) if old_value is not None else None,
            new_value=str(new_value) if new_value is not None else None,
            ip_address=ip_address,
        )
        db.session.add(entry)
        # Flush so the entry is persisted alongside the main transaction
        db.session.flush()
        return entry
