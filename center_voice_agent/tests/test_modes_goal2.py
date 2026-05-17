from pathlib import Path

import pytest

from center_voice_agent.modes.registry import ModeRegistry
from center_voice_agent.modes.schema import load_mode_yaml_file


def test_reload_all_loads_three_modes() -> None:
    root = Path(__file__).resolve().parents[1]
    reg = ModeRegistry(root / "config" / "modes", project_root=root)
    ids = reg.reload_all()
    assert "dialog" in ids and "lesson" in ids and "play" in ids
    d = reg.get("dialog")
    assert "наставник" in d.system_prompt.lower() or "дет" in d.system_prompt.lower()


def test_duplicate_mode_id_raises(tmp_path: Path) -> None:
    modes = tmp_path / "modes"
    modes.mkdir()
    (modes / "a.yaml").write_text("id: dup\ndisplay_name: A\nsystem_prompt: x\n", encoding="utf-8")
    (modes / "b.yaml").write_text("id: dup\ndisplay_name: B\nsystem_prompt: y\n", encoding="utf-8")
    reg = ModeRegistry(modes, project_root=tmp_path)
    with pytest.raises(ValueError, match="Дублирующийся"):
        reg.reload_all()


def test_invalid_allowed_transition_raises(tmp_path: Path) -> None:
    modes = tmp_path / "modes"
    modes.mkdir()
    (modes / "one.yaml").write_text(
        "id: one\ndisplay_name: O\nsystem_prompt: s\nallowed_transitions:\n  - ghost\n",
        encoding="utf-8",
    )
    reg = ModeRegistry(modes, project_root=tmp_path)
    with pytest.raises(ValueError, match="ghost"):
        reg.reload_all()


def test_load_prompt_from_path(tmp_path: Path) -> None:
    modes = tmp_path / "modes"
    modes.mkdir()
    pr = modes / "prompts"
    pr.mkdir()
    (pr / "p.txt").write_text("hello from file", encoding="utf-8")
    (modes / "m.yaml").write_text(
        'id: m\ndisplay_name: M\nsystem_prompt: ""\nsystem_prompt_path: ./prompts/p.txt\n',
        encoding="utf-8",
    )
    m = load_mode_yaml_file(modes / "m.yaml", project_root=tmp_path)
    assert m.system_prompt.strip() == "hello from file"
