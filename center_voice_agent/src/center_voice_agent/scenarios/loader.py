from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

import structlog

from center_voice_agent.scenarios.db_source import fetch_published_scenario_yamls
from center_voice_agent.scenarios.graph_engine import ScenarioGraph, load_scenario, load_scenario_yaml_string

log = structlog.get_logger(__name__)


@lru_cache
def _scan_scenario_files(scenarios_dir: str) -> tuple[tuple[str, str], ...]:
    """Кэш: (scenario_id, path_str) для всех *.yaml в каталоге."""
    root = Path(scenarios_dir)
    if not root.is_dir():
        return ()
    out: list[tuple[str, str]] = []
    for p in sorted(root.glob("*.yaml")):
        try:
            g = load_scenario(p)
            out.append((g.id, str(p.resolve())))
        except Exception:
            continue
    return tuple(out)


def clear_scenario_scan_cache() -> None:
    _scan_scenario_files.cache_clear()


def resolve_scenario_path(scenarios_dir: Path, scenario_id: str) -> Path:
    for sid, path_str in _scan_scenario_files(str(scenarios_dir.resolve())):
        if sid == scenario_id:
            return Path(path_str)
    raise FileNotFoundError(
        f"Сценарий «{scenario_id}» не найден в {scenarios_dir} (ожидался уникальный id в *.yaml)"
    )


def load_scenario_by_id(scenarios_dir: Path, scenario_id: str) -> ScenarioGraph:
    path = resolve_scenario_path(scenarios_dir, scenario_id)
    return load_scenario(path)


def load_scenario_graph_unified(
    scenarios_dir: Path,
    scenario_id: str,
    *,
    database_url: Optional[str] = None,
    scenarios_source: str = "files",
    scenarios_center_id: Optional[str] = None,
) -> ScenarioGraph:
    """
    Источник графа: files | database | hybrid (как MODES_SOURCE).
    При database и пустой БД — fallback на файлы.
    """
    db_yaml: str | None = None
    if scenarios_source in ("database", "hybrid") and database_url:
        published = fetch_published_scenario_yamls(database_url, center_id=scenarios_center_id)
        db_yaml = published.get(scenario_id)

    if scenarios_source == "database":
        if db_yaml:
            log.debug("scenario_loaded_from_database", scenario_id=scenario_id)
            return load_scenario_yaml_string(db_yaml, source_hint=f"database:{scenario_id}")
        log.warning("scenarios_database_empty_fallback_files", scenario_id=scenario_id)
        return load_scenario_by_id(scenarios_dir, scenario_id)

    if scenarios_source == "hybrid" and db_yaml:
        log.debug("scenario_loaded_hybrid_overlay", scenario_id=scenario_id)
        return load_scenario_yaml_string(db_yaml, source_hint=f"hybrid-db:{scenario_id}")

    return load_scenario_by_id(scenarios_dir, scenario_id)
