"""Document retrieval service for semantic search"""
from typing import List
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
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
        document_filename: str | None = None,
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
            query_embedding, db_session, top_k, document_filename
        )

        return results

    async def _semantic_search(
        self,
        query_embedding: List[float],
        db_session: AsyncSession,
        top_k: int,
        document_filename: str | None,
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
        import json

        # Convert embedding to JSON string for pgvector
        query_vector_str = json.dumps(query_embedding)

        # Use raw SQL for pgvector operations
        # The <=> operator returns cosine distance, so we use 1 - distance for similarity
        where_clause = ""
        params = {"top_k": top_k}
        if document_filename:
            where_clause = "WHERE d.filename = :document_filename"
            params["document_filename"] = document_filename

        sql_query = text(f"""
            SELECT
                c.id,
                c.document_id,
                c.content,
                c.chunk_index,
                d.title,
                d.filename,
                1 - (c.embedding <=> '{query_vector_str}'::vector) as similarity
            FROM chunks c
            JOIN documents d ON c.document_id = d.id
            {where_clause}
            ORDER BY c.embedding <=> '{query_vector_str}'::vector
            LIMIT :top_k
        """)

        result = await db_session.execute(sql_query, params)
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
