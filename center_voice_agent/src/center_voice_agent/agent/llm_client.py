"""Фабрика LLM из Settings через LLMProvider."""

from __future__ import annotations

from typing import Any, Optional

from langchain_core.language_models import BaseChatModel

from center_voice_agent.agent.llm_provider import LLMProvider, get_llm_provider
from center_voice_agent.settings import Settings


def build_chat_model(
    settings: Settings,
    mode_llm_params: dict[str, Any],
    *,
    override: Optional[BaseChatModel] = None,
    provider: Optional[LLMProvider] = None,
) -> BaseChatModel:
    p = provider or get_llm_provider()
    return p.build_chat_model(settings, mode_llm_params, override=override)
