from types import SimpleNamespace

import pytest

from app.ai.llm.client import Message, OpenAIClient


def _chunk(content: str | None = None, tool_calls: list | None = None) -> SimpleNamespace:
    delta = SimpleNamespace(content=content, tool_calls=tool_calls)
    return SimpleNamespace(choices=[SimpleNamespace(delta=delta)])


def _tool_call_delta(
    index: int,
    id: str | None = None,
    name: str | None = None,
    arguments: str | None = None,
) -> SimpleNamespace:
    function = SimpleNamespace(name=name, arguments=arguments) if (name or arguments) else None
    return SimpleNamespace(index=index, id=id, function=function)


def _fake_stream(chunks: list[SimpleNamespace]):
    async def gen():
        for chunk in chunks:
            yield chunk

    return gen()


@pytest.fixture
def client() -> OpenAIClient:
    return OpenAIClient(api_key="test-key", model="gpt-test", max_tokens=100, timeout_s=5.0)


@pytest.mark.asyncio
async def test_chat_stream_forwards_content_deltas(
    client: OpenAIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    chunks = [_chunk(content="Hello"), _chunk(content=" there")]

    async def fake_create(**kwargs):
        return _fake_stream(chunks)

    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)

    results = [c async for c in client.chat_stream([Message(role="user", content="hi")], [])]

    texts = [c.text for c in results if c.text is not None]
    final = [c.response for c in results if c.response is not None]
    assert texts == ["Hello", " there"]
    assert len(final) == 1
    assert final[0].content == "Hello there"
    assert final[0].tool_calls == []


@pytest.mark.asyncio
async def test_chat_stream_accumulates_tool_call_fragments_by_index(
    client: OpenAIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    chunks = [
        _chunk(
            tool_calls=[_tool_call_delta(0, id="call_1", name="get_ad_performance", arguments="")]
        ),
        _chunk(tool_calls=[_tool_call_delta(0, arguments='{"metric"')]),
        _chunk(tool_calls=[_tool_call_delta(0, arguments=': "ctr"}')]),
    ]

    async def fake_create(**kwargs):
        return _fake_stream(chunks)

    monkeypatch.setattr(client._client.chat.completions, "create", fake_create)

    results = [c async for c in client.chat_stream([Message(role="user", content="hi")], [])]

    final = next(c.response for c in results if c.response is not None)
    assert final.content is None
    assert len(final.tool_calls) == 1
    tool_call = final.tool_calls[0]
    assert tool_call.id == "call_1"
    assert tool_call.name == "get_ad_performance"
    assert tool_call.arguments == {"metric": "ctr"}
