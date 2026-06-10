"""Обратная совместимость: re-export из moderation_engine."""

from center_voice_agent.security.moderation_engine import (  # noqa: F401
    ModerationEngine,
    check_input_blocked,
    check_output_blocked,
    normalize_for_moderation,
)
