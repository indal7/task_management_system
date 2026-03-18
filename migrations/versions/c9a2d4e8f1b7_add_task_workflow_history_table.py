"""add task_workflow_history table

Revision ID: c9a2d4e8f1b7
Revises: b4a1f7c9d2e3
Create Date: 2026-03-18 13:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c9a2d4e8f1b7"
down_revision = "b4a1f7c9d2e3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "task_workflow_history",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("task_id", sa.Integer(), nullable=False),
        sa.Column("from_status", sa.String(length=50), nullable=True),
        sa.Column("to_status", sa.String(length=50), nullable=True),
        sa.Column("from_stage", sa.String(length=100), nullable=True),
        sa.Column("to_stage", sa.String(length=100), nullable=True),
        sa.Column("from_sprint_id", sa.Integer(), nullable=True),
        sa.Column("to_sprint_id", sa.Integer(), nullable=True),
        sa.Column("from_assignee_id", sa.Integer(), nullable=True),
        sa.Column("to_assignee_id", sa.Integer(), nullable=True),
        sa.Column("changed_by_id", sa.Integer(), nullable=True),
        sa.Column("change_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["changed_by_id"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["from_assignee_id"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["from_sprint_id"], ["sprint.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["task_id"], ["task.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["to_assignee_id"], ["user.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["to_sprint_id"], ["sprint.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_task_workflow_history_task_id", "task_workflow_history", ["task_id"], unique=False)
    op.create_index("ix_task_workflow_history_changed_by_id", "task_workflow_history", ["changed_by_id"], unique=False)
    op.create_index("ix_task_workflow_history_created_at", "task_workflow_history", ["created_at"], unique=False)


def downgrade():
    op.drop_index("ix_task_workflow_history_created_at", table_name="task_workflow_history")
    op.drop_index("ix_task_workflow_history_changed_by_id", table_name="task_workflow_history")
    op.drop_index("ix_task_workflow_history_task_id", table_name="task_workflow_history")
    op.drop_table("task_workflow_history")
