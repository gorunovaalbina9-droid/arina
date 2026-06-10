"""Многослойная модерация: нормализация, подстроки, regex, опциональный HTTP API."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional, Sequence

import structlog

from center_voice_agent.security.moderation_provider import (
    HttpModerationProvider,
    ModerationProvider,
    NullModerationProvider,
)
from center_voice_agent.settings import Settings

log = structlog.get_logger(__name__)

_FALLBACK_BLOCKED = (
    "как сделать бомбу",
    "как убить",
    "порно",
    "наркотик",
)

_LEET_MAP = str.maketrans(
    {
        "0": "o",
        "1": "i",
        "3": "e",
        "4": "a",
        "5": "s",
        "7": "t",
        "@": "a",
        "$": "s",
    }
)

_SPACE_RE = re.compile(r"[\s\-_]+")
_PUNCT_RE = re.compile(r"[^\w\s]+", re.UNICODE)


def normalize_for_moderation(text: str) -> str:
    """Снижает обход перефразом: lower, leet, homoglyphs, пробелы, пунктуация."""
    t = (text or "").lower().translate(_LEET_MAP)
    t = t.translate(
        str.maketrans(
            {
                "a": "а",
                "e": "е",
                "o": "о",
                "p": "р",
                "c": "с",
                "x": "х",
                "y": "у",
                "k": "к",
            }
        )
    )
    t = _SPACE_RE.sub(" ", t)
    t = _PUNCT_RE.sub(" ", t)
    return " ".join(t.split())


def _compile_patterns(raw: Sequence[str]) -> tuple[re.Pattern[str], ...]:
    out: list[re.Pattern[str]] = []
    for item in raw:
        s = (item or "").strip()
        if not s:
            continue
        try:
            out.append(re.compile(s, re.IGNORECASE | re.UNICODE))
        except re.error:
            log.warning("moderation_pattern_invalid", pattern=s[:80])
    return tuple(out)


def _match_substrings(norm: str, phrases: Sequence[str]) -> Optional[str]:
    for phrase in phrases:
        p = normalize_for_moderation(phrase)
        if p and p in norm:
            return f"blocked_phrase:{phrase}"
    return None


def _match_patterns(text: str, patterns: Sequence[re.Pattern[str]]) -> Optional[str]:
    for pat in patterns:
        m = pat.search(text)
        if m:
            return f"blocked_pattern:{pat.pattern[:60]}"
    return None


@dataclass
class ModerationEngine:
    blocked_input: Sequence[str] = field(default_factory=tuple)
    blocked_output: Sequence[str] = field(default_factory=tuple)
    input_patterns: Sequence[re.Pattern[str]] = field(default_factory=tuple)
    output_patterns: Sequence[re.Pattern[str]] = field(default_factory=tuple)
    external: ModerationProvider = field(default_factory=NullModerationProvider)

    @classmethod
    def from_settings(cls, settings: Settings) -> ModerationEngine:
        inp = settings.moderation_blocked_input_substrings or _FALLBACK_BLOCKED
        out = settings.moderation_blocked_output_substrings or _FALLBACK_BLOCKED
        ext: ModerationProvider = NullModerationProvider()
        if settings.moderation_api_url:
            ext = HttpModerationProvider(
                url=settings.moderation_api_url,
                api_key=settings.moderation_api_key,
                timeout_sec=settings.moderation_api_timeout_sec,
            )
        return cls(
            blocked_input=inp,
            blocked_output=out,
            input_patterns=_compile_patterns(settings.moderation_blocked_input_patterns),
            output_patterns=_compile_patterns(settings.moderation_blocked_output_patterns),
            external=ext,
        )

    def check_input(self, user_text: str) -> Optional[str]:
        raw = user_text or ""
        norm = normalize_for_moderation(raw)
        hit = _match_substrings(norm, self.blocked_input)
        if hit:
            return hit
        hit = _match_patterns(raw, self.input_patterns)
        if hit:
            return hit
        hit = _match_patterns(norm, self.input_patterns)
        if hit:
            return hit
        return self.external.check_input(raw)

    def check_output(self, text: str) -> Optional[str]:
        raw = text or ""
        norm = normalize_for_moderation(raw)
        hit = _match_substrings(norm, self.blocked_output)
        if hit:
            return hit
        hit = _match_patterns(raw, self.output_patterns)
        if hit:
            return hit
        hit = _match_patterns(norm, self.output_patterns)
        if hit:
            return hit
        return self.external.check_output(raw)


def check_input_blocked(
    user_text: str,
    *,
    blocked: Sequence[str] = (),
    engine: Optional[ModerationEngine] = None,
) -> Optional[str]:
    if engine is not None:
        return engine.check_input(user_text)
    phrases = tuple(blocked) if blocked else _FALLBACK_BLOCKED
    norm = normalize_for_moderation(user_text)
    return _match_substrings(norm, phrases)


def check_output_blocked(
    text: str,
    *,
    blocked: Sequence[str] = (),
    engine: Optional[ModerationEngine] = None,
) -> Optional[str]:
    if engine is not None:
        return engine.check_output(text)
    phrases = tuple(blocked) if blocked else _FALLBACK_BLOCKED
    norm = normalize_for_moderation(text)
    return _match_substrings(norm, phrases)
