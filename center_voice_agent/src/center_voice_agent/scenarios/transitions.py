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


def _strip_edge_punct(word: str) -> str:
    return word.strip(".,!?;:…\"'«»()[]")


def _text_matches_keys(user_text: str, keys: tuple[str, ...]) -> bool:
    low = _norm_text(user_text)
    if not low:
        return False
    tokens = [_strip_edge_punct(w) for w in low.split()]
    token_set = {t for t in tokens if t}
    for k in keys:
        if not k:
            continue
        if k == low:
            return True
        if k in token_set:
            return True
        if low.startswith(k + " ") or low.startswith(k + ",") or low.startswith(k + "."):
            return True
        if f" {k} " in f" {low} ":
            return True
    return False


def parse_when(when: str) -> tuple[str, str | tuple[str, ...]]:
    """
    Возвращает (kind, payload):
    - ("always", "")
    - ("event", "turn_complete")
    - ("keyword", ("да", "хорошо"))
    - ("mood", ("рад", "хорошо"))  — смысловые группы (после хода)
    """
    w = (when or "").strip()
    if w == "always":
        return "always", ""
    if w.lower().startswith("keyword:"):
        part = w.split(":", 1)[1]
        keys = tuple(k.strip().lower() for k in part.split(",") if k.strip())
        return "keyword", keys
    if w.lower().startswith("mood:"):
        part = w.split(":", 1)[1]
        keys = tuple(k.strip().lower() for k in part.split(",") if k.strip())
        return "mood", keys
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
    if kind in ("keyword", "mood"):
        if not isinstance(payload, tuple) or not payload:
            return False
        return _text_matches_keys(user_text, payload)
    ev = normalize_transition_event(event)
    return payload == ev
