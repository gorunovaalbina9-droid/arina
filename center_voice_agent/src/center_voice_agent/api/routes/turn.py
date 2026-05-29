from __future__ import annotations

from fastapi import APIRouter

from center_voice_agent.api.dto import TurnRequest, TurnResponse
from center_voice_agent.composition.runtime import get_process_container
from center_voice_agent.integration.bridge import AgentSession

router = APIRouter()


@router.post("/turn", response_model=TurnResponse)
async def post_turn(body: TurnRequest) -> TurnResponse:
    container = await get_process_container()
    session = await AgentSession.open_with_container(
        container,
        session_id=body.session_id,
        child_profile_id=body.child_profile_id,
        age_band=body.age_band,
        scenario_id=body.scenario_id,
    )
    result = await session.ask(body.user_text)
    spoken = session.spoken_text(result)
    return TurnResponse(
        text=result.text,
        reply_spoken=spoken,
        mode_id=result.mode_id,
        scenario_id=result.scenario_id,
        scenario_node_id=result.scenario_node_id,
        tool_calls=result.tool_calls,
    )


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
