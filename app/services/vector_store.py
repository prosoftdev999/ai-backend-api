from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentChunk


@dataclass(slots=True)
class VectorSearchHit:
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    content: str
    chunk_index: int
    score: float


async def search_similar_chunks(
    db: AsyncSession,
    *,
    query_embedding: list[float],
    limit: int,
    document_id: uuid.UUID | None = None,
) -> list[VectorSearchHit]:
    distance = DocumentChunk.embedding.cosine_distance(query_embedding)

    statement: Select = (
        select(
            DocumentChunk.id.label("chunk_id"),
            DocumentChunk.document_id,
            Document.original_filename.label("filename"),
            DocumentChunk.content,
            DocumentChunk.chunk_index,
            (1 - distance).label("score"),
        )
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.embedding.is_not(None))
        .order_by(distance)
        .limit(limit)
    )

    if document_id is not None:
        statement = statement.where(DocumentChunk.document_id == document_id)

    result = await db.execute(statement)

    return [
        VectorSearchHit(
            chunk_id=row.chunk_id,
            document_id=row.document_id,
            filename=row.filename,
            content=row.content,
            chunk_index=row.chunk_index,
            score=float(row.score),
        )
        for row in result.all()
    ]
