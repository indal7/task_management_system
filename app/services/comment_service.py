# app/services/comment_service.py
from app.models.task_comment import TaskComment
from app.models.task import Task
from app.models.user import User
from app import db
from app.utils.cache_utils import cache, cached_per_user, CacheKeys, invalidate_user_cache, invalidate_project_cache
from app.utils.logger import get_logger, log_db_query

logger = get_logger('comments')


class CommentService:

    @staticmethod
    @cached_per_user(timeout=300, key_prefix=CacheKeys.TASK_COMMENTS)
    def get_comments_by_task(task_id):
        """Gets all comments for a specific task."""
        try:
            comments = TaskComment.query.filter_by(task_id=task_id).order_by(TaskComment.created_at.asc()).all()
            logger.info(f"Fetched {len(comments)} comments for task {task_id}")
            return [comment.to_dict() for comment in comments]
        except Exception as e:
            logger.error(f"Error fetching comments for task {task_id}: {str(e)}")
            return {'error': f'Error fetching comments: {str(e)}'}, 500

    @staticmethod
    def add_comment(task_id, user_id, comment_text):
        """Adds a new comment to a task."""
        try:
            task = Task.query.get_or_404(task_id)

            comment = TaskComment(
                task_id=task_id,
                user_id=user_id,
                comment=comment_text
            )

            db.session.add(comment)
            db.session.commit()
            log_db_query("INSERT", "task_comments")
            logger.info(f"User {user_id} added comment {comment.id} to task {task_id}")

            # Invalidate cache for this task
            invalidate_project_cache(task.project_id)

            return comment.to_dict()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding comment to task {task_id}: {str(e)}")
            return {'error': f'Error adding comment: {str(e)}'}, 500

    @staticmethod
    def update_comment(comment_id, user_id, comment_text):
        """Updates an existing comment."""
        try:
            comment = TaskComment.query.get_or_404(comment_id)

            if comment.user_id != user_id:
                logger.warning(f"User {user_id} unauthorized to update comment {comment_id}")
                return {'error': 'You are not authorized to edit this comment'}, 403

            comment.comment = comment_text
            db.session.commit()
            log_db_query("UPDATE", "task_comments")
            logger.info(f"Comment {comment_id} updated by user {user_id}")

            # Invalidate cache for this task
            invalidate_project_cache(comment.task.project_id)

            return comment.to_dict()
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating comment {comment_id}: {str(e)}")
            return {'error': f'Error updating comment: {str(e)}'}, 500

    @staticmethod
    def delete_comment(comment_id, user_id):
        """Deletes a comment."""
        try:
            comment = TaskComment.query.get_or_404(comment_id)

            if comment.user_id != user_id:
                logger.warning(f"User {user_id} unauthorized to delete comment {comment_id}")
                return {'error': 'You are not authorized to delete this comment'}, 403

            project_id = comment.task.project_id
            db.session.delete(comment)
            db.session.commit()
            log_db_query("DELETE", "task_comments")
            logger.info(f"Comment {comment_id} deleted by user {user_id}")

            # Invalidate cache for this task
            invalidate_project_cache(project_id)

            return {'message': 'Comment deleted successfully'}
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting comment {comment_id}: {str(e)}")
            return {'error': f'Error deleting comment: {str(e)}'}, 500
