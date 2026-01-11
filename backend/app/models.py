"""Database models for RAG application"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import JSONB
from pgvector.sqlalchemy import Vector
from datetime import datetime
from app.database import Base


class Document(Base):
    """Stores metadata about uploaded documents"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    content_type = Column(String(50))
    file_size = Column(Integer)
    chunk_count = Column(Integer, default=0)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Chunk(Base):
    """Stores text chunks with their embeddings"""
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(1536))
    chunk_index = Column(Integer)
    metadata = Column(JSONB, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
