"""
Глобальная конфигурация приложения.

Единственный модуль, который читает переменные окружения и .env.
Остальной код получает только экземпляр Settings (или AppContainer).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

import yaml
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
    here = Path(__file__).resolve()
    return here.parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    project_root: Path = Field(default_factory=_find_project_root)

    llm_base_url: str = Field(default="https://api.openai.com/v1", alias="LLM_BASE_URL")
    llm_api_key: Optional[str] = Field(default=None, alias="LLM_API_KEY")
    llm_model: str = Field(default="gpt-4o-mini", alias="LLM_MODEL")
    # Запасной ключ (только здесь читается из env)
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    # Опционально: путь к .env с OPENAI_API_KEY (например ../voice_assistant/.env)
    llm_fallback_env_file: Optional[str] = Field(default=None, alias="LLM_FALLBACK_ENV_FILE")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_json: bool = Field(default=True, alias="LOG_JSON")
    log_file_path: Optional[Path] = Field(default=None, alias="LOG_FILE_PATH")
    log_file_max_bytes: int = Field(default=5_000_000, alias="LOG_FILE_MAX_BYTES")
    log_file_backup_count: int = Field(default=3, alias="LOG_FILE_BACKUP_COUNT")
    security_incidents_path: Optional[Path] = Field(default=None, alias="SECURITY_INCIDENTS_PATH")
    security_incidents_max_bytes: int = Field(default=1_000_000, alias="SECURITY_INCIDENTS_MAX_BYTES")

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
    default_max_tool_rounds: int = Field(default=10, alias="DEFAULT_MAX_TOOL_ROUNDS")

    prefetch_long_term_memory: bool = Field(default=True, alias="PREFETCH_LONG_TERM_MEMORY")
    prefetch_memory_limit: int = Field(default=8, alias="PREFETCH_MEMORY_LIMIT")
    short_term_max_pairs: int = Field(default=15, alias="SHORT_TERM_MAX_PAIRS")
    short_term_max_messages: int = Field(default=30, alias="SHORT_TERM_MAX_MESSAGES")
    short_term_source: Literal["memory", "db"] = Field(default="memory", alias="SHORT_TERM_SOURCE")

    log_redact_user_text: bool = Field(default=True, alias="LOG_REDACT_USER_TEXT")
    tool_max_output_chars: int = Field(default=4000, alias="TOOL_MAX_OUTPUT_CHARS")
    web_search_url: Optional[str] = Field(default=None, alias="WEB_SEARCH_URL")
    web_search_timeout_sec: float = Field(default=15.0, alias="WEB_SEARCH_TIMEOUT_SEC")
    moderation_enabled: bool = Field(default=True, alias="MODERATION_ENABLED")
    moderation_config_path: Optional[Path] = Field(default=None)
    moderation_blocked_input_substrings: tuple[str, ...] = Field(default_factory=tuple)
    moderation_blocked_output_substrings: tuple[str, ...] = Field(default_factory=tuple)
    moderation_blocked_input_patterns: tuple[str, ...] = Field(default_factory=tuple)
    moderation_blocked_output_patterns: tuple[str, ...] = Field(default_factory=tuple)
    moderation_api_url: Optional[str] = Field(default=None, alias="MODERATION_API_URL")
    moderation_api_key: Optional[str] = Field(default=None, alias="MODERATION_API_KEY")
    moderation_api_timeout_sec: float = Field(default=5.0, alias="MODERATION_API_TIMEOUT_SEC")
    moderation_escalation_threshold: int = Field(default=3, alias="MODERATION_ESCALATION_THRESHOLD")
    rate_limit_enabled: bool = Field(default=True, alias="RATE_LIMIT_ENABLED")
    rate_limit_per_minute: int = Field(default=20, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=120, alias="RATE_LIMIT_PER_HOUR")
    rate_limit_backend: Literal["memory", "redis"] = Field(default="memory", alias="RATE_LIMIT_BACKEND")
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")
    web_search_enabled: bool = Field(default=False, alias="WEB_SEARCH_ENABLED")
    web_search_allowed_mode_ids: tuple[str, ...] = Field(default_factory=tuple)
    log_redact_tool_args: bool = Field(default=True, alias="LOG_REDACT_TOOL_ARGS")
    require_parent_consent: bool = Field(default=False, alias="REQUIRE_PARENT_CONSENT")
    compliance_llm_region: Optional[str] = Field(default=None, alias="COMPLIANCE_LLM_REGION")
    text_tool_fallback: bool = Field(default=False, alias="TEXT_TOOL_FALLBACK")
    text_tool_fallback_mode: Literal["off", "fenced_only", "strict", "permissive"] = Field(
        default="off",
        alias="TEXT_TOOL_FALLBACK_MODE",
    )

    @model_validator(mode="after")
    def _load_agent_yaml(self) -> Settings:
        """Несекретные лимиты из config/agent.yaml (режимы/сценарии — отдельные YAML)."""
        path = self.project_root / "config" / "agent.yaml"
        if not path.is_file():
            return self
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except OSError:
            return self
        if not isinstance(raw, dict):
            return self
        mapping: dict[str, str] = {
            "short_term_max_pairs": "short_term_max_pairs",
            "short_term_max_messages": "short_term_max_messages",
            "default_max_tool_rounds": "default_max_tool_rounds",
            "memory_prefetch_limit": "prefetch_memory_limit",
            "log_file_path": "log_file_path",
            "log_file_max_bytes": "log_file_max_bytes",
            "log_file_backup_count": "log_file_backup_count",
            "security_incidents_path": "security_incidents_path",
            "security_incidents_max_bytes": "security_incidents_max_bytes",
        }
        path_keys = {"log_file_path", "security_incidents_path"}
        for yaml_key, attr in mapping.items():
            if yaml_key in raw and raw[yaml_key] is not None:
                val = raw[yaml_key]
                if yaml_key in path_keys:
                    val = Path(str(val))
                object.__setattr__(self, attr, val)
        rel = raw.get("openai_fallback_env_relative")
        if rel and not self.llm_fallback_env_file:
            object.__setattr__(
                self,
                "llm_fallback_env_file",
                str((self.project_root / str(rel)).resolve()),
            )
        return self

    @model_validator(mode="after")
    def _load_moderation_yaml(self) -> Settings:
        path = self.moderation_config_path or (self.project_root / "config" / "moderation.yaml")
        if not path.is_file():
            return self
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        except OSError:
            return self
        if not isinstance(raw, dict):
            return self

        def _phrases(key: str) -> tuple[str, ...]:
            items = raw.get(key) or []
            if not isinstance(items, list):
                return ()
            return tuple(str(x).strip().lower() for x in items if str(x).strip())

        def _patterns(key: str) -> tuple[str, ...]:
            items = raw.get(key) or []
            if not isinstance(items, list):
                return ()
            return tuple(str(x).strip() for x in items if str(x).strip())

        inp = _phrases("blocked_input_substrings")
        out = _phrases("blocked_output_substrings")
        inp_pat = _patterns("blocked_input_patterns")
        out_pat = _patterns("blocked_output_patterns")
        legacy = _phrases("blocked_substrings")
        if not inp and legacy:
            inp = legacy
        if not out and legacy:
            out = legacy
        if inp:
            object.__setattr__(self, "moderation_blocked_input_substrings", inp)
        if out:
            object.__setattr__(self, "moderation_blocked_output_substrings", out)
        if inp_pat:
            object.__setattr__(self, "moderation_blocked_input_patterns", inp_pat)
        if out_pat:
            object.__setattr__(self, "moderation_blocked_output_patterns", out_pat)
        return self

    @model_validator(mode="after")
    def _resolve_text_tool_fallback_mode(self) -> Settings:
        if not self.text_tool_fallback:
            object.__setattr__(self, "text_tool_fallback_mode", "off")
        elif self.text_tool_fallback_mode == "off":
            object.__setattr__(self, "text_tool_fallback_mode", "fenced_only")
        return self

    @model_validator(mode="after")
    def _resolve_llm_credentials(self) -> Settings:
        key = (self.llm_api_key or "").strip()
        if not key or key.lower() in _LLM_KEY_PLACEHOLDERS:
            alt = (self.openai_api_key or "").strip()
            if not alt or alt.lower() in _LLM_KEY_PLACEHOLDERS:
                fallback_path = self.llm_fallback_env_file
                if not fallback_path:
                    sibling = self.project_root.parent / "voice_assistant" / ".env"
                    if sibling.is_file():
                        fallback_path = str(sibling)
                if fallback_path:
                    p = Path(fallback_path)
                    if not p.is_absolute():
                        p = (self.project_root / p).resolve()
                    alt = (_read_dotenv_value(p, "OPENAI_API_KEY") or "").strip()
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

    @property
    def short_term_message_limit(self) -> int:
        """Число сообщений user/assistant в STM (пары × 2)."""
        return self.short_term_max_pairs * 2


@lru_cache
def get_settings() -> Settings:
    return Settings()
