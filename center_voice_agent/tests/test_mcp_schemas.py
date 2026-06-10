import center_voice_agent.tools.builtin  # noqa: F401
from center_voice_agent.mcp.schemas import TOOL_SCHEMAS, list_tool_schemas
from center_voice_agent.tools.registry import registered_tool_ids


def test_mcp_schemas_cover_registered_tools() -> None:
    registered = registered_tool_ids()
    for tid in registered:
        assert tid in TOOL_SCHEMAS, f"Нет MCP schema для {tid}"


def test_list_tool_schemas_subset() -> None:
    all_schemas = list_tool_schemas()
    assert len(all_schemas) == len(TOOL_SCHEMAS)
    subset = list_tool_schemas(tool_ids=frozenset({"web_search", "rag_search"}))
    names = {s["name"] for s in subset}
    assert names == {"web_search", "rag_search"}
