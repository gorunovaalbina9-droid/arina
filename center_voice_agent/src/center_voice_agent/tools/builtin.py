"""Обратная совместимость: web_search регистрируется через tools.factory.make_web_search_tool."""

from center_voice_agent.tools.factory import make_web_search_tool

__all__ = ["make_web_search_tool"]
