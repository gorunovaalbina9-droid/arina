import logging
from pathlib import Path

import structlog

from center_voice_agent.logging_setup import configure_logging, setup_logging
from center_voice_agent.settings import Settings


def test_setup_logging_writes_file(tmp_path: Path) -> None:
    structlog.reset_defaults()
    log_path = tmp_path / "agent.log"
    setup_logging(json_logs=True, level="INFO", log_file=log_path)
    structlog.get_logger("test").info("hello_log", cid="x")
    assert log_path.is_file()
    assert "hello_log" in log_path.read_text(encoding="utf-8")


def test_configure_logging_uses_agent_yaml_path() -> None:
    """При project_root=пакет пишет в logs/agent.log из config/agent.yaml."""
    structlog.reset_defaults()
    root = Path(__file__).resolve().parents[1]
    log_path = root / "logs" / "agent.log"
    if log_path.exists():
        log_path.unlink()
    settings = Settings(project_root=root, database_url="sqlite+aiosqlite:///:memory:")
    configure_logging(settings)
    structlog.get_logger("test").info("yaml_log_probe")
    assert log_path.is_file()
    text = log_path.read_text(encoding="utf-8")
    assert "yaml_log_probe" in text
    log_path.unlink(missing_ok=True)
