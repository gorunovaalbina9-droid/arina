"""Поиск по локальным методичкам (keyword RAG, без векторной БД)."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional


def _snippet(text: str, query: str, *, radius: int = 120) -> str:
    lower = text.lower()
    idx = lower.find(query.lower())
    if idx < 0:
        return text[: radius * 2].strip()
    start = max(0, idx - radius)
    end = min(len(text), idx + len(query) + radius)
    chunk = text[start:end].strip()
    chunk = re.sub(r"\s+", " ", chunk)
    if start > 0:
        chunk = "…" + chunk
    if end < len(text):
        chunk = chunk + "…"
    return chunk


async def rag_search_text(
    query: str,
    *,
    docs_dir: Optional[Path],
    max_chars: int,
    max_hits: int = 5,
) -> str:
    q = query.strip()
    if not q:
        return "Уточни, пожалуйста, что искать в методичках."
    if docs_dir is None or not docs_dir.is_dir():
        return (
            "[rag_search] Каталог методичек не настроен: задайте RAG_DOCS_DIR "
            f"и положите .md/.txt (запрос: {q!r})."
        )

    q_lower = q.lower()
    hits: list[str] = []
    for path in sorted(docs_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in {".md", ".txt"}:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if q_lower not in text.lower():
            continue
        rel = path.relative_to(docs_dir).as_posix()
        snip = _snippet(text, q)
        hits.append(f"### {rel}\n{snip}")
        if len(hits) >= max_hits:
            break

    if not hits:
        return f"По запросу {q!r} в методичках ничего не найдено."

    body = "\n\n".join(hits)
    if max_chars > 0 and len(body) > max_chars:
        body = body[: max_chars - 20] + "\n…(обрезано)"
    return body
