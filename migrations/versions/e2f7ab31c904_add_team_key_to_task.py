"""add team_key to task

Revision ID: e2f7ab31c904
Revises: c9a2d4e8f1b7
Create Date: 2026-03-18 14:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e2f7ab31c904"
down_revision = "c9a2d4e8f1b7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('task', sa.Column('team_key', sa.String(length=100), nullable=True))
    op.create_index('ix_task_team_key', 'task', ['team_key'], unique=False)


def downgrade():
    op.drop_index('ix_task_team_key', table_name='task')
    op.drop_column('task', 'team_key')
