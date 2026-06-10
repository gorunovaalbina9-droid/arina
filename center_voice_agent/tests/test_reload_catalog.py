"""Тест reload каталога после publish."""

from __future__ import annotations

from pathlib import Path

import pytest

from center_voice_agent.composition.container import AppContainer
from center_voice_agent.composition.reload import reload_catalog
from center_voice_agent.scenarios.loader import _scan_scenario_files


@pytest.mark.asyncio
async def test_reload_catalog_clears_scenario_scan(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    db = tmp_path / "r.db"
    url = f"sqlite+aiosqlite:///{db.as_posix().replace(chr(92), '/')}"
    monkeypatch.setenv("DATABASE_URL", url)

    from center_voice_agent.db.session import init_database
    from center_voice_agent.settings import Settings, get_settings

    modes = tmp_path / "modes"
    modes.mkdir()
    (modes / "dialog.yaml").write_text(
        "id: dialog\ndisplay_name: D\nsystem_prompt: s\ntool_ids: []\n", encoding="utf-8"
    )
    scen = tmp_path / "scenarios"
    scen.mkdir()
    (scen / "demo.yaml").write_text(
        "id: demo\nversion: 1\nentry: start\nnodes:\n  start:\n    title: S\n    transitions: []\n",
        encoding="utf-8",
    )
    (tmp_path / "voice.yaml").write_text("entries: []\n", encoding="utf-8")
    (tmp_path / "sc_voice.yaml").write_text("reset_phrases: []\n", encoding="utf-8")
    (tmp_path / "age.yaml").write_text("default_block: ''\nbands: {}\n", encoding="utf-8")

    get_settings.cache_clear()
    settings = Settings(
        DATABASE_URL=url,
        project_root=tmp_path,
        modes_dir=modes,
        scenarios_dir=scen,
        voice_commands_path=tmp_path / "voice.yaml",
        scenario_commands_path=tmp_path / "sc_voice.yaml",
        age_bands_path=tmp_path / "age.yaml",
    )
    project_root = Path(__file__).resolve().parents[1]
    await init_database(project_root, settings.database_url)

    container = AppContainer.from_settings(settings)
    _scan_scenario_files(str(scen.resolve()))
    result = reload_catalog(container)
    assert "dialog" in result.mode_ids
    assert "demo" in result.scenario_ids
    await container.aclose()
    get_settings.cache_clear()
