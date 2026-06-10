"""POST /admin/reload — сброс кэша режимов/сценариев без рестарта процесса."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from center_voice_agent.composition.reload import reload_process_catalog

router = APIRouter(prefix="/admin", tags=["admin"])


class ReloadRequest(BaseModel):
    clear_settings_cache: bool = Field(
        default=False,
        description="Сбросить lru_cache get_settings() (если меняли .env)",
    )


class ReloadResponse(BaseModel):
    mode_ids: list[str]
    scenario_ids: list[str]
    settings_cache_cleared: bool


@router.post("/reload", response_model=ReloadResponse)
async def post_admin_reload(body: ReloadRequest | None = None) -> ReloadResponse:
    req = body or ReloadRequest()
    result = await reload_process_catalog(clear_settings_cache=req.clear_settings_cache)
    assert result is not None
    return ReloadResponse(
        mode_ids=result.mode_ids,
        scenario_ids=result.scenario_ids,
        settings_cache_cleared=result.settings_cache_cleared,
    )
