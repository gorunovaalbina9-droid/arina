from __future__ import annotations

from typing import Optional, Sequence

# Запасной минимум, если config/moderation.yaml отсутствует
_FALLBACK_BLOCKED = (
    "как сделать бомбу",
    "как убить",
    "порно",
    "наркотик",
)


def check_input_blocked(
    user_text: str,
    *,
    blocked: Sequence[str] = (),
) -> Optional[str]:
    """None если ок, иначе причина блокировки."""
    low = user_text.lower()
    phrases = tuple(blocked) if blocked else _FALLBACK_BLOCKED
    for phrase in phrases:
        if phrase in low:
            return f"blocked_phrase:{phrase}"
    return None


def check_output_blocked(
    text: str,
    *,
    blocked: Sequence[str] = (),
) -> Optional[str]:
    low = text.lower()
    phrases = tuple(blocked) if blocked else _FALLBACK_BLOCKED
    for phrase in phrases:
        if phrase in low:
            return f"blocked_output:{phrase}"
    return None
