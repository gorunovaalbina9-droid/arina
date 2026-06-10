"""Внешний провайдер модерации (HTTP API). По умолчанию — заглушка."""

from __future__ import annotations

from typing import Optional, Protocol

import structlog

log = structlog.get_logger(__name__)


class ModerationProvider(Protocol):
    def check_input(self, user_text: str) -> Optional[str]:
        ...

    def check_output(self, text: str) -> Optional[str]:
        ...


class NullModerationProvider:
    def check_input(self, user_text: str) -> Optional[str]:
        return None

    def check_output(self, text: str) -> Optional[str]:
        return None


class HttpModerationProvider:
    """
    POST JSON {"text": "...", "direction": "input"|"output"} → {"blocked": bool, "reason": "..."}.
    При недоступности API — пропуск (fail-open с логом; для prod настройте мониторинг).
    """

    def __init__(
        self,
        *,
        url: str,
        api_key: Optional[str] = None,
        timeout_sec: float = 5.0,
    ) -> None:
        self._url = url.rstrip("/")
        self._api_key = (api_key or "").strip()
        self._timeout = timeout_sec

    def _call(self, text: str, direction: str) -> Optional[str]:
        try:
            import urllib.error
            import urllib.request
            import json

            body = json.dumps({"text": text, "direction": direction}, ensure_ascii=False).encode("utf-8")
            req = urllib.request.Request(
                self._url,
                data=body,
                headers={
                    "Content-Type": "application/json",
                    **({"Authorization": f"Bearer {self._api_key}"} if self._api_key else {}),
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            if isinstance(data, dict) and data.get("blocked"):
                reason = str(data.get("reason") or "external_api")
                return f"blocked_api:{reason}"
        except Exception as exc:
            log.warning("moderation_api_unavailable", error=str(exc)[:200])
        return None

    def check_input(self, user_text: str) -> Optional[str]:
        return self._call(user_text, "input")

    def check_output(self, text: str) -> Optional[str]:
        return self._call(text, "output")
