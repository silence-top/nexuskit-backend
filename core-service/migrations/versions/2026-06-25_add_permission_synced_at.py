"""add permission synced_at audit column

Revision ID: a3c7e9f1b204
Revises: 0e52f5b7538a
Create Date: 2026-06-25 10:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3c7e9f1b204'
down_revision: Union[str, None] = '0e52f5b7538a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'auth_permissions',
        sa.Column(
            'synced_at',
            sa.DateTime(timezone=True),
            nullable=True,
            comment='最近一次子系统同步时间戳',
        ),
    )


def downgrade() -> None:
    op.drop_column('auth_permissions', 'synced_at')
