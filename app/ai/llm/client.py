"""Provider-agnostic chat types, plus an OpenAI adapter that implements LLMClient."""

import json
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from openai import AsyncOpenAI

from app.core.config import Settings


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


class LLMClient(Protocol):
    """Provider-agnostic chat interface; concrete clients (e.g. OpenAIClient) implement this."""

    async def chat(self, messages: list[Message], tools: list[ToolDef]) -> LLMResponse: ...


def _to_openai_message(message: Message) -> dict[str, Any]:
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
    return payload


def _to_openai_tool(tool: ToolDef) -> dict[str, Any]:
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        },
    }


class OpenAIClient:
    """Adapts the OpenAI chat.completions API to the neutral LLMClient protocol."""

    def __init__(self, api_key: str, model: str, max_tokens: int, timeout_s: float) -> None:
        self._client = AsyncOpenAI(api_key=api_key, timeout=timeout_s)
        self._model = model
        self._max_tokens = max_tokens

    async def chat(self, messages: list[Message], tools: list[ToolDef]) -> LLMResponse:
        """Translate neutral types -> OpenAI chat.completions format and back.

        Provider exceptions (auth, timeout, rate limit, ...) propagate to the
        caller; ChatService is responsible for catching them.
        """
        response = await self._client.chat.completions.create(
            model=self._model,
            max_tokens=self._max_tokens,
            messages=[_to_openai_message(m) for m in messages],
            tools=[_to_openai_tool(t) for t in tools] if tools else None,
        )
        choice_message = response.choices[0].message
        tool_calls = [
            ToolCall(
                id=tc.id,
                name=tc.function.name,
                arguments=json.loads(tc.function.arguments) if tc.function.arguments else {},
            )
            for tc in (choice_message.tool_calls or [])
        ]
        return LLMResponse(content=choice_message.content, tool_calls=tool_calls)


def get_llm_client(settings: Settings) -> LLMClient:
    """Construct the LLMClient for the configured provider; raises on an unknown provider."""
    match settings.llm_provider:
        case "openai":
            return OpenAIClient(
                settings.openai_api_key,
                settings.llm_model,
                settings.llm_max_tokens,
                settings.llm_timeout_s,
            )
        case _:
            raise ValueError(f"Unknown LLM provider: {settings.llm_provider}")
