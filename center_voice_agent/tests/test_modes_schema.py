from pathlib import Path

import pytest

from center_voice_agent.modes.registry import ModeRegistry
from center_voice_agent.modes.schema import validate_mode_graph


def test_validate_mode_graph_rejects_unknown_transition(tmp_path: Path) -> None:
    modes = tmp_path / "modes"
    modes.mkdir()
    (modes / "a.yaml").write_text(
        "id: a\ndisplay_name: A\nsystem_prompt: s\nallowed_transitions: [missing]\n",
        encoding="utf-8",
    )
    reg = ModeRegistry(modes, project_root=tmp_path, modes_source="files")
    with pytest.raises(ValueError, match="неизвестный mode_id"):
        reg.reload_all()


def test_validate_mode_graph_accepts_calm(tmp_path: Path) -> None:
    real_root = Path(__file__).resolve().parents[1]
    modes_dir = real_root / "config" / "modes"
    reg = ModeRegistry(modes_dir, project_root=real_root, modes_source="files")
    ids = reg.reload_all()
    assert "calm" in ids
    assert "dialog" in ids
