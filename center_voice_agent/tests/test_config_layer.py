"""Конфиг: env только в settings, YAML подхватывается."""

from pathlib import Path

from center_voice_agent.settings import Settings


def test_agent_yaml_overrides_limits(tmp_path: Path) -> None:
    root = tmp_path / "proj"
    (root / "config").mkdir(parents=True)
    (root / "config" / "agent.yaml").write_text(
        "short_term_max_messages: 7\nmemory_prefetch_limit: 3\n",
        encoding="utf-8",
    )
    (root / "config" / "moderation.yaml").write_text(
        'blocked_substrings:\n  - "тест-блок"\n',
        encoding="utf-8",
    )
    s = Settings(
        _env_file=str(root / ".env"),
        project_root=root,
        DATABASE_URL="sqlite+aiosqlite:///./data/x.db",
    )
    assert s.short_term_max_messages == 7
    assert s.prefetch_memory_limit == 3
    assert "тест-блок" in s.moderation_blocked_substrings


def test_no_os_environ_in_package_modules() -> None:
    import center_voice_agent.settings as settings_mod

    src = Path(settings_mod.__file__).resolve().parent
    for path in src.rglob("*.py"):
        if path.name == "settings.py":
            continue
        text = path.read_text(encoding="utf-8")
        assert "os.environ" not in text, path.name
        assert "os.getenv" not in text, path.name
        assert "getenv(" not in text, path.name
