from __future__ import annotations

from fastapi import FastAPI

from center_voice_agent.api.routes.turn import router as turn_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="center_voice_agent",
        description="HTTP API голосового наставника (один ход диалога)",
        version="0.1.0",
    )
    app.include_router(turn_router)
    return app


app = create_app()
