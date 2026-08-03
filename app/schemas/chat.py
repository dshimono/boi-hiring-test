from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    # Holds past assistant answers too, which can run well past the 1000-char
    # cap on a fresh user message — llm_max_tokens=1000 caps generation at
    # roughly 4000 characters, so history needs the same headroom.
    content: str = Field(max_length=4000)


class ChatRequest(BaseModel):
    message: str = Field(max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=10)
