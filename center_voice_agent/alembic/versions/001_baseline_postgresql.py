"""Baseline PostgreSQL schema from db/migrations/postgresql/*.sql

Revision ID: 001_baseline
Revises:
Create Date: 2026-05-29

После center-agent-init-db выполните: alembic stamp head
Дальнейшие DDL — новые ревизии Alembic.
"""

from typing import Sequence, Union

revision: str = "001_baseline"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
