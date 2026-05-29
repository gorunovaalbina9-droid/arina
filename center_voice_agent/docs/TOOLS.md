# Инструменты (tools)

Реестр: `src/center_voice_agent/tools/registry.py`. Встроенные tools регистрируются в `tools/builtin.py` при импорте.

## Добавить новый tool

1. Реализовать builder `def _build_my_tool(ctx: ToolBuildContext) -> StructuredTool`.
2. В `builtin.py`: `register_tool("my_tool", _build_my_tool)`.
3. В YAML режима: `tool_ids: [..., my_tool]`.
4. Тест в `tests/test_tool_registry.py`.

Сборка для хода: `build_tools_for_mode()` в `tools/factory.py`.
