import center_voice_agent.tools.builtin  # noqa: F401
from center_voice_agent.tools.registry import ToolBuildContext, build_tool, registered_tool_ids


def test_builtin_tools_registered() -> None:
    ids = registered_tool_ids()
    assert "memory_search" in ids
    assert "memory_upsert" in ids
    assert "web_search" in ids


def test_build_web_search_without_repo() -> None:
    ctx = ToolBuildContext(
        memory_repo=None,
        child_profile_id="c1",
        web_search_url=None,
    )
    tool = build_tool("web_search", ctx)
    assert tool.name == "web_search"
