from __future__ import annotations

from openai import AsyncOpenAI

from app.core.config import settings


class EmbeddingService:
    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            max_retries=2,
        )

    async def create_embedding(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(
            model=settings.embedding_model,
            input=text,
            encoding_format="float",
        )
        return list(response.data[0].embedding)

    async def create_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        response = await self.client.embeddings.create(
            model=settings.embedding_model,
            input=texts,
            encoding_format="float",
        )

        ordered = sorted(response.data, key=lambda item: item.index)
        return [list(item.embedding) for item in ordered]

    async def close(self) -> None:
        await self.client.close()


embedding_service = EmbeddingService()
