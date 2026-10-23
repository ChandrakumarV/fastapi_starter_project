"""rename_name_to_full_name_in_users

Revision ID: cf3711c40f80
Revises: c174f8287e91
Create Date: 2026-10-23 15:40:17.861109

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf3711c40f80'
down_revision: Union[str, Sequence[str], None] = 'c174f8287e91'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'name', new_column_name='full_name')


def downgrade() -> None:
    op.alter_column('users', 'full_name', new_column_name='name')
