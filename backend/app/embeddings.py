"""Embedding provider interface and implementations"""
from abc import ABC, abstractmethod
from typing import List
import asyncio
from openai import AsyncOpenAI
from app.config import settings


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers"""

    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text string"""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of texts"""
        pass

    @property
    @abstractmethod
    def embedding_dimension(self) -> int:
        """Return the dimension of embeddings produced by this provider"""
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider using text-embedding-3-small model"""

    MODEL = "text-embedding-3-small"
    DIMENSION = 1536

    def __init__(self, api_key: str = None):
        """Initialize OpenAI embedding provider"""
        self.client = AsyncOpenAI(api_key=api_key or settings.openai_api_key)

    async def embed_text(self, text: str) -> List[float]:
        """Embed a single text string"""
        embeddings = await self.embed_batch([text])
        return embeddings[0]

    async def embed_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """Embed a batch of texts with rate limiting"""
        all_embeddings = []

        # Process in batches to respect rate limits
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            response = await self.client.embeddings.create(
                model=self.MODEL,
                input=batch,
            )

            # Extract embeddings and maintain order
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

            # Add delay between batches to respect rate limits
            if i + batch_size < len(texts):
                await asyncio.sleep(0.5)

        return all_embeddings

    @property
    def embedding_dimension(self) -> int:
        """Return embedding dimension"""
        return self.DIMENSION


class MockEmbeddingProvider(EmbeddingProvider):
    """Mock embedding provider for testing (without API calls)"""

    DIMENSION = 1536

    async def embed_text(self, text: str) -> List[float]:
        """Return mock embedding"""
        embeddings = await self.embed_batch([text])
        return embeddings[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Return mock embeddings (consistent but fake)"""
        embeddings = []
        for text in texts:
            # Generate consistent mock embedding based on text hash
            hash_value = hash(text)
            embedding = [
                ((hash_value >> i) & 1) * 0.5 + 0.25
                for i in range(self.DIMENSION)
            ]
            embeddings.append(embedding)
        return embeddings

    @property
    def embedding_dimension(self) -> int:
        """Return embedding dimension"""
        return self.DIMENSION


def get_embedding_provider(use_mock: bool = False) -> EmbeddingProvider:
    """Factory function to get embedding provider"""
    if use_mock or not settings.openai_api_key:
        return MockEmbeddingProvider()
    return OpenAIEmbeddingProvider()
