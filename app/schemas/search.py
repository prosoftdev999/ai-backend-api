import uuid

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=5000)
    limit: int = Field(default=5, ge=1, le=50)
    document_id: uuid.UUID | None = None


class SearchResult(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    filename: str
    content: str
    chunk_index: int
    score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class RAGRequest(BaseModel):
    question: str = Field(min_length=1, max_length=5000)
    document_id: uuid.UUID | None = None
    limit: int = Field(default=5, ge=1, le=20)


class RAGSource(BaseModel):
    document_id: uuid.UUID
    filename: str
    chunk_index: int
    score: float
    content: str


class RAGResponse(BaseModel):
    answer: str
    sources: list[RAGSource]
