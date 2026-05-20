"""Вызов агента из других приложений (голосовой помощник, боты)."""

from center_voice_agent.integration.bridge import AgentSession, ask_once

__all__ = ["AgentSession", "ask_once"]
