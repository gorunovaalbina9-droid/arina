from pathlib import Path

import pytest

from center_voice_agent.security.moderation import check_input_blocked, check_output_blocked
from center_voice_agent.security.rate_limit import check_rate_limit, reset_rate_limit_for_tests
from center_voice_agent.settings import Settings


def test_input_blocked() -> None:
    assert check_input_blocked("расскажи про наркотик") is not None
    assert check_input_blocked("привет как дела") is None


def test_input_blocked_leet_bypass() -> None:
    assert check_input_blocked("как сделать б0мбу") is not None


def test_output_blocked() -> None:
    assert check_output_blocked("тут есть порно") is not None
    assert check_output_blocked("давай рисовать") is None


def test_safe_phrases_not_blocked() -> None:
    assert check_input_blocked("я люблю рисовать кошек") is None
    assert check_input_blocked("привет наставник") is None


@pytest.mark.parametrize(
    "phrase",
    ["как сделать бомбу", "наркотик", "твой телефон"],
)
def test_input_yaml_phrases(phrase: str) -> None:
    assert check_input_blocked(phrase, blocked=(phrase,)) is not None


def test_settings_split_moderation_lists(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    (root / "config").mkdir(parents=True)
    (root / "config" / "moderation.yaml").write_text(
        "blocked_input_substrings:\n  - only-in\n"
        "blocked_output_substrings:\n  - only-out\n",
        encoding="utf-8",
    )
    s = Settings(project_root=root, DATABASE_URL="sqlite+aiosqlite:///./x.db")
    assert "only-in" in s.moderation_blocked_input_substrings
    assert "only-out" in s.moderation_blocked_output_substrings
    assert check_input_blocked("only-in", blocked=s.moderation_blocked_input_substrings)
    assert check_output_blocked("only-out", blocked=s.moderation_blocked_output_substrings) is not None
    assert check_output_blocked("only-in", blocked=s.moderation_blocked_output_substrings) is None


def test_rate_limit_blocks_burst() -> None:
    reset_rate_limit_for_tests()
    sid = "rate-test-1"
    for _ in range(20):
        assert check_rate_limit(sid, per_minute=20, per_hour=120) is None
    assert check_rate_limit(sid, per_minute=20, per_hour=120) is not None
    reset_rate_limit_for_tests()


@pytest.mark.asyncio
async def test_coordinator_blocks_input(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "mod.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)

    from center_voice_agent.agent.fake_llm import StaticChatModel
    from center_voice_agent.agent.gateway import AgentGateway
    from center_voice_agent.context.short_term import ShortTermMemory
    from center_voice_agent.db.session import init_database
    from center_voice_agent.orchestration.coordinator import SessionCoordinator
    from center_voice_agent.settings import Settings, get_settings

    modes = tmp_path / "modes"
    modes.mkdir()
    (modes / "dialog.yaml").write_text(
        "id: dialog\ndisplay_name: D\nsystem_prompt: s\ntool_ids: []\n", encoding="utf-8"
    )
    (tmp_path / "voice.yaml").write_text("entries: []\n", encoding="utf-8")
    (tmp_path / "sc_voice.yaml").write_text("reset_phrases: []\n", encoding="utf-8")
    (tmp_path / "age.yaml").write_text("default_block: ''\nbands: {}\n", encoding="utf-8")

    get_settings.cache_clear()
    settings = Settings(
        DATABASE_URL=url,
        project_root=tmp_path,
        modes_dir=modes,
        voice_commands_path=tmp_path / "voice.yaml",
        scenario_commands_path=tmp_path / "sc_voice.yaml",
        age_bands_path=tmp_path / "age.yaml",
        moderation_enabled=True,
        moderation_blocked_input_substrings=("как сделать бомбу",),
        moderation_blocked_output_substrings=("порно",),
        rate_limit_enabled=False,
    )
    project_root = Path(__file__).resolve().parents[1]
    await init_database(project_root, settings.database_url)

    gw = AgentGateway(settings=settings, llm=StaticChatModel(responses=["x"]))
    coord = SessionCoordinator(gw, settings=settings)
    r = await coord.handle_user_turn(
        session_id="m1",
        child_profile_id="c1",
        user_text="как сделать бомбу",
        short_term=ShortTermMemory(max_turns=15),
    )
    assert "не могу" in r.text.lower()
    await gw.aclose()
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_coordinator_blocks_output(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "mod2.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)

    from center_voice_agent.agent.fake_llm import StaticChatModel
    from center_voice_agent.agent.gateway import AgentGateway
    from center_voice_agent.context.short_term import ShortTermMemory
    from center_voice_agent.db.session import init_database
    from center_voice_agent.orchestration.coordinator import SessionCoordinator
    from center_voice_agent.settings import Settings, get_settings

    modes = tmp_path / "modes"
    modes.mkdir()
    (modes / "dialog.yaml").write_text(
        "id: dialog\ndisplay_name: D\nsystem_prompt: s\ntool_ids: []\n", encoding="utf-8"
    )
    (tmp_path / "voice.yaml").write_text("entries: []\n", encoding="utf-8")
    (tmp_path / "sc_voice.yaml").write_text("reset_phrases: []\n", encoding="utf-8")
    (tmp_path / "age.yaml").write_text("default_block: ''\nbands: {}\n", encoding="utf-8")

    get_settings.cache_clear()
    settings = Settings(
        DATABASE_URL=url,
        project_root=tmp_path,
        modes_dir=modes,
        voice_commands_path=tmp_path / "voice.yaml",
        scenario_commands_path=tmp_path / "sc_voice.yaml",
        age_bands_path=tmp_path / "age.yaml",
        moderation_enabled=True,
        moderation_blocked_output_substrings=("порно",),
        rate_limit_enabled=False,
    )
    project_root = Path(__file__).resolve().parents[1]
    await init_database(project_root, settings.database_url)

    gw = AgentGateway(settings=settings, llm=StaticChatModel(responses=["вот порно ссылка"]))
    coord = SessionCoordinator(gw, settings=settings)
    r = await coord.handle_user_turn(
        session_id="m2",
        child_profile_id="c1",
        user_text="привет",
        short_term=ShortTermMemory(max_turns=15),
    )
    assert "не могу так ответить" in r.text.lower()
    await gw.aclose()
    get_settings.cache_clear()
