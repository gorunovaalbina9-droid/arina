from __future__ import annotations

import json
import re
import uuid
from typing import Any, Iterator, List, Literal, Optional, Union

from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.tools import BaseTool
from pydantic import Field, PrivateAttr, model_validator

StaticStep = Union[str, dict[str, Any]]


def _tool_call_dict(name: str, args: dict[str, Any], *, call_id: Optional[str] = None) -> dict[str, Any]:
    return {
        "name": name,
        "args": args,
        "id": call_id or f"static-{uuid.uuid4().hex[:12]}",
        "type": "tool_call",
    }


class StaticChatModel(BaseChatModel):
    """
    Детерминированные ответы без внешнего API (локальная разработка / CI).

    steps/responses: строка или dict:
      - {"text": "..."} / {"content": "..."}
      - {"tool_calls": [{"name": "...", "args": {...}, "id": "..."}]}
    """

    responses: List[StaticStep] = Field(default_factory=lambda: ["Привет!"])
    reply: Optional[str] = Field(default=None, description="Синоним одного текстового ответа")
    _idx: int = PrivateAttr(default=0)

    @model_validator(mode="after")
    def _reply_to_responses(self) -> StaticChatModel:
        if self.reply is not None and str(self.reply).strip():
            object.__setattr__(self, "responses", [str(self.reply)])
        return self

    @property
    def _llm_type(self) -> str:
        return "static-chat"

    @classmethod
    def with_tool_then_text(
        cls,
        *,
        tool_name: str,
        tool_args: dict[str, Any],
        text: str,
        call_id: str = "static-1",
    ) -> StaticChatModel:
        """Удобный конструктор для E2E: tool_call → финальный текст."""
        return cls(
            responses=[
                {"tool_calls": [_tool_call_dict(tool_name, tool_args, call_id=call_id)]},
                text,
            ]
        )

    def bind_tools(
        self,
        tools: list[BaseTool | dict[str, Any] | type],
        *,
        tool_choice: Optional[str] = None,
        **kwargs: Any,
    ) -> BaseChatModel:
        _ = (tools, tool_choice, kwargs)
        return self

    def _next_message(self) -> AIMessage:
        steps = self.responses or [""]
        i = min(self._idx, len(steps) - 1)
        step = steps[i]
        self._idx = min(self._idx + 1, len(steps))

        if isinstance(step, str):
            return AIMessage(content=step)

        if isinstance(step, dict):
            raw_calls = step.get("tool_calls") or []
            tool_calls: list[dict[str, Any]] = []
            for tc in raw_calls:
                if not isinstance(tc, dict):
                    continue
                name = tc.get("name")
                if not name:
                    continue
                args = tc.get("args") or {}
                if not isinstance(args, dict):
                    args = {}
                tool_calls.append(
                    _tool_call_dict(str(name), args, call_id=str(tc.get("id") or f"static-{len(tool_calls)}"))
                )
            text = str(step.get("text") or step.get("content") or "")
            if tool_calls:
                return AIMessage(content=text, tool_calls=tool_calls)
            return AIMessage(content=text)

        return AIMessage(content=str(step))

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        msg = self._next_message()
        return ChatResult(generations=[ChatGeneration(message=msg)])

    async def _agenerate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[AsyncCallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        return self._generate(messages, stop=stop, run_manager=None, **kwargs)

    def _stream(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> Iterator[ChatGeneration]:
        yield ChatGeneration(message=self._next_message())
