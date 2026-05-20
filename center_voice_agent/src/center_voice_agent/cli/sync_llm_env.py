"""
Скопировать OPENAI_API_KEY из voice_assistant/.env в center_voice_agent/.env (локально).

Не выводит ключ. Не коммитьте .env.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
MONOREPO = REPO_ROOT.parent
VOICE_ENV = MONOREPO / "voice_assistant" / ".env"
CENTER_ENV = REPO_ROOT / ".env"


def _parse_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    if not path.is_file():
        return out
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def sync(*, dry_run: bool = False) -> bool:
    voice = _parse_env(VOICE_ENV)
    key = voice.get("OPENAI_API_KEY") or ""
    if not key or key.lower().startswith("sk-your") or key == "replace_me":
        print("Нет OPENAI_API_KEY в voice_assistant/.env")
        return False

    if not CENTER_ENV.is_file():
        example = REPO_ROOT / ".env.example"
        if example.is_file():
            CENTER_ENV.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
        else:
            print("Нет .env и .env.example")
            return False

    text = CENTER_ENV.read_text(encoding="utf-8")
    repl = {
        "LLM_API_KEY": key,
        "LLM_BASE_URL": voice.get("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "LLM_MODEL": voice.get("OPENAI_MODEL") or voice.get("LLM_MODEL") or "gpt-4o-mini",
    }
    for name, val in repl.items():
        if re.search(rf"^{name}=", text, flags=re.MULTILINE):
            text = re.sub(rf"^{name}=.*$", f"{name}={val}", text, count=1, flags=re.MULTILINE)
        else:
            text += f"\n{name}={val}\n"

    if dry_run:
        print("OK: можно записать LLM_* в center_voice_agent/.env (ключ не показан)")
        return True

    CENTER_ENV.write_text(text, encoding="utf-8")
    print(f"OK: обновлён {CENTER_ENV} (LLM_API_KEY, LLM_BASE_URL, LLM_MODEL)")
    return True


def main() -> None:
    dry = "--dry-run" in sys.argv
    raise SystemExit(0 if sync(dry_run=dry) else 1)


if __name__ == "__main__":
    main()
