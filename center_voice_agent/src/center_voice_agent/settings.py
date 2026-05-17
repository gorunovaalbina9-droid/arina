from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _find_project_root() -> Path:
    """Каталог center_voice_agent (родитель src)."""
    here = Path(__file__).resolve()
    return here.parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    project_root: Path = Field(default_factory=_find_project_root)

    llm_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_BASE_URL")
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=True, alias="LOG_JSON")

    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/agent.db",
        alias="DATABASE_URL",
    )

    modes_dir: Path = Field(default_factory=lambda: _find_project_root() / "config" / "modes")
    scenarios_dir: Path = Field(default_factory=lambda: _find_project_root() / "config" / "scenarios")
    voice_commands_path: Path = Field(
        default_factory=lambda: _find_project_root() / "config" / "voice" / "mode_commands.yaml"
    )
    scenario_commands_path: Path = Field(
        default_factory=lambda: _find_project_root() / "config" / "voice" / "scenario_commands.yaml"
    )
    age_bands_path: Path = Field(
        default_factory=lambda: _find_project_root() / "config" / "age_bands" / "default.yaml"
    )
    default_mode_id: str = Field(default="dialog", alias="DEFAULT_MODE_ID")

    modes_source: Literal["files", "database", "hybrid"] = Field(
        default="files",
        alias="MODES_SOURCE",
    )
    modes_center_id: Optional[str] = Field(default=None, alias="MODES_CENTER_ID")

    scenarios_source: Literal["files", "database", "hybrid"] = Field(
        default="files",
        alias="SCENARIOS_SOURCE",
    )
    scenarios_center_id: Optional[str] = Field(default=None, alias="SCENARIOS_CENTER_ID")

    use_langgraph: bool = Field(default=True, alias="USE_LANGGRAPH")

    @model_validator(mode="after")
    def _resolve_sqlite_file_url(self) -> Settings:
        url = self.database_url
        marker = "sqlite+aiosqlite:///"
        if not url.startswith(marker):
            return self
        rest = url[len(marker) :]
        new_url: str | None = None
        if rest.startswith("./"):
            abs_path = (self.project_root / rest[2:]).resolve()
            new_url = f"{marker}{abs_path.as_posix()}"
        elif not rest.startswith("/") and ":" not in rest[:3]:
            abs_path = (self.project_root / rest).resolve()
            new_url = f"{marker}{abs_path.as_posix()}"
        elif rest.startswith("/") and len(rest) >= 3 and rest[2] == ":":
            new_url = f"{marker}{rest.lstrip('/')}"
        if new_url is not None:
            object.__setattr__(self, "database_url", new_url)
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
