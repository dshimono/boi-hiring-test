import json
from collections.abc import AsyncGenerator

import structlog
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chat_service import ChatService
from app.ai.llm.client import Message
from app.api.deps import get_current_user, get_db
from app.schemas.chat import ChatRequest

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(get_current_user)])

CHAT_UNAVAILABLE_MESSAGE = "Chat is temporarily unavailable. Please try again later."


def _sse(event: dict) -> str:
    return f"data: {json.dumps(event)}\n\n"


async def _event_stream(
    message: str, history: list[Message], db: AsyncSession
) -> AsyncGenerator[str]:
    try:
        async for token in ChatService(db).ask_stream(message, history):
            yield _sse({"type": "token", "text": token})
    except Exception:
        # Streaming has already started (status 200 sent), so a failure can only
        # be surfaced as an event, never as an HTTP status.
        logger.exception("chat_route_failed")
        yield _sse({"type": "error", "message": CHAT_UNAVAILABLE_MESSAGE})
        return
    yield _sse({"type": "done"})


@router.post("")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)) -> StreamingResponse:
    """Ask a question about ads and ads performance, grounded in tool calls against the real data.

    Streams the answer as Server-Sent Events: `token` deltas, then `done`, or
    `error` if the provider/tooling fails partway through.
    """
    history = [Message(role=turn.role, content=turn.content) for turn in request.history]
    return StreamingResponse(
        _event_stream(request.message, history, db), media_type="text/event-stream"
    )
