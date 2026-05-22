"""Разбор поля when в рёбрах сценария."""

from __future__ import annotations


def normalize_transition_event(when: str) -> str:
    """Единое имя события для сопоставления рёбер."""
    w = (when or "").strip()
    if w == "user_spoke":
        return "turn_complete"
    return w


def _norm_text(s: str) -> str:
    return " ".join((s or "").lower().split())


def parse_when(when: str) -> tuple[str, str | tuple[str, ...]]:
    """
    Возвращает (kind, payload):
    - ("always", "")
    - ("event", "turn_complete")
    - ("keyword", ("да", "хорошо"))
    """
    w = (when or "").strip()
    if w == "always":
        return "always", ""
    if w.lower().startswith("keyword:"):
        part = w.split(":", 1)[1]
        keys = tuple(k.strip().lower() for k in part.split(",") if k.strip())
        return "keyword", keys
    return "event", normalize_transition_event(w)


def transition_matches(
    when: str,
    *,
    event: str,
    user_text: str = "",
) -> bool:
    kind, payload = parse_when(when)
    if kind == "always":
        return True
    if kind == "keyword":
        if not isinstance(payload, tuple) or not payload:
            return False
        low = _norm_text(user_text)
        return any(k in low for k in payload)
    ev = normalize_transition_event(event)
    return payload == ev
