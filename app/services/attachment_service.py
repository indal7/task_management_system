# app/services/attachment_service.py
import os
import uuid
from werkzeug.utils import secure_filename

from app.models.task_attachment import TaskAttachment
from app.models.task import Task
from app import db
from app.utils.logger import get_logger

logger = get_logger('attachment_service')

ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg',  # images
    'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',           # documents
    'xls', 'xlsx', 'csv',                                  # spreadsheets
    'ppt', 'pptx',                                         # presentations
    'py', 'js', 'ts', 'html', 'css', 'java', 'cpp',       # code
    'c', 'php', 'rb', 'go', 'rs', 'jsx', 'vue',
    'sql', 'json', 'xml', 'yaml', 'yml', 'md',
    'zip', 'tar', 'gz',                                    # archives
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class AttachmentService:

    @staticmethod
    def get_upload_dir(app=None):
        """Return (and create) the upload directory."""
        from flask import current_app
        app = app or current_app
        upload_dir = app.config.get('UPLOAD_FOLDER', '/tmp/task_attachments')
        os.makedirs(upload_dir, exist_ok=True)
        return upload_dir

    @staticmethod
    def get_task_attachments(task_id, user_id):
        """Return all attachments for a task."""
        try:
            task = Task.query.get(task_id)
            if not task:
                return {'error': 'Task not found'}, 404

            attachments = TaskAttachment.query.filter_by(task_id=task_id).all()
            return [a.to_dict() for a in attachments], 200

        except Exception as e:
            logger.error(f"Error fetching attachments for task {task_id}: {e}")
            return {'error': f'Error fetching attachments: {str(e)}'}, 500

    @staticmethod
    def upload_attachment(task_id, user_id, file):
        """Save an uploaded file and persist the metadata."""
        try:
            task = Task.query.get(task_id)
            if not task:
                return {'error': 'Task not found'}, 404

            if not file or file.filename == '':
                return {'error': 'No file provided'}, 400

            if not _allowed_file(file.filename):
                return {
                    'error': 'File type not allowed. Supported types: '
                             + ', '.join(sorted(ALLOWED_EXTENSIONS))
                }, 400

            # Read file content to check size
            content = file.read()
            if len(content) > MAX_FILE_SIZE:
                return {
                    'error': f'File too large. Maximum size is '
                             f'{MAX_FILE_SIZE // (1024*1024)} MB'
                }, 400
            file.seek(0)  # reset pointer for saving

            original_filename = secure_filename(file.filename)
            ext = original_filename.rsplit('.', 1)[1].lower() \
                if '.' in original_filename else ''
            stored_filename = f"{uuid.uuid4().hex}.{ext}" if ext else \
                f"{uuid.uuid4().hex}"

            upload_dir = AttachmentService.get_upload_dir()
            file_path = os.path.join(upload_dir, stored_filename)
            file.save(file_path)

            mime_type = file.content_type or 'application/octet-stream'
            file_size = os.path.getsize(file_path)

            attachment = TaskAttachment(
                task_id=task_id,
                uploaded_by_id=user_id,
                filename=stored_filename,
                original_filename=original_filename,
                file_path=file_path,
                file_size=file_size,
                mime_type=mime_type,
            )
            db.session.add(attachment)
            db.session.commit()

            logger.info(
                f"Attachment {attachment.id} uploaded to task {task_id} "
                f"by user {user_id}"
            )
            return attachment.to_dict(), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error uploading attachment to task {task_id}: {e}")
            return {'error': f'Error uploading attachment: {str(e)}'}, 500

    @staticmethod
    def delete_attachment(attachment_id, user_id, user_role):
        """Delete an attachment (uploader or admin only)."""
        try:
            from app.models.enums import UserRole
            attachment = TaskAttachment.query.get(attachment_id)
            if not attachment:
                return {'error': 'Attachment not found'}, 404

            is_admin = user_role == UserRole.ADMIN
            is_uploader = attachment.uploaded_by_id == int(user_id)
            if not is_admin and not is_uploader:
                return {'error': 'Permission denied'}, 403

            # Remove physical file
            attachment.delete_file()

            db.session.delete(attachment)
            db.session.commit()

            logger.info(
                f"Attachment {attachment_id} deleted by user {user_id}"
            )
            return {'message': 'Attachment deleted successfully'}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting attachment {attachment_id}: {e}")
            return {'error': f'Error deleting attachment: {str(e)}'}, 500

    @staticmethod
    def get_attachment(attachment_id, user_id):
        """Get attachment metadata."""
        try:
            attachment = TaskAttachment.query.get(attachment_id)
            if not attachment:
                return {'error': 'Attachment not found'}, 404
            return attachment.to_dict(), 200
        except Exception as e:
            logger.error(f"Error fetching attachment {attachment_id}: {e}")
            return {'error': f'Error fetching attachment: {str(e)}'}, 500
