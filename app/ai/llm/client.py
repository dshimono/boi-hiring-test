"""Chat types shared across the tool-calling loop, plus the OpenAI client that speaks them."""

import json
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal, cast

from openai import AsyncOpenAI, omit
from openai.types.chat import ChatCompletionMessageParam, ChatCompletionToolParam


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: str | None = None  # set on role="tool" results
    tool_calls: list[ToolCall] = field(default_factory=list)  # set on assistant messages


@dataclass
class ToolDef:
    name: str
    description: str
    parameters: dict[str, Any]  # JSON schema


@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall]


@dataclass
class StreamChunk:
    """Either a text delta (`text` set) or the final accumulated response (`response` set)."""

    text: str | None = None
    response: LLMResponse | None = None


def _to_openai_message(message: Message) -> ChatCompletionMessageParam:
    payload: dict[str, Any] = {"role": message.role, "content": message.content}
    if message.tool_call_id is not None:
        payload["tool_call_id"] = message.tool_call_id
    if message.tool_calls:
        payload["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.name, "arguments": json.dumps(tc.arguments)},
            }
            for tc in message.tool_calls
        ]
    return cast(ChatCompletionMessageParam, payload)


def _to_openai_tool(tool: ToolDef) -> ChatCompletionToolParam:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


class OpenAIClient:
    """Adapts the OpenAI chat.completions API to the shared Message/ToolDef types."""

    def __init__(self, api_key: str, model: str, max_tokens: int, timeout_s: float) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout_s)
        self._model = model
        self._max_tokens = max_tokens

    async def chat_stream(
        self, messages: list[Message], tools: list[ToolDef]
    ) -> AsyncIterator[StreamChunk]:
        """Translate neutral types -> OpenAI chat.completions format and back, streamed.

        Yields a StreamChunk per content delta, then one final StreamChunk carrying
        the accumulated LLMResponse (content + tool calls) once the stream ends.
        Provider exceptions (auth, timeout, rate limit, ...) propagate to the
        caller; ChatService is responsible for catching them.
        """
        stream = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[_to_openai_message(m) for m in messages],
            tools=[_to_openai_tool(t) for t in tools] if tools else omit,
            stream=True,
        )

        content_parts: list[str] = []
        # Tool-call fragments arrive by index: id/name on the first chunk for
        # that index, arguments dribble in across subsequent chunks.
        tool_calls_by_index: dict[int, dict[str, str]] = {}

        async for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta is None:
                continue
            if delta.content:
                content_parts.append(delta.content)
                yield StreamChunk(text=delta.content)
            for tc_delta in delta.tool_calls or []:
                entry = tool_calls_by_index.setdefault(
                    tc_delta.index, {"id": "", "name": "", "arguments": ""}
                )
                if tc_delta.id:
                    entry["id"] = tc_delta.id
                if tc_delta.function and tc_delta.function.name:
                    entry["name"] = tc_delta.function.name
                if tc_delta.function and tc_delta.function.arguments:
                    entry["arguments"] += tc_delta.function.arguments

        tool_calls = [
            ToolCall(
                id=entry["id"],
                name=entry["name"],
                arguments=json.loads(entry["arguments"]) if entry["arguments"] else {},
            )
            for entry in tool_calls_by_index.values()
        ]
        content = "".join(content_parts) or None
        yield StreamChunk(response=LLMResponse(content=content, tool_calls=tool_calls))
