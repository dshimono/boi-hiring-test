import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.llm.client import LLMClient, Message, get_llm_client
from app.ai.prompts import build_system_prompt
from app.ai.tools import TOOLS, execute
from app.core.config import settings
from app.services.metrics import get_dataset_date_range, list_ads

logger = structlog.get_logger(__name__)

MAX_TOOL_ITERATIONS = 5
ITERATION_CAP_MESSAGE = "I couldn't complete that — try rephrasing."
PROVIDER_ERROR_MESSAGE = "Sorry, I couldn't reach the AI assistant right now. Please try again."


class ChatService:
    """Runs the tool-calling loop for one chat turn against a real LLM provider."""

    def __init__(self, session: AsyncSession, llm_client: LLMClient | None = None) -> None:
        self.session = session
        self.llm_client = llm_client or get_llm_client(settings)

    async def ask(self, message: str, history: list[Message]) -> str:
        dataset_start, dataset_end = await get_dataset_date_range(self.session)
        ads = await list_ads(self.session)
        messages = [
            Message(role="system", content=build_system_prompt(dataset_start, dataset_end, ads)),
            *history,
            Message(role="user", content=message),
        ]
        tool_defs = [tool.definition() for tool in TOOLS]

        for _ in range(MAX_TOOL_ITERATIONS):
            try:
                response = await self.llm_client.chat(messages, tool_defs)
            except Exception:
                logger.exception("chat_provider_error")
                return PROVIDER_ERROR_MESSAGE

            if not response.tool_calls:
                return response.content or ""

            messages.append(
                Message(
                    role="assistant", content=response.content or "", tool_calls=response.tool_calls
                )
            )
            for tool_call in response.tool_calls:
                result = await execute(self.session, tool_call.name, tool_call.arguments)
                messages.append(Message(role="tool", content=result, tool_call_id=tool_call.id))

        logger.warning("chat_iteration_cap_reached")
        return ITERATION_CAP_MESSAGE
