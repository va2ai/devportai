"""Document retrieval service for semantic search"""
from typing import List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import array
from app.models import Chunk, Document
from app.embeddings import EmbeddingProvider


class RetrievalResult(BaseModel):
    """Single search result"""
    chunk_id: int
    document_id: int
    document_title: str
    document_filename: str
    content: str
    similarity_score: float
    chunk_index: int

    class Config:
        from_attributes = True


class DocumentRetrievalService:
    """Service for semantic search and document retrieval"""

    def __init__(self, embedding_provider: EmbeddingProvider):
        """
        Initialize retrieval service

        Args:
            embedding_provider: Provider for generating query embeddings
        """
        self.embedding_provider = embedding_provider

    async def retrieve(
        self,
        query: str,
        db_session: AsyncSession,
        top_k: int = 5,
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks for a query using semantic search

        Args:
            query: Search query text
            db_session: Database session
            top_k: Number of top results to return

        Returns:
            List of RetrievalResult objects sorted by similarity
        """
        if not query or not query.strip():
            return []

        # Generate embedding for query
        query_embedding = await self.embedding_provider.embed_text(query)

        # Search using cosine similarity
        results = await self._semantic_search(
            query_embedding, db_session, top_k
        )

        return results

    async def _semantic_search(
        self,
        query_embedding: List[float],
        db_session: AsyncSession,
        top_k: int,
    ) -> List[RetrievalResult]:
        """
        Perform semantic search using pgvector cosine similarity

        Args:
            query_embedding: Embedding vector for the query
            db_session: Database session
            top_k: Number of results to return

        Returns:
            List of RetrievalResult objects
        """
        # Build query using pgvector <-> operator for cosine similarity
        stmt = (
            select(
                Chunk.id,
                Chunk.document_id,
                Chunk.content,
                Chunk.chunk_index,
                Document.title,
                Document.filename,
                # Calculate similarity score (1 - distance) for cosine similarity
                (1 - (Chunk.embedding.cosine_distance(query_embedding))).label("similarity"),
            )
            .join(Document, Chunk.document_id == Document.id)
            .order_by((1 - (Chunk.embedding.cosine_distance(query_embedding))).desc())
            .limit(top_k)
        )

        result = await db_session.execute(stmt)
        rows = result.fetchall()

        results = []
        for row in rows:
            results.append(
                RetrievalResult(
                    chunk_id=row.id,
                    document_id=row.document_id,
                    document_title=row.title,
                    document_filename=row.filename,
                    content=row.content,
                    similarity_score=float(row.similarity),
                    chunk_index=row.chunk_index,
                )
            )

        return results
