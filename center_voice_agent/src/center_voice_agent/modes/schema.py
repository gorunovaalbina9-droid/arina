from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

import yaml
from pydantic import BaseModel, Field, field_validator


def _resolve_prompt_path(
    path_str: str,
    *,
    mode_file_dir: Path,
    project_root: Path,
) -> Path:
    """Путь к файлу промпта: абсолютный; ./ — сначала от каталога YAML режима, иначе от корня репо."""
    raw = path_str.strip().strip('"').strip("'")
    p = Path(raw)
    if p.is_absolute():
        return p
    if raw.startswith("./"):
        rel = raw[2:]
        cand = (mode_file_dir / rel).resolve()
        if cand.is_file():
            return cand
        return (project_root / rel).resolve()
    return (mode_file_dir / raw).resolve()


class ModeConfig(BaseModel):
    """Контракт режима (YAML). Редактируется без изменения Python."""

    id: str = Field(..., pattern=r"^[a-z][a-z0-9_]*$")
    display_name: str
    system_prompt: str = ""
    system_prompt_path: Optional[str] = None
    llm_params: dict[str, Any] = Field(default_factory=dict)
    tool_ids: list[str] = Field(default_factory=list)
    allowed_transitions: list[str] = Field(
        default_factory=list,
        description="Пусто = разрешён переход в любой известный режим. Иначе только перечисленные mode_id.",
    )
    voice_aliases: list[str] = Field(
        default_factory=list,
        description="Доп. фразы для смены режима (дополняют config/voice/mode_commands.yaml).",
    )
    description_for_admin: Optional[str] = None
    max_tool_rounds: Optional[int] = Field(default=None, ge=1, le=50)

    @field_validator("tool_ids", mode="before")
    @classmethod
    def _strip_tools(cls, v: Any) -> list[str]:
        if v is None:
            return []
        return [str(x).strip() for x in v if str(x).strip()]


def load_mode_config_dict(
    data: dict[str, Any],
    project_root: Path,
    *,
    virtual_dir: Path,
    source_hint: str = "",
) -> ModeConfig:
    """Разбор уже загруженного объекта режима (файл или БД). virtual_dir — база для system_prompt_path."""
    prompt = str(data.get("system_prompt") or "").strip()
    path_key = data.get("system_prompt_path")
    if path_key:
        pth = _resolve_prompt_path(str(path_key), mode_file_dir=virtual_dir, project_root=project_root)
        if not pth.is_file():
            raise FileNotFoundError(
                f"system_prompt_path не найден: {pth} (источник {source_hint or virtual_dir})"
            )
        prompt = pth.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"Пустой system_prompt ({source_hint})")
    data = dict(data)
    data["system_prompt"] = prompt
    return ModeConfig.model_validate(data)


def load_mode_yaml_file(mode_file: Path, project_root: Path) -> ModeConfig:
    raw = yaml.safe_load(mode_file.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"Ожидался объект YAML в {mode_file}")
    return load_mode_config_dict(raw, project_root, virtual_dir=mode_file.parent, source_hint=str(mode_file))


def load_mode_yaml_text(
    yaml_text: str,
    project_root: Path,
    *,
    virtual_dir: Path | None = None,
    source_hint: str = "database",
) -> ModeConfig:
    """Режим из строки YAML (таблица mode_definitions). Пути ./ по умолчанию от config/modes/."""
    raw = yaml.safe_load(yaml_text)
    if not isinstance(raw, dict):
        raise ValueError("Ожидался один объект YAML в config_yaml")
    vd = virtual_dir or (project_root / "config" / "modes")
    return load_mode_config_dict(raw, project_root, virtual_dir=vd, source_hint=source_hint)


def validate_mode_graph(modes: dict[str, ModeConfig]) -> None:
    """Проверка allowed_transitions после загрузки всех файлов."""
    all_ids = frozenset(modes.keys())
    for mid, mode in modes.items():
        for t in mode.allowed_transitions:
            if t not in all_ids:
                raise ValueError(
                    f"Режим «{mid}»: allowed_transitions содержит неизвестный mode_id «{t}». "
                    f"Известны: {sorted(all_ids)}"
                )
            if t == mid:
                raise ValueError(f"Режим «{mid}»: переход сам в себя в allowed_transitions не имеет смысла.")
