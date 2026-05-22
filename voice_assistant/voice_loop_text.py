"""
Текстовый цикл пилота: ввод с клавиатуры → center_voice_agent → ответ.

Без ASR/TTS. Для голоса подключите распознавание/озвучку к ask_center_agent().
"""

from __future__ import annotations

import os
import uuid

from center_agent_bridge import ask_center_agent, use_center_agent


def main() -> None:
    if not use_center_agent():
        print("Задайте USE_CENTER_AGENT=true")
        raise SystemExit(1)
    sid = os.environ.get("PILOT_SESSION_ID") or f"pilot-{uuid.uuid4().hex[:10]}"
    child = os.environ.get("PILOT_CHILD_ID", "child-default")
    print(f"Сессия {sid}, ребёнок {child}. Пустая строка — выход.")
    while True:
        try:
            line = input("Вы: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            break
        reply = ask_center_agent(line, session_id=sid, child_profile_id=child)
        print(f"Арина: {reply}\n")


if __name__ == "__main__":
    main()
