from __future__ import annotations

from fastapi import FastAPI

from center_voice_agent.api.routes.admin import router as admin_router
from center_voice_agent.api.routes.info import router as info_router
from center_voice_agent.api.routes.turn import router as turn_router
from center_voice_agent.api.routes.ws import router as ws_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="center_voice_agent",
        description="HTTP/WebSocket API голосового наставника",
        version="0.1.0",
    )
    app.include_router(turn_router)
    app.include_router(ws_router)
    app.include_router(admin_router)
    app.include_router(info_router)
    return app


app = create_app()
