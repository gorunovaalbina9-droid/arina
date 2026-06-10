"""MCP stdio-сервер: те же инструменты, что и у LangChain-агента."""

from __future__ import annotations

import asyncio
from typing import Any

from center_voice_agent.mcp.schemas import list_tool_schemas
from center_voice_agent.settings import Settings, get_settings
from center_voice_agent.tools.impl import rag_search as rag_search_impl
from center_voice_agent.tools.impl import web_search as web_search_impl


async def _dispatch_tool(name: str, arguments: dict[str, Any], settings: Settings) -> str:
    if name == "web_search":
        return await web_search_impl.run_web_search(
            str(arguments.get("query") or ""),
            api_url=settings.web_search_url,
            timeout_sec=settings.web_search_timeout_sec,
            max_chars=settings.tool_max_output_chars,
        )
    if name == "rag_search":
        return await rag_search_impl.rag_search_text(
            str(arguments.get("query") or ""),
            docs_dir=settings.rag_docs_dir,
            max_chars=settings.tool_max_output_chars,
        )
    if name in {"memory_search", "memory_upsert"}:
        return (
            f"[{name}] Требуется сессия агента с БД; вызывайте через HTTP /turn "
            "или LangChain, не через standalone MCP."
        )
    return f"Неизвестный инструмент: {name}"


async def _run_with_mcp_sdk(settings: Settings) -> None:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool

    server = Server("center-voice-agent")

    @server.list_tools()
    async def handle_list_tools() -> list[Tool]:
        return [
            Tool(
                name=s["name"],
                description=s["description"],
                inputSchema=s["inputSchema"],
            )
            for s in list_tool_schemas()
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict[str, Any] | None) -> list[TextContent]:
        args = arguments or {}
        text = await _dispatch_tool(name, args, settings)
        return [TextContent(type="text", text=text)]

    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
    try:
        import mcp  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "MCP SDK не установлен. Выполните: pip install center-voice-agent[mcp]"
        ) from exc
    settings = get_settings()
    asyncio.run(_run_with_mcp_sdk(settings))


if __name__ == "__main__":
    main()
