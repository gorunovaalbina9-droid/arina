"""Alembic env — URL из DATABASE_URL (sync psycopg для PostgreSQL)."""

from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def _sync_database_url() -> str:
    raw = os.environ.get("DATABASE_URL", "").strip()
    if not raw:
        return config.get_main_option("sqlalchemy.url") or ""
    if raw.startswith("postgresql+asyncpg://"):
        return "postgresql+psycopg://" + raw.removeprefix("postgresql+asyncpg://")
    if raw.startswith("sqlite+aiosqlite://"):
        return "sqlite://" + raw.removeprefix("sqlite+aiosqlite://")
    return raw


def run_migrations_offline() -> None:
    url = _sync_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _sync_database_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
