from center_voice_agent.agent.text_tool_fallback import parse_text_tool_calls


def test_parse_fence_json() -> None:
    text = '''Отвечаю. Сохраняю:
```json
{"tool": "memory_upsert", "args": {"category": "hobby", "value_text": "лего"}}
```
'''
    calls = parse_text_tool_calls(
        text,
        mode="fenced_only",
        allowed_tools=("memory_upsert",),
    )
    assert len(calls) == 1
    assert calls[0]["name"] == "memory_upsert"
    assert calls[0]["args"]["category"] == "hobby"


def test_parse_inline_name_strict() -> None:
    text = '{"name": "memory_search", "args": {"query": "кошки", "limit": 3}}'
    calls = parse_text_tool_calls(
        text,
        mode="strict",
        allowed_tools=("memory_search",),
    )
    assert calls[0]["name"] == "memory_search"
    assert calls[0]["args"]["query"] == "кошки"


def test_fenced_only_ignores_inline_json_in_prose() -> None:
    text = 'Расскажу про {"tool": "memory_upsert", "args": {"value_text": "x"}} в сказке.'
    calls = parse_text_tool_calls(
        text,
        mode="fenced_only",
        allowed_tools=("memory_upsert",),
    )
    assert calls == []


def test_strict_rejects_unknown_tool() -> None:
    text = '''```json
{"tool": "web_search", "args": {"query": "x"}}
```'''
    calls = parse_text_tool_calls(
        text,
        mode="fenced_only",
        allowed_tools=("memory_search",),
    )
    assert calls == []


def test_off_mode_never_parses() -> None:
    text = '{"name": "memory_search", "args": {"query": "a"}}'
    assert parse_text_tool_calls(text, mode="off") == []
