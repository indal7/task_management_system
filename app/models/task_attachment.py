# app/models/task_attachment.py
from app import db
from datetime import datetime
import os

class TaskAttachment(db.Model):
    __tablename__ = 'task_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('task.id', ondelete='CASCADE'), nullable=False)
    uploaded_by_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    
    # File information
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)  # Size in bytes
    mime_type = db.Column(db.String(100))
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    task = db.relationship('Task', back_populates='attachments')
    uploaded_by = db.relationship('User', backref='uploaded_attachments')

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'uploaded_by_id': self.uploaded_by_id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'uploaded_at': self.uploaded_at.isoformat(),
            'uploaded_by': self.uploaded_by.to_dict() if self.uploaded_by else None,
            'file_size_formatted': self.get_formatted_file_size()
        }

    def get_formatted_file_size(self):
        """Return human-readable file size."""
        if not self.file_size:
            return "Unknown"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"

    def get_file_extension(self):
        """Get file extension from filename."""
        return os.path.splitext(self.original_filename)[1].lower()

    def is_image(self):
        """Check if attachment is an image."""
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
        return self.get_file_extension() in image_extensions

    def is_document(self):
        """Check if attachment is a document."""
        doc_extensions = ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt']
        return self.get_file_extension() in doc_extensions

    def is_code_file(self):
        """Check if attachment is a code file."""
        code_extensions = ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.php', '.rb', '.go', '.rs', '.ts', '.jsx', '.vue', '.sql', '.json', '.xml', '.yaml', '.yml']
        return self.get_file_extension() in code_extensions

    def delete_file(self):
        """Delete the physical file from storage."""
        try:
            if os.path.exists(self.file_path):
                os.remove(self.file_path)
                return True
        except Exception as e:
            print(f"Error deleting file {self.file_path}: {e}")
            return False
        return False