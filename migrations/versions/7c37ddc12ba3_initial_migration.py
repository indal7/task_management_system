"""initial migration

Revision ID: 7c37ddc12ba3
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c37ddc12ba3'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    userrole = sa.Enum(
        'ADMIN', 'PROJECT_MANAGER', 'TEAM_LEAD', 'SENIOR_DEVELOPER', 'DEVELOPER',
        'QA_ENGINEER', 'DEVOPS_ENGINEER', 'UI_UX_DESIGNER', 'BUSINESS_ANALYST',
        'PRODUCT_OWNER', 'SCRUM_MASTER',
        name='userrole'
    )
    projectstatus = sa.Enum(
        'PLANNING', 'ACTIVE', 'ON_HOLD', 'COMPLETED', 'CANCELLED',
        name='projectstatus'
    )
    sprintstatus = sa.Enum(
        'PLANNED', 'ACTIVE', 'COMPLETED', 'CANCELLED',
        name='sprintstatus'
    )
    taskstatus = sa.Enum(
        'BACKLOG', 'TODO', 'IN_PROGRESS', 'IN_REVIEW', 'TESTING',
        'BLOCKED', 'DONE', 'CANCELLED', 'DEPLOYED',
        name='taskstatus'
    )
    taskpriority = sa.Enum(
        'CRITICAL', 'HIGH', 'MEDIUM', 'LOW',
        name='taskpriority'
    )
    tasktype = sa.Enum(
        'FEATURE', 'BUG', 'ENHANCEMENT', 'REFACTOR', 'DOCUMENTATION',
        'TESTING', 'DEPLOYMENT', 'RESEARCH', 'MAINTENANCE', 'SECURITY',
        name='tasktype'
    )
    estimationunit = sa.Enum(
        'HOURS', 'DAYS', 'STORY_POINTS',
        name='estimationunit'
    )
    notificationtype = sa.Enum(
        'TASK_ASSIGNED', 'TASK_UPDATED', 'TASK_COMPLETED', 'TASK_OVERDUE',
        'COMMENT_ADDED', 'PROJECT_UPDATED', 'SPRINT_STARTED', 'SPRINT_COMPLETED',
        'MENTION',
        name='notificationtype'
    )

    # ### Create user table ###
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=200), nullable=False),
        sa.Column('role', userrole, nullable=False),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('skills', sa.Text(), nullable=True),
        sa.Column('github_username', sa.String(length=100), nullable=True),
        sa.Column('linkedin_url', sa.String(length=500), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('timezone', sa.String(length=50), nullable=True),
        sa.Column('daily_work_hours', sa.Float(), nullable=True),
        sa.Column('hourly_rate', sa.Float(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('last_login', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    # ### Create project table ###
    op.create_table(
        'project',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', projectstatus, nullable=False),
        sa.Column('repository_url', sa.String(length=500), nullable=True),
        sa.Column('documentation_url', sa.String(length=500), nullable=True),
        sa.Column('technology_stack', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('client_name', sa.String(length=200), nullable=True),
        sa.Column('client_email', sa.String(length=120), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ### Create project_members table ###
    op.create_table(
        'project_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(length=100), nullable=True),
        sa.Column('can_create_tasks', sa.Boolean(), nullable=True),
        sa.Column('can_edit_tasks', sa.Boolean(), nullable=True),
        sa.Column('can_delete_tasks', sa.Boolean(), nullable=True),
        sa.Column('can_manage_sprints', sa.Boolean(), nullable=True),
        sa.Column('can_manage_members', sa.Boolean(), nullable=True),
        sa.Column('joined_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('project_id', 'user_id', name='unique_project_member')
    )

    # ### Create sprint table ###
    op.create_table(
        'sprint',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sprintstatus, nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=False),
        sa.Column('start_date', sa.DateTime(), nullable=False),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('goal', sa.Text(), nullable=True),
        sa.Column('capacity_hours', sa.Float(), nullable=True),
        sa.Column('velocity_points', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ### Create task table ###
    op.create_table(
        'task',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', taskstatus, nullable=False),
        sa.Column('priority', taskpriority, nullable=False),
        sa.Column('task_type', tasktype, nullable=False),
        sa.Column('assigned_to_id', sa.Integer(), nullable=True),
        sa.Column('created_by_id', sa.Integer(), nullable=False),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('sprint_id', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('completion_date', sa.DateTime(), nullable=True),
        sa.Column('estimated_hours', sa.Float(), nullable=True),
        sa.Column('actual_hours', sa.Float(), nullable=True),
        sa.Column('story_points', sa.Integer(), nullable=True),
        sa.Column('estimation_unit', estimationunit, nullable=True),
        sa.Column('labels', sa.Text(), nullable=True),
        sa.Column('acceptance_criteria', sa.Text(), nullable=True),
        sa.Column('parent_task_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to_id'], ['user.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_task_id'], ['task.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sprint_id'], ['sprint.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )

    # ### Create task_comment table ###
    op.create_table(
        'task_comment',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ### Create task_attachments table ###
    op.create_table(
        'task_attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_by_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ### Create time_logs table ###
    op.create_table(
        'time_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('hours', sa.Float(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('work_date', sa.Date(), nullable=False),
        sa.Column('logged_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ### Create notification table ###
    op.create_table(
        'notification',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.Integer(), nullable=True),
        sa.Column('type', notificationtype, nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('related_user_id', sa.Integer(), nullable=True),
        sa.Column('project_id', sa.Integer(), nullable=True),
        sa.Column('sprint_id', sa.Integer(), nullable=True),
        sa.Column('read', sa.Boolean(), nullable=True),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['project_id'], ['project.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['related_user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['sprint_id'], ['sprint.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['task_id'], ['task.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('notification')
    op.drop_table('time_logs')
    op.drop_table('task_attachments')
    op.drop_table('task_comment')
    op.drop_table('task')
    op.drop_table('sprint')
    op.drop_table('project_members')
    op.drop_table('project')
    op.drop_table('user')

    # Drop enum types
    sa.Enum(name='notificationtype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='estimationunit').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='tasktype').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='taskpriority').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='taskstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='sprintstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='projectstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum(name='userrole').drop(op.get_bind(), checkfirst=True)
