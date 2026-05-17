from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import structlog

from center_voice_agent.modes.db_source import fetch_published_mode_yamls
from center_voice_agent.modes.schema import (
    ModeConfig,
    load_mode_yaml_file,
    load_mode_yaml_text,
    validate_mode_graph,
)

log = structlog.get_logger(__name__)


class ModeRegistry:
    """Динамическая загрузка режимов: YAML в каталоге и/или опубликованные строки в SQLite."""

    def __init__(
        self,
        modes_dir: Path,
        *,
        project_root: Path,
        database_url: Optional[str] = None,
        modes_source: str = "files",
        modes_center_id: Optional[str] = None,
    ) -> None:
        self._modes_dir = modes_dir
        self._project_root = project_root
        self._database_url = database_url
        self._modes_source = modes_source
        self._modes_center_id = modes_center_id
        self._cache: dict[str, ModeConfig] = {}
        self._source_files: dict[str, Optional[Path]] = {}

    def reload_all(self) -> list[str]:
        """Полная перезагрузка. Возвращает список mode_id (отсортированный)."""
        t0 = time.perf_counter()
        self._cache.clear()
        self._source_files.clear()

        file_meta: list[dict[str, Any]] = []
        configs: dict[str, ModeConfig] = {}

        if self._modes_dir.exists():
            seen: dict[str, Path] = {}
            for p in sorted(self._modes_dir.glob("*.yaml")):
                st = p.stat()
                file_meta.append(
                    {
                        "name": p.name,
                        "mtime_utc": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(),
                        "size_bytes": st.st_size,
                    }
                )
                cfg = load_mode_yaml_file(p, self._project_root)
                if cfg.id in seen:
                    raise ValueError(
                        f"Дублирующийся id режима «{cfg.id}» в файлах {seen[cfg.id].name} и {p.name}"
                    )
                seen[cfg.id] = p
                configs[cfg.id] = cfg
                self._source_files[cfg.id] = p
        elif self._modes_source == "files":
            log.warning("modes_dir_missing", path=str(self._modes_dir))

        db_yamls: dict[str, str] = {}
        if self._modes_source in ("database", "hybrid") and self._database_url:
            db_yamls = fetch_published_mode_yamls(
                self._database_url,
                center_id=self._modes_center_id,
            )

        if self._modes_source == "database":
            if not db_yamls:
                log.warning(
                    "database_modes_empty_fallback_files",
                    modes_dir=str(self._modes_dir),
                )
            else:
                configs = {}
                self._source_files.clear()
                for mid, ytext in db_yamls.items():
                    cfg = load_mode_yaml_text(
                        ytext,
                        self._project_root,
                        source_hint=f"database:{mid}",
                    )
                    configs[mid] = cfg
                    self._source_files[mid] = None
        elif self._modes_source == "hybrid" and db_yamls:
            for mid, ytext in db_yamls.items():
                cfg = load_mode_yaml_text(
                    ytext,
                    self._project_root,
                    source_hint=f"database:{mid}",
                )
                configs[mid] = cfg
                self._source_files[mid] = None

        if not configs and self._modes_source == "files" and not self._modes_dir.exists():
            log.warning("modes_dir_missing", path=str(self._modes_dir))
            return []

        validate_mode_graph(configs)
        self._cache = configs

        dt_ms = int((time.perf_counter() - t0) * 1000)
        ids = sorted(self._cache.keys())
        log.info(
            "mode_registry_loaded",
            mode_ids=ids,
            modes_dir=str(self._modes_dir),
            modes_source=self._modes_source,
            modes_center_id=self._modes_center_id,
            duration_ms=dt_ms,
            file_count=len(file_meta),
            mode_files=file_meta,
            database_mode_ids=sorted(db_yamls.keys()) if db_yamls else [],
        )
        return ids

    def reload(self) -> None:
        self.reload_all()

    def get(self, mode_id: str) -> ModeConfig:
        if not self._cache:
            self.reload_all()
        if mode_id not in self._cache:
            self.reload_all()
        if mode_id not in self._cache:
            raise KeyError(
                f"Неизвестный режим: {mode_id}. Проверьте YAML в {self._modes_dir} "
                f"и при MODES_SOURCE=database|hybrid — таблицу mode_definitions."
            )
        return self._cache[mode_id]

    def list_ids(self) -> list[str]:
        if not self._cache:
            self.reload_all()
        return sorted(self._cache.keys())

    def get_all(self) -> dict[str, ModeConfig]:
        if not self._cache:
            self.reload_all()
        return dict(self._cache)

    def source_path(self, mode_id: str) -> Optional[Path]:
        if not self._cache:
            self.reload_all()
        return self._source_files.get(mode_id)
