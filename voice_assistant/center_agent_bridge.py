"""
Мост voice_assistant → center_voice_agent (офлайн: fake LLM через env агента).

USE_CENTER_AGENT=true — GUI вызывает ask_center_agent() вместо старого контура.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _agent_src_on_path() -> Path:
    root = Path(__file__).resolve().parents[1] / "center_voice_agent" / "src"
    if not root.is_dir():
        raise FileNotFoundError(f"Нет пакета агента: {root}")
    s = str(root)
    if s not in sys.path:
        sys.path.insert(0, s)
    return root


def use_center_agent() -> bool:
    return os.environ.get("USE_CENTER_AGENT", "").strip().lower() in ("1", "true", "yes")


def _use_offline_llm() -> bool:
    """Без CENTER_AGENT_LIVE=true — fake LLM (пилот без API)."""
    return os.environ.get("CENTER_AGENT_LIVE", "").strip().lower() not in ("1", "true", "yes")


def ask_center_agent(
    user_text: str,
    *,
    session_id: str,
    child_profile_id: str = "child-default",
    age_band: str = "5-6",
    scenario_id: str | None = None,
) -> str:
    _agent_src_on_path()
    from center_voice_agent.integration.bridge import ask_once_sync

    return ask_once_sync(
        user_text,
        session_id=session_id,
        child_profile_id=child_profile_id,
        age_band=age_band,
        scenario_id=scenario_id,
        offline_llm=_use_offline_llm(),
    )
