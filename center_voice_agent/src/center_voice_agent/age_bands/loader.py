from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, Field


class AgeBandsFile(BaseModel):
    default_block: str = ""
    bands: dict[str, str] = Field(default_factory=dict)


def load_age_bands(path: Path) -> AgeBandsFile:
    if not path.is_file():
        return AgeBandsFile(default_block="", bands={})
    raw = yaml.safe_load(path.read_text(encoding="utf-8-sig"))
    if not raw:
        return AgeBandsFile(default_block="", bands={})
    if not isinstance(raw, dict):
        raise ValueError(f"Ожидался объект YAML в {path}")
    return AgeBandsFile.model_validate(raw)


def resolve_age_prompt(bands: AgeBandsFile, age_band: Optional[str]) -> str:
    """Текст блока для системного промпта по age_band."""
    parts: list[str] = []
    if bands.default_block.strip():
        parts.append(bands.default_block.strip())
    if age_band:
        key = age_band.strip()
        block = bands.bands.get(key)
        if block and str(block).strip():
            parts.append(str(block).strip())
    return "\n\n".join(parts) if parts else ""
