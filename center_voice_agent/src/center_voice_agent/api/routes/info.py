from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/info")
async def get_info() -> dict:
    return {
        "name": "center-voice-agent",
        "version": "0.1.0",
        "api": {
            "turn": "POST /turn",
            "websocket": "WS /ws/session",
            "admin_reload": "POST /admin/reload",
            "health": "GET /health",
        },
        "scope": {
            "in_repo": [
                "session_coordinator",
                "http_turn_and_websocket",
                "mode_nlu",
                "tool_registry_and_mcp_stdio",
                "rag_search_keyword_stub",
                "postgresql_sql_migrations_and_alembic",
            ],
            "out_of_repo": [
                "stt_tts_voice_assistant",
                "web_parent_cabinet",
                "vector_rag_production",
            ],
        },
        "docs": [
            "docs/API.md",
            "docs/SCOPE.md",
            "docs/VOICE_INTEGRATION.md",
            "docs/pilot/PILOT_READY.md",
        ],
    }
