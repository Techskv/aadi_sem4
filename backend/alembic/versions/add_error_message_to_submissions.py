"""Add error_message column to submissions

Revision ID: add_error_message_col
Revises: ed43e94f99a2
Create Date: 2026-04-18

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_error_message_col'
down_revision: Union[str, None] = 'ed43e94f99a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('submissions', sa.Column('error_message', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('submissions', 'error_message')
