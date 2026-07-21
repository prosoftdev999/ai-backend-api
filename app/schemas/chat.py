import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ChatRole = Literal["system", "user", "assistant"]


class ChatSessionCreate(BaseModel):
    title: str = Field(
        default="New conversation",
        min_length=1,
        max_length=255,
    )


class ChatSessionUpdate(BaseModel):
    title: str = Field(
        min_length=1,
        max_length=255,
    )


class ChatMessageCreate(BaseModel):
    content: str = Field(
        min_length=1,
        max_length=50_000,
    )


class ChatMessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    session_id: uuid.UUID
    role: ChatRole
    content: str
    model: str | None
    created_at: datetime


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatSessionDetail(ChatSessionResponse):
    messages: list[ChatMessageResponse]


class ChatCompletionResponse(BaseModel):
    session_id: uuid.UUID
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse


class ChatSessionListResponse(BaseModel):
    items: list[ChatSessionResponse]
    total: int