"""
Plan B: модели без нативного tool-calling иногда пишут JSON в тексте ответа.

Поддерживаемые форматы (в тексте или в ```json ... ```):
  {"tool": "memory_upsert", "args": {...}}
  {"name": "memory_upsert", "args": {...}}
  [{"tool": "...", "args": {...}}, ...]
"""

from __future__ import annotations

import json
import re
from typing import Any

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
    """Вырезает подстроки {...} с учётом вложенных скобок."""
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


def parse_text_tool_calls(text: str) -> list[dict[str, Any]]:
    """Извлекает вызовы инструментов из текста модели."""
    if not text or not text.strip():
        return []
    found: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _add_from_payload(payload: Any) -> None:
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
            key = json.dumps(norm, sort_keys=True, ensure_ascii=False)
            if key in seen:
                continue
            seen.add(key)
            found.append(norm)

    for m in _JSON_FENCE.finditer(text):
        try:
            _add_from_payload(json.loads(m.group(1)))
        except json.JSONDecodeError:
            continue

    for chunk in _iter_balanced_json_objects(text):
        try:
            payload = json.loads(chunk)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict) and _looks_like_tool_call(payload):
            _add_from_payload(payload)
        elif isinstance(payload, list):
            _add_from_payload(payload)

    return found
