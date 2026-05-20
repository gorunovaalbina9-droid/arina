from __future__ import annotations

from typing import Optional

# Минимальный список для пилота; расширяется конфигом позже.
_DEFAULT_BLOCKED_SUBSTRINGS = (
    "как сделать бомбу",
    "как убить",
    "порно",
    "наркотик",
)


def check_input_blocked(user_text: str, *, extra: tuple[str, ...] = ()) -> Optional[str]:
    """None если ок, иначе причина блокировки."""
    low = user_text.lower()
    for phrase in (*_DEFAULT_BLOCKED_SUBSTRINGS, *extra):
        if phrase in low:
            return f"blocked_phrase:{phrase}"
    return None


def check_output_blocked(text: str) -> Optional[str]:
    low = text.lower()
    for phrase in _DEFAULT_BLOCKED_SUBSTRINGS:
        if phrase in low:
            return f"blocked_output:{phrase}"
    return None
