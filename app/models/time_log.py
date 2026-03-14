# app/models/time_log.py
from app import db
from datetime import datetime
from app.utils.logger import get_logger

logger = get_logger('time_log')


class TimeLog(db.Model):
    __tablename__ = 'time_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    
    # Time tracking
    hours = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    
    # Date tracking
    work_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    
    # Timestamps
    logged_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    task = db.relationship('Task', back_populates='time_logs')
    user = db.relationship('User', backref='time_logs')

    def to_dict(self):
        """Return a dictionary representation of the time log."""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'hours': self.hours,
            'description': self.description,
            'work_date': self.work_date.isoformat(),
            'logged_at': self.logged_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'task': self.task.to_dict() if self.task else None,
            'user': self.user.to_dict() if self.user else None,
            'hours_formatted': self.get_formatted_hours()
        }

    def get_formatted_hours(self):
        """Return formatted hours as 'Xh Ym'."""
        if not self.hours:
            return "0h"
        
        total_minutes = int(self.hours * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        if hours > 0 and minutes > 0:
            return f"{hours}h {minutes}m"
        elif hours > 0:
            return f"{hours}h"
        else:
            return f"{minutes}m"

    def validate_hours(self):
        """Validate hours to ensure they are within reasonable limits."""
        try:
            if self.hours < 0:
                raise ValueError("Hours cannot be negative")
            if self.hours > 24:
                raise ValueError("Hours cannot exceed 24 per day")
            
            # Check if total daily hours for user exceed 24
            daily_total = TimeLog.get_user_daily_hours(self.user_id, self.work_date)
            if daily_total + self.hours > 24:
                raise ValueError("Total daily hours would exceed 24 hours")
        except ValueError as e:
            logger.error(f"TimeLog validation error for user {self.user_id} on {self.work_date}: {str(e)}")
            raise

    @classmethod
    def get_user_daily_hours(cls, user_id, date):
        """Get total hours logged by a user on a specific date."""
        try:
            logs = cls.query.filter_by(user_id=user_id, work_date=date).all()
            total = sum(log.hours for log in logs)
            logger.info(f"User {user_id} logged {total} hours on {date}")
            return total
        except Exception as e:
            logger.error(f"Error fetching daily hours for user {user_id} on {date}: {str(e)}")
            return 0

    @classmethod
    def get_task_total_hours(cls, task_id):
        """Get total hours logged for a specific task."""
        try:
            logs = cls.query.filter_by(task_id=task_id).all()
            total = sum(log.hours for log in logs)
            logger.info(f"Task {task_id} total logged hours: {total}")
            return total
        except Exception as e:
            logger.error(f"Error fetching total hours for task {task_id}: {str(e)}")
            return 0

    @classmethod
    def get_user_weekly_hours(cls, user_id, start_date, end_date):
        """Get total hours logged by a user in a date range."""
        try:
            logs = cls.query.filter(
                cls.user_id == user_id,
                cls.work_date >= start_date,
                cls.work_date <= end_date
            ).all()
            total = sum(log.hours for log in logs)
            logger.info(f"User {user_id} total hours from {start_date} to {end_date}: {total}")
            return total
        except Exception as e:
            logger.error(f"Error fetching weekly hours for user {user_id}: {str(e)}")
            return 0
