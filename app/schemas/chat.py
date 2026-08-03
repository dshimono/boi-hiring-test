from typing import Literal

from pydantic import BaseModel, Field


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=1000)


class ChatRequest(BaseModel):
    message: str = Field(max_length=1000)
    history: list[ChatTurn] = Field(default_factory=list, max_length=10)
