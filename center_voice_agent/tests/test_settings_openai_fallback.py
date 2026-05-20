from pathlib import Path

import pytest

from center_voice_agent.settings import Settings, get_settings


def test_openai_key_from_sibling_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    center = tmp_path / "center_voice_agent"
    center.mkdir()
    (center / ".env").write_text(
        "LLM_API_KEY=replace_me\nLLM_BASE_URL=https://api.example.com/v1\nLLM_MODEL=your-finetuned-model\n",
        encoding="utf-8",
    )
    va = tmp_path / "voice_assistant"
    va.mkdir()
    (va / ".env").write_text("OPENAI_API_KEY=sk-test-from-sibling\n", encoding="utf-8")
    monkeypatch.chdir(center)

    s = Settings(project_root=center)
    assert s.llm_api_key == "sk-test-from-sibling"
    assert s.llm_base_url == "https://api.openai.com/v1"
    assert s.llm_model == "gpt-4o-mini"
    get_settings.cache_clear()
