import json

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chat_service import (
    ITERATION_CAP_MESSAGE,
    MAX_TOOL_ITERATIONS,
    PROVIDER_ERROR_MESSAGE,
    ChatService,
)
from app.ai.llm.client import LLMResponse, Message, ToolCall, ToolDef


class FakeLLMClient:
    """Scripted LLMClient: returns queued responses in order, or raises a queued exception."""

    def __init__(self, responses: list[LLMResponse | Exception]) -> None:
        self._responses = list(responses)
        self.calls: list[list[Message]] = []

    async def chat(self, messages: list[Message], tools: list[ToolDef]) -> LLMResponse:
        self.calls.append(messages)
        response = self._responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def _tool_call_response(call_id: str, tool_name: str, arguments: dict | None = None) -> LLMResponse:
    return LLMResponse(
        content=None,
        tool_calls=[ToolCall(id=call_id, name=tool_name, arguments=arguments or {})],
    )


@pytest.mark.asyncio
async def test_ask_tool_call_then_final_answer(db_session: AsyncSession) -> None:
    fake = FakeLLMClient(
        [
            _tool_call_response("call_1", "get_ad_performance"),
            LLMResponse(content="Here's the answer.", tool_calls=[]),
        ]
    )
    service = ChatService(db_session, fake)

    result = await service.ask("which ad has the highest ctr?", [])

    assert result == "Here's the answer."
    assert len(fake.calls) == 2
    second_call_messages = fake.calls[1]
    tool_message = next(m for m in second_call_messages if m.role == "tool")
    assert tool_message.tool_call_id == "call_1"
    assert json.loads(tool_message.content)["metric"] == "ctr"


@pytest.mark.asyncio
async def test_ask_provider_error_returns_friendly_message(db_session: AsyncSession) -> None:
    fake = FakeLLMClient([TimeoutError("upstream timed out")])
    service = ChatService(db_session, fake)

    result = await service.ask("which ad has the highest ctr?", [])

    assert result == PROVIDER_ERROR_MESSAGE


@pytest.mark.asyncio
async def test_ask_unknown_tool_call_recovers(db_session: AsyncSession) -> None:
    fake = FakeLLMClient(
        [
            _tool_call_response("call_1", "delete_everything"),
            LLMResponse(content="I don't have that capability.", tool_calls=[]),
        ]
    )
    service = ChatService(db_session, fake)

    result = await service.ask("delete all my data", [])

    assert result == "I don't have that capability."
    tool_message = next(m for m in fake.calls[1] if m.role == "tool")
    assert json.loads(tool_message.content) == {"error": "unknown tool: delete_everything"}


@pytest.mark.asyncio
async def test_ask_iteration_cap_triggers(db_session: AsyncSession) -> None:
    fake = FakeLLMClient(
        [_tool_call_response(f"call_{i}", "get_ad_performance") for i in range(MAX_TOOL_ITERATIONS)]
    )
    service = ChatService(db_session, fake)

    result = await service.ask("keep going forever", [])

    assert result == ITERATION_CAP_MESSAGE
    assert len(fake.calls) == MAX_TOOL_ITERATIONS
