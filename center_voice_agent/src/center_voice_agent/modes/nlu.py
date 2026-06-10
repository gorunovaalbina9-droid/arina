"""NLU смены режима: exact match + fuzzy (difflib) вместо голого substring."""

from __future__ import annotations

import difflib
from typing import Optional

from center_voice_agent.modes.commands import (
    ModeCommandsFile,
    _norm,
    _phrase_matches_user,
)


def _command_pairs(
    commands: ModeCommandsFile,
    voice_aliases: dict[str, list[str]],
) -> list[tuple[str, str]]:
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
    return pairs


def _exact_mode_switch(user_n: str, pairs: list[tuple[str, str]]) -> Optional[str]:
    for phrase, mode_id in pairs:
        if _phrase_matches_user(user_n, phrase):
            return mode_id
    return None


def _fuzzy_mode_switch(
    user_n: str,
    pairs: list[tuple[str, str]],
    *,
    threshold: float,
) -> Optional[str]:
    """Fuzzy только для коротких реплик-команд (≤12 слов)."""
    if len(user_n.split()) > 12:
        return None
    phrases = [p for p, _ in pairs]
    if not phrases:
        return None
    matches = difflib.get_close_matches(user_n, phrases, n=1, cutoff=threshold)
    if not matches:
        return None
    hit = matches[0]
    for phrase, mode_id in pairs:
        if phrase == hit:
            return mode_id
    return None


def resolve_mode_switch(
    user_text: str,
    *,
    commands: ModeCommandsFile,
    voice_aliases: dict[str, list[str]],
    nlu_enabled: bool = True,
    nlu_threshold: float = 0.82,
) -> Optional[str]:
    user_n = _norm(user_text)
    if not user_n:
        return None
    pairs = _command_pairs(commands, voice_aliases)
    exact = _exact_mode_switch(user_n, pairs)
    if exact is not None:
        return exact
    if not nlu_enabled:
        return None
    return _fuzzy_mode_switch(user_n, pairs, threshold=nlu_threshold)
