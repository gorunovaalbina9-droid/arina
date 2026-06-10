"""Чтение/запись mode_definitions. Чтение — SQLAlchemy; publish — async (см. admin/publish)."""

from __future__ import annotations

from typing import Optional

from center_voice_agent.admin.async_util import run_coroutine_sync
from center_voice_agent.admin.db_read import fetch_published_mode_yamls_sync


def fetch_published_mode_yamls(
    database_url: str,
    *,
    center_id: Optional[str] = None,
) -> dict[str, str]:
    """Синхронное чтение (SQLAlchemy sync). Для async runtime — fetch_published_mode_yamls_async."""
    return fetch_published_mode_yamls_sync(database_url, center_id=center_id)


def publish_mode_yaml_sync(
    database_url: str,
    *,
    config_yaml: str,
    mode_id: str,
    center_id: Optional[str] = None,
    status: str = "published",
) -> str:
    """Обратная совместимость тестов: async publish на переданном database_url."""

    async def _run() -> str:
        from center_voice_agent.admin.publish import publish_mode_yaml
        from center_voice_agent.composition.runtime import _process_container
        from center_voice_agent.db.session import create_engine_and_session_factory, run_migrations
        from center_voice_agent.settings import get_settings

        if (
            _process_container is not None
            and _process_container.settings.database_url == database_url
        ):
            return await publish_mode_yaml(
                _process_container.engine,
                config_yaml=config_yaml,
                mode_id=mode_id,
                center_id=center_id,
                status=status,
            )

        settings = get_settings()
        engine, _ = create_engine_and_session_factory(database_url)
        try:
            await run_migrations(engine, settings.project_root)
            return await publish_mode_yaml(
                engine,
                config_yaml=config_yaml,
                mode_id=mode_id,
                center_id=center_id,
                status=status,
            )
        finally:
            await engine.dispose()

    return run_coroutine_sync(_run)
