"""add created_by and deleted_by to tenants and rename user audit columns

Revision ID: c174f8287e91
Revises: 842a206d9511
Create Date: 2026-10-23 13:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c174f8287e91'
down_revision: Union[str, Sequence[str], None] = '842a206d9511'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add created_by and deleted_by columns to tenants
    op.add_column('tenants', sa.Column('created_by', sa.UUID(), nullable=True))
    op.add_column('tenants', sa.Column('deleted_by', sa.UUID(), nullable=True))
    op.create_foreign_key(
        'fk_tenants_users_created_by',
        'tenants',
        'users',
        ['created_by'],
        ['id'],
        ondelete='SET NULL'
    )
    op.create_foreign_key(
        'fk_tenants_users_deleted_by',
        'tenants',
        'users',
        ['deleted_by'],
        ['id'],
        ondelete='SET NULL'
    )

    # 2. Rename created_by_id to created_by and deleted_by_id to deleted_by in users
    op.alter_column('users', 'created_by_id', new_column_name='created_by')
    op.alter_column('users', 'deleted_by_id', new_column_name='deleted_by')


def downgrade() -> None:
    op.alter_column('users', 'deleted_by', new_column_name='deleted_by_id')
    op.alter_column('users', 'created_by', new_column_name='created_by_id')
    op.drop_constraint('fk_tenants_users_deleted_by', 'tenants', type_='foreignkey')
    op.drop_constraint('fk_tenants_users_created_by', 'tenants', type_='foreignkey')
    op.drop_column('tenants', 'deleted_by')
    op.drop_column('tenants', 'created_by')
