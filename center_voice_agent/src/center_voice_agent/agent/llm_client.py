"""Фабрика LLM из Settings (без прямого доступа к env)."""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from center_voice_agent.settings import Settings


def build_chat_model(
    settings: Settings,
    mode_llm_params: dict[str, Any],
    *,
    override: Optional[BaseChatModel] = None,
) -> BaseChatModel:
    if override is not None:
        return override
    if not settings.llm_api_key:
        raise RuntimeError(
            "LLM_API_KEY не задан. Для демо передайте llm=StaticChatModel в AgentGateway."
        )
    return ChatOpenAI(
        model=settings.llm_model,
        temperature=float(mode_llm_params.get("temperature", 0.5)),
        max_tokens=int(mode_llm_params.get("max_tokens", 512)),
        base_url=settings.llm_base_url,
        api_key=settings.llm_api_key,
    )
