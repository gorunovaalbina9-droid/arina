"""Путь к файлу SQLite из URL async-драйвера (только для локальной синхронной утилиты загрузки режимов)."""

from __future__ import annotations

from pathlib import Path


def sqlite_file_path_from_url(database_url: str) -> Path | None:
    if not database_url.startswith("sqlite+"):
        return None
    marker = "sqlite+aiosqlite:///"
    if not database_url.startswith(marker):
        return None
    rest = database_url[len(marker) :].lstrip("/")
    rest = rest.replace("\\", "/")
    if not rest:
        return None
    p = Path(rest)
    if p.suffix.lower() in {".db", ".sqlite", ".sqlite3"}:
        return p
    return None
