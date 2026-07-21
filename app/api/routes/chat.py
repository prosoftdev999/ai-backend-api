import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.db.session import get_db
from app.models.chat import ChatMessage, ChatSession
from app.schemas.chat import (
    ChatCompletionResponse,
    ChatMessageCreate,
    ChatSessionCreate,
    ChatSessionDetail,
    ChatSessionListResponse,
    ChatSessionResponse,
    ChatSessionUpdate,
)
from app.services.llm import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMMessage,
    LLMRateLimitError,
    LLMRequestError,
    LLMServiceError,
    llm_service,
)


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


def get_llm_http_exception(exc: LLMServiceError) -> HTTPException:
    if isinstance(exc, LLMAuthenticationError):
        return HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The server's LLM credentials are invalid.",
        )

    if isinstance(exc, LLMRateLimitError):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        )

    if isinstance(exc, LLMRequestError):
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    if isinstance(exc, LLMConnectionError):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    return HTTPException(
        status_code=status.HTTP_502_BAD_GATEWAY,
        detail=str(exc),
    )


async def get_session_or_404(
    session_id: uuid.UUID,
    db: AsyncSession,
    *,
    include_messages: bool = False,
) -> ChatSession:
    statement = select(ChatSession).where(
        ChatSession.id == session_id
    )

    if include_messages:
        statement = statement.options(
            selectinload(ChatSession.messages)
        )

    result = await db.execute(statement)
    chat_session = result.scalar_one_or_none()

    if chat_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    return chat_session


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_chat_session(
    payload: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
) -> ChatSession:
    chat_session = ChatSession(title=payload.title.strip())

    db.add(chat_session)
    await db.commit()
    await db.refresh(chat_session)

    return chat_session


@router.get(
    "/sessions",
    response_model=ChatSessionListResponse,
)
async def list_chat_sessions(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionListResponse:
    total_result = await db.execute(
        select(func.count()).select_from(ChatSession)
    )
    total = total_result.scalar_one()

    sessions_result = await db.execute(
        select(ChatSession)
        .order_by(ChatSession.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )

    sessions = list(sessions_result.scalars().all())

    return ChatSessionListResponse(
        items=[
            ChatSessionResponse.model_validate(session)
            for session in sessions
        ],
        total=total,
    )


@router.get(
    "/sessions/{session_id}",
    response_model=ChatSessionDetail,
)
async def get_chat_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> ChatSession:
    return await get_session_or_404(
        session_id,
        db,
        include_messages=True,
    )


@router.patch(
    "/sessions/{session_id}",
    response_model=ChatSessionResponse,
)
async def update_chat_session(
    session_id: uuid.UUID,
    payload: ChatSessionUpdate,
    db: AsyncSession = Depends(get_db),
) -> ChatSession:
    chat_session = await get_session_or_404(session_id, db)

    chat_session.title = payload.title.strip()
    chat_session.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(chat_session)

    return chat_session


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_chat_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Response:
    await get_session_or_404(session_id, db)

    await db.execute(
        delete(ChatSession).where(ChatSession.id == session_id)
    )
    await db.commit()

    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatCompletionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def send_chat_message(
    session_id: uuid.UUID,
    payload: ChatMessageCreate,
    db: AsyncSession = Depends(get_db),
) -> ChatCompletionResponse:
    chat_session = await get_session_or_404(
        session_id,
        db,
        include_messages=True,
    )

    user_content = payload.content.strip()

    user_message = ChatMessage(
        session_id=chat_session.id,
        role="user",
        content=user_content,
        model=None,
    )

    db.add(user_message)
    await db.flush()

    conversation = [
        LLMMessage(
            role=message.role,
            content=message.content,
        )
        for message in chat_session.messages
        if message.role in {"user", "assistant"}
    ]

    conversation.append(
        LLMMessage(
            role="user",
            content=user_content,
        )
    )

    try:
        assistant_content = await llm_service.generate_reply(
            conversation
        )
    except LLMServiceError as exc:
        await db.rollback()
        raise get_llm_http_exception(exc) from exc

    assistant_message = ChatMessage(
        session_id=chat_session.id,
        role="assistant",
        content=assistant_content,
        model=settings.llm_model,
    )

    db.add(assistant_message)

    chat_session.updated_at = datetime.now(timezone.utc)

    if chat_session.title == "New conversation":
        chat_session.title = user_content[:100]

    await db.commit()
    await db.refresh(user_message)
    await db.refresh(assistant_message)

    return ChatCompletionResponse(
        session_id=chat_session.id,
        user_message=user_message,
        assistant_message=assistant_message,
    )