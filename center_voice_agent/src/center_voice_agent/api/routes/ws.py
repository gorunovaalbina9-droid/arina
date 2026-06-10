"""WebSocket API: потоковый диалог с тем же SessionCoordinator."""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from center_voice_agent.composition.runtime import get_process_container
from center_voice_agent.integration.bridge import AgentSession

router = APIRouter()


@router.websocket("/ws/session")
async def ws_session(websocket: WebSocket) -> None:
    await websocket.accept()
    container = await get_process_container()
    session: Optional[AgentSession] = None
    try:
        while True:
            payload: dict[str, Any] = await websocket.receive_json()
            msg_type = str(payload.get("type") or "turn")
            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})
                continue
            if msg_type == "close":
                if session is not None:
                    await session.close()
                    session = None
                await websocket.send_json({"type": "closed"})
                continue

            user_text = str(payload.get("user_text") or "").strip()
            if not user_text:
                await websocket.send_json({"type": "error", "message": "user_text required"})
                continue

            session_id = str(payload.get("session_id") or "ws-default")
            child_profile_id = str(payload.get("child_profile_id") or "child-default")
            age_band = payload.get("age_band")
            scenario_id = payload.get("scenario_id")
            offline_llm = bool(payload.get("offline_llm", False))

            if session is None or session.session_id != session_id:
                if session is not None:
                    await session.close()
                session = await AgentSession.open_with_container(
                    container,
                    session_id=session_id,
                    child_profile_id=child_profile_id,
                    age_band=str(age_band) if age_band else None,
                    scenario_id=str(scenario_id) if scenario_id else None,
                    offline_llm=offline_llm,
                )

            result = await session.ask(user_text)
            spoken = session.spoken_text(result)
            await websocket.send_json(
                {
                    "type": "turn",
                    "text": result.text,
                    "reply_spoken": spoken,
                    "mode_id": result.mode_id,
                    "scenario_id": result.scenario_id,
                    "scenario_node_id": result.scenario_node_id,
                    "mode_changed": result.mode_changed,
                }
            )
    except WebSocketDisconnect:
        if session is not None:
            await session.close()
