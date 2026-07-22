from __future__ import annotations

import uuid
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.services.embeddings import embedding_service
from app.services.llm import LLMMessage, llm_service
from app.services.vector_store import VectorSearchHit, search_similar_chunks


@dataclass(slots=True)
class RAGResult:
    answer: str
    sources: list[VectorSearchHit]


async def answer_with_rag(
    db: AsyncSession,
    *,
    question: str,
    document_id: uuid.UUID | None = None,
    limit: int | None = None,
) -> RAGResult:
    query_embedding = await embedding_service.create_embedding(question)

    sources = await search_similar_chunks(
        db,
        query_embedding=query_embedding,
        document_id=document_id,
        limit=limit or settings.vector_search_limit,
    )

    if not sources:
        return RAGResult(
            answer="I could not find relevant document context for that question.",
            sources=[],
        )

    context = "\n\n".join(
        (
            f"[Source {index}: {hit.filename}, chunk {hit.chunk_index}]\n"
            f"{hit.content}"
        )
        for index, hit in enumerate(sources, start=1)
    )

    prompt = (
        "Answer the question using only the supplied document context. "
        "If the answer is not present, say that the documents do not contain "
        "enough information. Cite sources in the form [Source 1].\n\n"
        f"Context:\n{context}\n\n"
        f"Question:\n{question}"
    )

    answer = await llm_service.generate_reply(
        [LLMMessage(role="user", content=prompt)]
    )

    return RAGResult(answer=answer, sources=sources)
