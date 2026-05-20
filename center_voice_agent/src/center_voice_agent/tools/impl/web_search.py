from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Optional


def truncate_tool_output(text: str, max_chars: int) -> str:
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[: max_chars - 20] + "\n…(обрезано)"


async def run_web_search(
    query: str,
    *,
    api_url: Optional[str],
    timeout_sec: float,
    max_chars: int,
) -> str:
    q = query.strip()
    if not q:
        return "Уточни, пожалуйста, что искать."
    if not api_url:
        return (
            "[web_search] Поиск не настроен: задайте WEB_SEARCH_URL в .env "
            f"(запрос: {q!r})."
        )
    body = json.dumps({"query": q}).encode("utf-8")
    req = urllib.request.Request(
        api_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        return f"Поиск временно недоступен: {e.reason or e}"
    except TimeoutError:
        return "Поиск занял слишком много времени. Попробуй переформулировать вопрос."
    return truncate_tool_output(raw, max_chars)
