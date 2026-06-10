import pytest

pytest.importorskip("fastapi")

from center_voice_agent.api.app import create_app
from fastapi.testclient import TestClient


def test_info_endpoint() -> None:
    client = TestClient(create_app())
    r = client.get("/info")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "center-voice-agent"
    assert "POST /turn" in data["api"]["turn"]
    assert "stt_tts_voice_assistant" in data["scope"]["out_of_repo"]
