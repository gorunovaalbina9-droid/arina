"""
Отчёт «прогресс» для родителя — без LLM, только долгая память (category=progress, note).

Пример:
  python -m center_voice_agent.cli.parent_progress_report --child-profile-id child-1
"""

from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from center_voice_agent.composition.container import AppContainer
from center_voice_agent.db.session import init_database
from center_voice_agent.settings import get_settings


def _render_markdown(
    *,
    child_profile_id: str,
    progress_lines: list[str],
    note_lines: list[str],
    scenario_id: str | None,
    scenario_node_id: str | None,
) -> str:
    parts = [
        f"# Прогресс занятий — {child_profile_id}",
        "",
        "_Отчёт сформирован из долгосрочной памяти агента. Сырой диалог не включён._",
        "",
    ]
    if scenario_id:
        parts.append(f"**Текущий сценарий (последняя сессия в БД):** `{scenario_id}`")
        if scenario_node_id:
            parts.append(f" — узел `{scenario_node_id}`")
        parts.append("")
    parts.append("## Прогресс")
    if progress_lines:
        parts.extend(f"- {line}" for line in progress_lines)
    else:
        parts.append("- _(записей progress пока нет)_")
    parts.append("")
    parts.append("## Заметки педагога")
    if note_lines:
        parts.extend(f"- {line}" for line in note_lines)
    else:
        parts.append("- _(заметок note пока нет)_")
    parts.append("")
    return "\n".join(parts)


def _format_entry(category: str, key: str | None, value: str, updated: str) -> str:
    prefix = f"[{category}]"
    if key:
        prefix += f" {key}:"
    return f"{prefix} {value} (_обновлено {updated}_)".strip()


async def _run(args: argparse.Namespace) -> int:
    settings = get_settings()
    await init_database(settings.project_root, settings.database_url)
    container = AppContainer.from_settings(settings)
    child_id = args.child_profile_id

    progress = await container.memory_repository.list_entries(child_id, "progress", limit=args.limit)
    notes = await container.memory_repository.list_entries(child_id, "note", limit=args.limit)
    scenario_id, scenario_node_id = await container.session_repository.latest_scenario_for_child(child_id)

    progress_lines = [_format_entry(e.category, e.key, e.value_text, e.updated_at) for e in progress]
    note_lines = [_format_entry(e.category, e.key, e.value_text, e.updated_at) for e in notes]

    if args.format == "json":
        payload = {
            "child_profile_id": child_id,
            "scenario_id": scenario_id,
            "scenario_node_id": scenario_node_id,
            "progress": [{"key": e.key, "value": e.value_text, "updated_at": e.updated_at} for e in progress],
            "notes": [{"key": e.key, "value": e.value_text, "updated_at": e.updated_at} for e in notes],
        }
        body = json.dumps(payload, ensure_ascii=False, indent=2)
    else:
        body = _render_markdown(
            child_profile_id=child_id,
            progress_lines=progress_lines,
            note_lines=note_lines,
            scenario_id=scenario_id,
            scenario_node_id=scenario_node_id,
        )

    if args.out:
        Path(args.out).write_text(body, encoding="utf-8")
        print(f"Записано: {args.out}")
    else:
        print(body)
    await container.aclose()
    return 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Отчёт прогресса для родителя (без LLM)")
    parser.add_argument("--child-profile-id", required=True, help="ID профиля ребёнка")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--out", default=None, help="Файл для сохранения")
    parser.add_argument("--limit", type=int, default=30, help="Макс. записей на категорию")
    raise SystemExit(asyncio.run(_run(parser.parse_args())))


if __name__ == "__main__":
    main()
