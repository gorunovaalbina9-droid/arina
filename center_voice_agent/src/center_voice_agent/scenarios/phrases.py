from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class ScenarioCommandsFile(BaseModel):
    """Фразы сброса сценария (подстрока в нормализованном тексте пользователя)."""

    reset_phrases: list[str] = Field(default_factory=list)


def load_scenario_commands(path: Path) -> ScenarioCommandsFile:
    if not path.is_file():
        return ScenarioCommandsFile()
    raw = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if raw is None:
        return ScenarioCommandsFile()
    if not isinstance(raw, dict):
        raise ValueError(f"Ожидался объект YAML в {path}")
    return ScenarioCommandsFile.model_validate(raw)


def _norm(s: str) -> str:
    return " ".join(s.lower().split())


def try_parse_scenario_reset(user_text: str, *, commands: ScenarioCommandsFile) -> bool:
    """True, если пользователь явно просит сбросить сценарий."""
    u = _norm(user_text)
    if not u:
        return False
    phrases = [_norm(p) for p in commands.reset_phrases if _norm(p)]
    phrases.sort(key=len, reverse=True)
    for p in phrases:
        if len(p) < 2:
            continue
        if p == u or p in u:
            return True
    return False
