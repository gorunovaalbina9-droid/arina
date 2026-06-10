"""Тесты NLU смены режима (exact + fuzzy)."""

from center_voice_agent.modes.commands import ModeCommandEntry, ModeCommandsFile, try_parse_mode_switch
from center_voice_agent.modes.nlu import resolve_mode_switch


def _cmds() -> ModeCommandsFile:
    return ModeCommandsFile(
        entries=[
            ModeCommandEntry(mode_id="lesson", phrases=["переключись в учебный"]),
            ModeCommandEntry(mode_id="dialog", phrases=["давай поболтаем"]),
        ]
    )


def test_exact_mode_switch() -> None:
    aliases = {"play": ["поиграем"]}
    assert (
        try_parse_mode_switch("  переключись в учебный  ", commands=_cmds(), voice_aliases=aliases)
        == "lesson"
    )


def test_fuzzy_mode_switch_typo() -> None:
    assert (
        resolve_mode_switch(
            "переключись в учебнай",
            commands=_cmds(),
            voice_aliases={},
            nlu_enabled=True,
            nlu_threshold=0.82,
        )
        == "lesson"
    )


def test_fuzzy_disabled() -> None:
    assert (
        resolve_mode_switch(
            "переключись в учебнай",
            commands=_cmds(),
            voice_aliases={},
            nlu_enabled=False,
        )
        is None
    )


def test_no_fuzzy_in_long_reply_without_command() -> None:
    long_text = " ".join(["расскажи"] * 20) + " про динозавров"
    assert (
        resolve_mode_switch(
            long_text,
            commands=_cmds(),
            voice_aliases={},
            nlu_enabled=True,
        )
        is None
    )
