from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


class DataInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    date: date
    value: float = Field(ge=-100, le=100, allow_inf_nan=False, description="서울 일별 최고기온, °C")
    memo: str = Field(default="", max_length=500)


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid")
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=4000)


class ConversationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=120)
    messages: list[Message] = Field(min_length=1, max_length=30)


class ChatInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=1000)
    conversation_id: str | None = Field(default=None, max_length=100)
