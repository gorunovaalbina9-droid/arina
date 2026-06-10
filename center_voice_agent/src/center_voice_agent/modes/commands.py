from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class ModeCommandEntry(BaseModel):
    mode_id: str
    phrases: list[str] = Field(default_factory=list)


class ModeCommandsFile(BaseModel):
    entries: list[ModeCommandEntry] = Field(default_factory=list)


def load_mode_commands(path: Path) -> ModeCommandsFile:
    if not path.is_file():
        return ModeCommandsFile(entries=[])
    raw = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not raw:
        return ModeCommandsFile(entries=[])
    if not isinstance(raw, dict):
        raise ValueError(f"Ожидался объект YAML в {path}")
    entries_raw = raw.get("entries") or raw.get("commands") or []
    return ModeCommandsFile.model_validate({"entries": entries_raw})


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def _phrase_matches_user(user_n: str, phrase: str) -> bool:
    """Точное совпадение или фраза-команда в начале/как отдельное слово (меньше ложных срабатываний)."""
    if not phrase or len(phrase) < 2:
        return False
    if user_n == phrase:
        return True
    if user_n.startswith(phrase + " ") or user_n.startswith(phrase + ","):
        return True
    if user_n.endswith(" " + phrase):
        return True
    wrapped = f" {user_n} "
    return f" {phrase} " in wrapped


def try_parse_mode_switch(
    user_text: str,
    *,
    commands: ModeCommandsFile,
    voice_aliases: dict[str, list[str]],
    nlu_enabled: bool = False,
    nlu_threshold: float = 0.82,
) -> Optional[str]:
    """
    Смена режима: exact match; при nlu_enabled — fuzzy fallback (difflib).
    """
    from center_voice_agent.modes.nlu import resolve_mode_switch

    return resolve_mode_switch(
        user_text,
        commands=commands,
        voice_aliases=voice_aliases,
        nlu_enabled=nlu_enabled,
        nlu_threshold=nlu_threshold,
    )
