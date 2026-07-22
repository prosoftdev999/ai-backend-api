from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.document import Document
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentTaskResponse,
)
from app.tasks.document_tasks import process_document


router = APIRouter(prefix="/documents", tags=["Documents"])

ALLOWED_SUFFIXES = {".pdf", ".docx", ".txt", ".md", ".markdown"}


async def get_document_or_404(
    document_id: uuid.UUID,
    db: AsyncSession,
) -> Document:
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found.",
        )

    return document


@router.post(
    "",
    response_model=DocumentTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
) -> DocumentTaskResponse:
    original_filename = Path(file.filename or "upload").name
    suffix = Path(original_filename).suffix.lower()

    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Supported files: PDF, DOCX, TXT, MD.",
        )

    content = await file.read()
    max_bytes = settings.max_upload_size_mb * 1024 * 1024

    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded file is empty.",
        )

    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Maximum upload size is {settings.max_upload_size_mb} MB.",
        )

    document_id = uuid.uuid4()
    stored_filename = f"{document_id}{suffix}"
    destination = settings.upload_directory / stored_filename
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)

    document = Document(
        id=document_id,
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type=file.content_type or "application/octet-stream",
        file_size=len(content),
        status="pending",
        metadata_json={},
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    task = process_document.delay(str(document.id))

    return DocumentTaskResponse(
        document=DocumentResponse.model_validate(document),
        task_id=task.id,
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> DocumentListResponse:
    total = (
        await db.execute(select(func.count()).select_from(Document))
    ).scalar_one()

    documents = list(
        (
            await db.execute(
                select(Document)
                .order_by(Document.created_at.desc())
                .offset(offset)
                .limit(limit)
            )
        )
        .scalars()
        .all()
    )

    return DocumentListResponse(
        items=[DocumentResponse.model_validate(item) for item in documents],
        total=total,
    )


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Document:
    return await get_document_or_404(document_id, db)


@router.post(
    "/{document_id}/reprocess",
    response_model=DocumentTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def reprocess_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> DocumentTaskResponse:
    document = await get_document_or_404(document_id, db)
    document.status = "pending"
    document.error_message = None

    await db.commit()
    await db.refresh(document)

    task = process_document.delay(str(document.id))

    return DocumentTaskResponse(
        document=DocumentResponse.model_validate(document),
        task_id=task.id,
    )


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> None:
    document = await get_document_or_404(document_id, db)
    file_path = settings.upload_directory / document.stored_filename

    await db.execute(delete(Document).where(Document.id == document_id))
    await db.commit()

    file_path.unlink(missing_ok=True)
