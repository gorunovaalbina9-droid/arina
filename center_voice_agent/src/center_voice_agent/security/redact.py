"""Redact ПДн в аргументах tools и API-ответах."""

from __future__ import annotations

from typing import Any, Mapping, Optional, Sequence

from center_voice_agent.logging_setup import text_fingerprint

_SENSITIVE_ARG_KEYS = frozenset(
    {
        "value_text",
        "query",
        "text",
        "content",
        "note",
        "summary",
        "message",
    }
)


def redact_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        if not value.strip():
            return value
        return f"<redacted fp={text_fingerprint(value)} len={len(value)}>"
    if isinstance(value, Mapping):
        return {k: redact_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [redact_value(v) for v in value]
    return value


def redact_tool_args(args: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for key, val in args.items():
        if key in _SENSITIVE_ARG_KEYS:
            out[key] = redact_value(val)
        elif key == "child_profile_id":
            out[key] = val
        else:
            out[key] = redact_value(val) if isinstance(val, str) and len(val) > 80 else val
    return out


def redact_tool_call(call: Mapping[str, Any], *, redact_args: bool = True) -> dict[str, Any]:
    out = dict(call)
    if redact_args and "args" in out and isinstance(out["args"], Mapping):
        out["args"] = redact_tool_args(out["args"])
    return out


def redact_tool_calls(
    calls: Sequence[Mapping[str, Any]],
    *,
    redact_args: bool = True,
) -> list[dict[str, Any]]:
    if not redact_args:
        return [dict(c) for c in calls]
    return [redact_tool_call(c, redact_args=True) for c in calls]
