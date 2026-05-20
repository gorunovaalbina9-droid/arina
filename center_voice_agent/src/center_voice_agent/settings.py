from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

_LLM_KEY_PLACEHOLDERS = frozenset(
    {"", "replace_me", "your-api-key", "your-finetuned-model", "sk-your-key-here"}
)


def _read_dotenv_value(path: Path, key: str) -> str | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    prefix = f"{key}="
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(prefix):
            return stripped[len(prefix) :].strip().strip('"').strip("'")
    return None


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

    prefetch_long_term_memory: bool = Field(default=True, alias="PREFETCH_LONG_TERM_MEMORY")
    log_redact_user_text: bool = Field(default=True, alias="LOG_REDACT_USER_TEXT")
    tool_max_output_chars: int = Field(default=4000, alias="TOOL_MAX_OUTPUT_CHARS")
    web_search_url: Optional[str] = Field(default=None, alias="WEB_SEARCH_URL")
    web_search_timeout_sec: float = Field(default=15.0, alias="WEB_SEARCH_TIMEOUT_SEC")
    moderation_enabled: bool = Field(default=True, alias="MODERATION_ENABLED")

    # Plan B: если модель не вызвала tools, попробовать JSON из текста ответа
    text_tool_fallback: bool = Field(default=True, alias="TEXT_TOOL_FALLBACK")

    @model_validator(mode="after")
    def _resolve_llm_from_openai_env(self) -> Settings:
        """Если LLM_* — заглушки, взять OPENAI_API_KEY из env или voice_assistant/.env."""
        key = (self.llm_api_key or "").strip()
        if not key or key.lower() in _LLM_KEY_PLACEHOLDERS:
            alt = os.environ.get("OPENAI_API_KEY", "").strip()
            if not alt or alt.lower() in _LLM_KEY_PLACEHOLDERS:
                sibling = self.project_root.parent / "voice_assistant" / ".env"
                alt = (_read_dotenv_value(sibling, "OPENAI_API_KEY") or "").strip()
            if alt and alt.lower() not in _LLM_KEY_PLACEHOLDERS:
                object.__setattr__(self, "llm_api_key", alt)
        if "example.com" in (self.llm_base_url or ""):
            object.__setattr__(self, "llm_base_url", "https://api.openai.com/v1")
        model = (self.llm_model or "").strip()
        if model.lower() in _LLM_KEY_PLACEHOLDERS:
            object.__setattr__(self, "llm_model", "gpt-4o-mini")
        return self

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
