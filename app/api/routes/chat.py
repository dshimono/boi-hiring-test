import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.chat_service import ChatService
from app.ai.llm.client import Message
from app.api.deps import get_current_user, get_db
from app.core.exceptions import ChatUnavailableError
from app.schemas.chat import ChatRequest, ChatResponse

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(get_current_user)])


@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)) -> ChatResponse:
    """Ask a question about ad performance, grounded in tool calls against the real data."""
    history = [Message(role=turn.role, content=turn.content) for turn in request.history]
    try:
        answer = await ChatService(db).ask(request.message, history)
    except Exception as exc:
        logger.exception("chat_route_failed")
        raise ChatUnavailableError() from exc
    return ChatResponse(message=answer)
