from pathlib import Path

import pytest

from center_voice_agent.tools.impl import rag_search as rag_search_impl


@pytest.mark.asyncio
async def test_rag_search_finds_keyword(tmp_path: Path) -> None:
    docs = tmp_path / "rag"
    docs.mkdir()
    (docs / "emotions.md").write_text("Когда ребёнок расстроен — назови эмоцию.", encoding="utf-8")

    out = await rag_search_impl.rag_search_text(
        "эмоцию",
        docs_dir=docs,
        max_chars=4000,
    )
    assert "emotions.md" in out
    assert "эмоцию" in out.lower()


@pytest.mark.asyncio
async def test_rag_search_missing_dir() -> None:
    out = await rag_search_impl.rag_search_text(
        "test",
        docs_dir=Path("/nonexistent/rag/dir"),
        max_chars=1000,
    )
    assert "не настроен" in out or "не найден" in out.lower()
