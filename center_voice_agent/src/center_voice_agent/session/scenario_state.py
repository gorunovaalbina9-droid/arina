"""Сериализация state_json: сценарий, переменные, метаданные сессии."""

from __future__ import annotations

import json
from typing import Any, Optional


def load_state(raw: str) -> dict[str, Any]:
    if not raw or not str(raw).strip():
        return {"version": 2}
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return {"version": 2}
    if not isinstance(data, dict):
        return {"version": 2}
    if "version" not in data:
        data["version"] = 2
    return data


def dump_state(state: dict[str, Any]) -> str:
    return json.dumps(state, ensure_ascii=False)


def get_scenario_bucket(state: dict[str, Any]) -> dict[str, Any]:
    sc = state.get("scenario")
    if isinstance(sc, dict):
        return sc
    return {}


def scenario_vars(state: dict[str, Any]) -> dict[str, Any]:
    bucket = get_scenario_bucket(state)
    vars_raw = bucket.get("vars")
    if isinstance(vars_raw, dict):
        return dict(vars_raw)
    return {}


def merge_scenario_state(
    state: dict[str, Any],
    *,
    scenario_id: Optional[str],
    node_id: Optional[str],
    vars_patch: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    out = dict(state)
    out["version"] = 2
    bucket = dict(get_scenario_bucket(out))
    if scenario_id is not None:
        bucket["id"] = scenario_id
    if node_id is not None:
        bucket["node"] = node_id
    if vars_patch:
        merged = scenario_vars(out)
        merged.update(vars_patch)
        bucket["vars"] = merged
    out["scenario"] = bucket
    return out
