from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.search import (
    RAGRequest,
    RAGResponse,
    RAGSource,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from app.services.embeddings import embedding_service
from app.services.rag import answer_with_rag
from app.services.vector_store import search_similar_chunks


router = APIRouter(tags=["Search and RAG"])


@router.post("/search", response_model=SearchResponse)
async def vector_search(
    payload: SearchRequest,
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    query_embedding = await embedding_service.create_embedding(payload.query)

    hits = await search_similar_chunks(
        db,
        query_embedding=query_embedding,
        document_id=payload.document_id,
        limit=payload.limit,
    )

    return SearchResponse(
        query=payload.query,
        results=[
            SearchResult(
                chunk_id=hit.chunk_id,
                document_id=hit.document_id,
                filename=hit.filename,
                content=hit.content,
                chunk_index=hit.chunk_index,
                score=hit.score,
            )
            for hit in hits
        ],
    )


@router.post("/rag", response_model=RAGResponse)
async def rag_question(
    payload: RAGRequest,
    db: AsyncSession = Depends(get_db),
) -> RAGResponse:
    result = await answer_with_rag(
        db,
        question=payload.question,
        document_id=payload.document_id,
        limit=payload.limit,
    )

    return RAGResponse(
        answer=result.answer,
        sources=[
            RAGSource(
                document_id=hit.document_id,
                filename=hit.filename,
                chunk_index=hit.chunk_index,
                score=hit.score,
                content=hit.content,
            )
            for hit in result.sources
        ],
    )
