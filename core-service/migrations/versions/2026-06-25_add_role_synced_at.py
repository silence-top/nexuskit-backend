"""add role synced_at column

Revision ID: b4d8f2e91a05
Revises: a3c7e9f1b204
Create Date: 2026-06-25
"""
from alembic import op
import sqlalchemy as sa

revision = "b4d8f2e91a05"
down_revision = "a3c7e9f1b204"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "auth_roles",
        sa.Column(
            "synced_at",
            sa.DateTime(timezone=True),
            nullable=True,
            comment="最近一次子系统同步时间戳",
        ),
    )


def downgrade() -> None:
    op.drop_column("auth_roles", "synced_at")
