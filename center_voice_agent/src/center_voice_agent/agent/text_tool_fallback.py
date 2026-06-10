"""
Plan B: модели без нативного tool-calling иногда пишут JSON в тексте ответа.

Режимы (Settings.text_tool_fallback_mode):
- off — не парсить
- fenced_only — только ```json ... ``` (меньше ложных срабатываний)
- strict — fenced + целиком JSON-сообщение; tool должен быть в allowed_tools
"""

from __future__ import annotations

import json
import re
from typing import Any, Literal, Optional, Sequence

TextToolFallbackMode = Literal["off", "fenced_only", "strict", "permissive"]

_JSON_FENCE = re.compile(r"```(?:json)?\s*(\{[\s\S]*?\}|\[[\s\S]*?\])\s*```", re.IGNORECASE)


def _normalize_call(raw: dict[str, Any]) -> dict[str, Any] | None:
    name = raw.get("tool") or raw.get("name")
    if not name or not isinstance(name, str):
        return None
    args = raw.get("args") or raw.get("arguments") or {}
    if not isinstance(args, dict):
        return None
    return {"name": name.strip(), "args": args}


def _looks_like_tool_call(raw: dict[str, Any]) -> bool:
    return _normalize_call(raw) is not None


def _iter_balanced_json_objects(text: str) -> list[str]:
    chunks: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] != "{":
            i += 1
            continue
        depth = 0
        for j in range(i, n):
            ch = text[j]
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    chunks.append(text[i : j + 1])
                    i = j + 1
                    break
        else:
            i += 1
    return chunks


def _add_from_payload(
    payload: Any,
    *,
    found: list[dict[str, Any]],
    seen: set[str],
    allowed_tools: Optional[frozenset[str]],
) -> None:
    items: list[dict[str, Any]]
    if isinstance(payload, list):
        items = [x for x in payload if isinstance(x, dict)]
    elif isinstance(payload, dict):
        items = [payload]
    else:
        return
    for raw in items:
        norm = _normalize_call(raw)
        if norm is None:
            continue
        if allowed_tools is not None and norm["name"] not in allowed_tools:
            continue
        key = json.dumps(norm, sort_keys=True, ensure_ascii=False)
        if key in seen:
            continue
        seen.add(key)
        found.append(norm)


def parse_text_tool_calls(
    text: str,
    *,
    mode: TextToolFallbackMode = "fenced_only",
    allowed_tools: Optional[Sequence[str]] = None,
) -> list[dict[str, Any]]:
    """Извлекает вызовы инструментов из текста модели."""
    if mode == "off" or not text or not text.strip():
        return []

    allowed = frozenset(allowed_tools) if allowed_tools is not None else None
    found: list[dict[str, Any]] = []
    seen: set[str] = set()

    for m in _JSON_FENCE.finditer(text):
        try:
            _add_from_payload(
                json.loads(m.group(1)),
                found=found,
                seen=seen,
                allowed_tools=allowed,
            )
        except json.JSONDecodeError:
            continue

    if mode in ("strict", "permissive"):
        stripped = text.strip()
        if stripped.startswith("{") or stripped.startswith("["):
            try:
                payload = json.loads(stripped)
                if isinstance(payload, dict) and _looks_like_tool_call(payload):
                    _add_from_payload(payload, found=found, seen=seen, allowed_tools=allowed)
                elif isinstance(payload, list):
                    _add_from_payload(payload, found=found, seen=seen, allowed_tools=allowed)
            except json.JSONDecodeError:
                pass

    if mode == "permissive":
        for chunk in _iter_balanced_json_objects(text):
            try:
                payload = json.loads(chunk)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict) and _looks_like_tool_call(payload):
                _add_from_payload(payload, found=found, seen=seen, allowed_tools=allowed)
            elif isinstance(payload, list):
                _add_from_payload(payload, found=found, seen=seen, allowed_tools=allowed)

    return found
