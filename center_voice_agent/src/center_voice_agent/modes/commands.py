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


def try_parse_mode_switch(
    user_text: str,
    *,
    commands: ModeCommandsFile,
    voice_aliases: dict[str, list[str]],
) -> Optional[str]:
    """
    Определяет, хочет ли пользователь сменить режим по фразе.
    voice_aliases: mode_id -> список фраз из YAML режимов.
    """
    user_n = _norm(user_text)
    if not user_n:
        return None

    pairs: list[tuple[str, str]] = []
    for e in commands.entries:
        for ph in e.phrases:
            p = _norm(ph)
            if p:
                pairs.append((p, e.mode_id))
    for mid, phrases in voice_aliases.items():
        for ph in phrases:
            p = _norm(ph)
            if p:
                pairs.append((p, mid))

    pairs.sort(key=lambda x: len(x[0]), reverse=True)
    for phrase, mode_id in pairs:
        if len(phrase) < 2:
            continue
        if phrase == user_n or phrase in user_n:
            return mode_id
    return None
