"""
Голосовой контур агента (текст in/out для STT/TTS снаружи).

Для GUI: VoiceSessionManager — одна сессия на комнату, общий AppContainer.
"""

from center_voice_agent.voice.session_manager import (
    VoiceSessionManager,
    ask_voice_sync,
    get_voice_session_manager,
    reset_voice_sessions_for_tests,
)

__all__ = [
    "VoiceSessionManager",
    "ask_voice_sync",
    "get_voice_session_manager",
    "reset_voice_sessions_for_tests",
]
