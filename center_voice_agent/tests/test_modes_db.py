from pathlib import Path

import pytest

from center_voice_agent.db.session import create_engine_and_session_factory, run_migrations
from center_voice_agent.modes.db_source import fetch_published_mode_yamls, publish_mode_yaml_sync
from center_voice_agent.modes.registry import ModeRegistry

PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.asyncio
async def test_migrations_create_mode_definitions(tmp_path: Path) -> None:
    dbfile = tmp_path / "m.db"
    url = f"sqlite+aiosqlite:///{dbfile.as_posix().replace(chr(92), '/')}"
    engine, _ = create_engine_and_session_factory(url)
    await run_migrations(engine, PROJECT_ROOT)
    await engine.dispose()

    import sqlite3

    conn = sqlite3.connect(str(dbfile))
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='mode_definitions'"
        )
        assert cur.fetchone() is not None
    finally:
        conn.close()


@pytest.mark.asyncio
async def test_hybrid_overlay_from_database(tmp_path: Path) -> None:
    dbfile = tmp_path / "m.db"
    url = f"sqlite+aiosqlite:///{dbfile.as_posix().replace(chr(92), '/')}"
    engine, _ = create_engine_and_session_factory(url)
    await run_migrations(engine, PROJECT_ROOT)
    await engine.dispose()

    modes = tmp_path / "config" / "modes"
    modes.mkdir(parents=True)
    (modes / "x.yaml").write_text(
        "id: x\ndisplay_name: X\nsystem_prompt: from file\nallowed_transitions: []\n",
        encoding="utf-8",
    )

    publish_mode_yaml_sync(
        url,
        config_yaml="id: x\ndisplay_name: X\nsystem_prompt: from database\nallowed_transitions: []\n",
        mode_id="x",
        center_id=None,
        status="published",
    )

    reg = ModeRegistry(
        modes,
        project_root=tmp_path,
        database_url=url,
        modes_source="hybrid",
        modes_center_id=None,
    )
    reg.reload_all()
    assert reg.get("x").system_prompt.strip() == "from database"
    assert reg.source_path("x") is None


@pytest.mark.asyncio
async def test_database_empty_falls_back_to_files(tmp_path: Path) -> None:
    dbfile = tmp_path / "m.db"
    url = f"sqlite+aiosqlite:///{dbfile.as_posix().replace(chr(92), '/')}"
    engine, _ = create_engine_and_session_factory(url)
    await run_migrations(engine, PROJECT_ROOT)
    await engine.dispose()

    modes = tmp_path / "config" / "modes"
    modes.mkdir(parents=True)
    (modes / "x.yaml").write_text(
        "id: x\ndisplay_name: X\nsystem_prompt: only file\nallowed_transitions: []\n",
        encoding="utf-8",
    )

    reg = ModeRegistry(
        modes,
        project_root=tmp_path,
        database_url=url,
        modes_source="database",
        modes_center_id=None,
    )
    reg.reload_all()
    assert reg.get("x").system_prompt.strip() == "only file"


@pytest.mark.asyncio
async def test_database_only_published_rows(tmp_path: Path) -> None:
    dbfile = tmp_path / "m.db"
    url = f"sqlite+aiosqlite:///{dbfile.as_posix().replace(chr(92), '/')}"
    engine, _ = create_engine_and_session_factory(url)
    await run_migrations(engine, PROJECT_ROOT)
    await engine.dispose()

    publish_mode_yaml_sync(
        url,
        config_yaml="id: a\ndisplay_name: A\nsystem_prompt: pa\nallowed_transitions:\n  - b\n",
        mode_id="a",
        status="published",
    )
    publish_mode_yaml_sync(
        url,
        config_yaml="id: b\ndisplay_name: B\nsystem_prompt: pb\nallowed_transitions:\n  - a\n",
        mode_id="b",
        status="published",
    )

    modes = tmp_path / "config" / "modes"
    modes.mkdir(parents=True)

    reg = ModeRegistry(
        modes,
        project_root=tmp_path,
        database_url=url,
        modes_source="database",
        modes_center_id=None,
    )
    reg.reload_all()
    assert set(reg.list_ids()) == {"a", "b"}


def test_fetch_published_respects_center_priority(tmp_path: Path) -> None:
    dbfile = tmp_path / "m.db"
    url = f"sqlite+aiosqlite:///{dbfile.as_posix().replace(chr(92), '/')}"

    import asyncio

    async def _setup() -> None:
        engine, _ = create_engine_and_session_factory(url)
        await run_migrations(engine, PROJECT_ROOT)
        await engine.dispose()

    asyncio.run(_setup())

    publish_mode_yaml_sync(
        url,
        config_yaml="id: z\ndisplay_name: Z\nsystem_prompt: global\nallowed_transitions: []\n",
        mode_id="z",
        center_id=None,
        status="published",
    )
    publish_mode_yaml_sync(
        url,
        config_yaml="id: z\ndisplay_name: Z\nsystem_prompt: center\nallowed_transitions: []\n",
        mode_id="z",
        center_id="c1",
        status="published",
    )

    g = fetch_published_mode_yamls(url, center_id=None)
    assert "z" in g and "global" in g["z"]

    c = fetch_published_mode_yamls(url, center_id="c1")
    assert "z" in c and "center" in c["z"]
