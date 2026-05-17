from __future__ import annotations

from typing import Any, Iterator, List, Optional

from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import Field, PrivateAttr


class StaticChatModel(BaseChatModel):
    """Детерминированные ответы без внешнего API (локальная разработка / CI)."""

    responses: List[str] = Field(default_factory=lambda: ["Привет!"])
    _idx: int = PrivateAttr(default=0)

    @property
    def _llm_type(self) -> str:
        return "static-chat"

    def _next_text(self) -> str:
        if not self.responses:
            return ""
        i = min(self._idx, len(self.responses) - 1)
        text = self.responses[i]
        self._idx = min(self._idx + 1, len(self.responses))
        return text

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        msg = AIMessage(content=self._next_text())
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
        yield ChatGeneration(message=AIMessage(content=self._next_text()))
