from center_voice_agent.agent.text_tool_fallback import parse_text_tool_calls


def test_parse_fence_json() -> None:
    text = '''Отвечаю. Сохраняю:
```json
{"tool": "memory_upsert", "args": {"category": "hobby", "value_text": "лего"}}
```
'''
    calls = parse_text_tool_calls(text)
    assert len(calls) == 1
    assert calls[0]["name"] == "memory_upsert"
    assert calls[0]["args"]["category"] == "hobby"


def test_parse_inline_name() -> None:
    text = '{"name": "memory_search", "args": {"query": "кошки", "limit": 3}}'
    calls = parse_text_tool_calls(text)
    assert calls[0]["name"] == "memory_search"
    assert calls[0]["args"]["query"] == "кошки"
