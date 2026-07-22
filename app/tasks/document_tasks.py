from __future__ import annotations

import asyncio
import uuid

from sqlalchemy import delete, select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.document import Document, DocumentChunk
from app.services.document_parser import extract_text
from app.services.embeddings import embedding_service
from app.tasks.celery_app import celery_app
from app.utils.chunking import split_text


@celery_app.task(
    bind=True,
    name="app.tasks.document_tasks.process_document",
    autoretry_for=(ConnectionError, TimeoutError),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def process_document(self, document_id: str) -> dict[str, object]:
    return asyncio.run(_process_document(uuid.UUID(document_id)))


async def _process_document(document_id: uuid.UUID) -> dict[str, object]:
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if document is None:
            return {"status": "missing", "document_id": str(document_id)}

        document.status = "processing"
        document.error_message = None
        await db.commit()

        try:
            file_path = settings.upload_directory / document.stored_filename
            text = extract_text(file_path, document.content_type)

            if not text.strip():
                raise ValueError("No text could be extracted from this document.")

            chunks = split_text(
                text,
                chunk_size=settings.chunk_size,
                chunk_overlap=settings.chunk_overlap,
            )

            embeddings = await embedding_service.create_embeddings(chunks)

            await db.execute(
                delete(DocumentChunk).where(
                    DocumentChunk.document_id == document.id
                )
            )

            for index, (chunk, embedding) in enumerate(
                zip(chunks, embeddings, strict=True)
            ):
                db.add(
                    DocumentChunk(
                        document_id=document.id,
                        chunk_index=index,
                        content=chunk,
                        token_count=None,
                        metadata_json={},
                        embedding=embedding,
                    )
                )

            document.status = "completed"
            document.metadata_json = {
                **document.metadata_json,
                "character_count": len(text),
                "chunk_count": len(chunks),
            }

            await db.commit()

            return {
                "status": "completed",
                "document_id": str(document.id),
                "chunk_count": len(chunks),
            }

        except Exception as exc:
            await db.rollback()

            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if document is not None:
                document.status = "failed"
                document.error_message = str(exc)[:2000]
                await db.commit()

            raise
