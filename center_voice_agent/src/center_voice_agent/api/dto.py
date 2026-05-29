from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


class TurnRequest(BaseModel):
    session_id: str = Field(..., min_length=1)
    child_profile_id: str = Field(..., min_length=1)
    user_text: str = Field(..., min_length=1)
    age_band: Optional[str] = None
    scenario_id: Optional[str] = None


class TurnResponse(BaseModel):
    text: str
    reply_spoken: str
    mode_id: str
    scenario_id: Optional[str] = None
    scenario_node_id: Optional[str] = None
    tool_calls: list[dict[str, Any]] = Field(default_factory=list)
