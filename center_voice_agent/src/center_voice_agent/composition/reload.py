"""Перезагрузка каталога режимов/сценариев в long-running процессе."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Optional

import structlog

from center_voice_agent.scenarios.loader import clear_scenario_scan_cache
from center_voice_agent.settings import Settings, get_settings

if TYPE_CHECKING:
    from center_voice_agent.composition.container import AppContainer

log = structlog.get_logger(__name__)


@dataclass
class CatalogReloadResult:
    mode_ids: list[str]
    scenario_ids: list[str]
    settings_cache_cleared: bool = False


def _list_scenario_ids(settings: Settings) -> list[str]:
    root = settings.scenarios_dir
    if not root.is_dir():
        return []
    from center_voice_agent.scenarios.graph_engine import load_scenario

    ids: list[str] = []
    for p in sorted(root.glob("*.yaml")):
        try:
            ids.append(load_scenario(p).id)
        except Exception:
            continue
    return sorted(set(ids))


def reload_catalog(
    container: "AppContainer",
    *,
    clear_settings_cache: bool = False,
) -> CatalogReloadResult:
    """
    После modes_publish / scenarios_publish / правки YAML:
    modes из registry, scan сценариев, опционально сброс get_settings().
    """
    clear_scenario_scan_cache()
    mode_ids = container.mode_registry.reload_all()
    scenario_ids = _list_scenario_ids(container.settings)
    settings_cleared = False
    if clear_settings_cache:
        get_settings.cache_clear()
        settings_cleared = True
    log.info(
        "catalog_reloaded",
        mode_ids=mode_ids,
        scenario_ids=scenario_ids,
        settings_cache_cleared=settings_cleared,
    )
    return CatalogReloadResult(
        mode_ids=mode_ids,
        scenario_ids=scenario_ids,
        settings_cache_cleared=settings_cleared,
    )


async def reload_process_catalog(
    *,
    clear_settings_cache: bool = False,
) -> Optional[CatalogReloadResult]:
    from center_voice_agent.composition.runtime import get_process_container

    container = await get_process_container()
    return reload_catalog(container, clear_settings_cache=clear_settings_cache)
