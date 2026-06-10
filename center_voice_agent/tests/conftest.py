import pytest

from center_voice_agent.agent.turn_langgraph import reset_compiled_graph_for_tests
from center_voice_agent.composition.runtime import reset_process_runtime_for_tests
from center_voice_agent.security.rate_limit import reset_rate_limit_for_tests
from center_voice_agent.voice.session_manager import reset_voice_sessions_for_tests
from center_voice_agent.settings import get_settings


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture(autouse=True)
def _reset_process_globals() -> None:
    reset_rate_limit_for_tests()
    reset_compiled_graph_for_tests()
    reset_process_runtime_for_tests()
    reset_voice_sessions_for_tests()
    yield
    reset_rate_limit_for_tests()
    reset_compiled_graph_for_tests()
    reset_process_runtime_for_tests()
    reset_voice_sessions_for_tests()
