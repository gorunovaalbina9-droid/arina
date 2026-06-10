from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque, Iterable, Literal

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage


Role = Literal["user", "assistant"]


@dataclass
class ShortTermMemory:
    """Последние N сообщений user/assistant (N = Settings.short_term_message_limit, обычно пары×2)."""

    max_turns: int = 15
    _messages: Deque[tuple[Role, str]] = field(init=False)

    def __post_init__(self) -> None:
        self._messages = deque(maxlen=self.max_turns)

    def append_user(self, text: str) -> None:
        self._messages.append(("user", text))

    def append_assistant(self, text: str) -> None:
        self._messages.append(("assistant", text))

    def as_langchain(self, *, system_preamble: str | None = None) -> list[BaseMessage]:
        out: list[BaseMessage] = []
        if system_preamble:
            out.append(SystemMessage(content=system_preamble))
        for role, text in self._messages:
            if role == "user":
                out.append(HumanMessage(content=text))
            else:
                out.append(AIMessage(content=text))
        return out

    def snapshot(self) -> list[tuple[Role, str]]:
        return list(self._messages)

    @classmethod
    def from_pairs(cls, pairs: Iterable[tuple[Role, str]], *, max_turns: int = 15) -> ShortTermMemory:
        mem = cls(max_turns=max_turns)
        tail = list(pairs)[-max_turns:]
        for role, text in tail:
            if role == "user":
                mem.append_user(text)
            else:
                mem.append_assistant(text)
        return mem

    def __len__(self) -> int:
        return len(self._messages)
