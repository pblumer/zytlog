"""add system admin role

Revision ID: 20260403_0008
Revises: 20260331_0007
Create Date: 2026-04-03 02:20:00
"""

from typing import Sequence

from alembic import op


revision: str = "20260403_0008"
down_revision: str | None = "20260331_0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'SYSTEM_ADMIN'")


def downgrade() -> None:
    # PostgreSQL enum value removal is intentionally left as a no-op.
    # Downgrading would require rebuilding the enum and rewriting dependent rows.
    pass
