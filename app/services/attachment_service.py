# app/services/attachment_service.py
import os
import uuid
from werkzeug.utils import secure_filename
from flask import current_app
from app.models.task import Task
from app.models.task_attachment import TaskAttachment
from app import db
from app.utils.logger import get_logger

logger = get_logger('attachments')

ALLOWED_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp', 'svg',
    'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt',
    'xls', 'xlsx', 'csv',
    'zip', 'tar', 'gz', 'rar',
    'py', 'js', 'ts', 'html', 'css', 'json', 'xml', 'yaml', 'yml',
    'java', 'cpp', 'c', 'h', 'go', 'rs', 'rb', 'php', 'sh',
    'mp4', 'mp3', 'avi', 'mov',
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB


def _allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


class AttachmentService:

    @staticmethod
    def get_upload_folder():
        folder = current_app.config.get('UPLOAD_FOLDER', '/tmp/task_attachments')
        os.makedirs(folder, exist_ok=True)
        return folder

    @staticmethod
    def upload_attachment(task_id, user_id, file):
        """Upload a file and attach it to a task."""
        try:
            task = Task.query.get(task_id)
            if not task:
                return {'error': 'Task not found'}, 404

            if not file or file.filename == '':
                return {'error': 'No file provided'}, 400

            original_filename = file.filename
            if not _allowed_file(original_filename):
                return {'error': 'File type not allowed'}, 400

            # Read file content to check size
            file_content = file.read()
            if len(file_content) > MAX_FILE_SIZE:
                return {'error': 'File size exceeds 10 MB limit'}, 400

            # Generate unique filename
            ext = original_filename.rsplit('.', 1)[1].lower()
            unique_filename = f'{uuid.uuid4().hex}.{ext}'

            upload_folder = AttachmentService.get_upload_folder()
            task_folder = os.path.join(upload_folder, str(task_id))
            os.makedirs(task_folder, exist_ok=True)

            file_path = os.path.join(task_folder, unique_filename)
            with open(file_path, 'wb') as f:
                f.write(file_content)

            # Determine MIME type
            mime_type = file.content_type or 'application/octet-stream'

            attachment = TaskAttachment(
                task_id=task_id,
                uploaded_by_id=user_id,
                filename=unique_filename,
                original_filename=secure_filename(original_filename),
                file_path=file_path,
                file_size=len(file_content),
                mime_type=mime_type,
            )
            db.session.add(attachment)
            db.session.commit()

            logger.info(f'Attachment {attachment.id} uploaded for task {task_id} by user {user_id}')
            return attachment.to_dict(), 201

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error uploading attachment for task {task_id}: {str(e)}')
            return {'error': f'Error uploading file: {str(e)}'}, 500

    @staticmethod
    def get_attachments(task_id):
        """Get all attachments for a task."""
        try:
            task = Task.query.get(task_id)
            if not task:
                return {'error': 'Task not found'}, 404

            attachments = TaskAttachment.query.filter_by(task_id=task_id).all()
            return [a.to_dict() for a in attachments], 200

        except Exception as e:
            logger.error(f'Error fetching attachments for task {task_id}: {str(e)}')
            return {'error': f'Error fetching attachments: {str(e)}'}, 500

    @staticmethod
    def get_attachment(attachment_id):
        """Get a single attachment by ID."""
        try:
            attachment = TaskAttachment.query.get(attachment_id)
            if not attachment:
                return {'error': 'Attachment not found'}, 404
            return attachment.to_dict(), 200

        except Exception as e:
            logger.error(f'Error fetching attachment {attachment_id}: {str(e)}')
            return {'error': f'Error fetching attachment: {str(e)}'}, 500

    @staticmethod
    def delete_attachment(attachment_id, user_id):
        """Delete an attachment. Only uploader or admin can delete."""
        try:
            attachment = TaskAttachment.query.get(attachment_id)
            if not attachment:
                return {'error': 'Attachment not found'}, 404

            from app.models.user import User
            from app.models.enums import UserRole
            requesting_user = User.query.get(user_id)
            if int(attachment.uploaded_by_id) != int(user_id) and (
                not requesting_user or requesting_user.role != UserRole.ADMIN
            ):
                return {'error': 'Permission denied'}, 403

            # Delete physical file
            attachment.delete_file()

            db.session.delete(attachment)
            db.session.commit()

            logger.info(f'Attachment {attachment_id} deleted by user {user_id}')
            return {'message': 'Attachment deleted successfully'}, 200

        except Exception as e:
            db.session.rollback()
            logger.error(f'Error deleting attachment {attachment_id}: {str(e)}')
            return {'error': f'Error deleting attachment: {str(e)}'}, 500
