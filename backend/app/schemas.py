"""Pydantic schemas for API request/response"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


class IngestRequest(BaseModel):
    """Request schema for document ingestion"""
    # File is handled via multipart/form-data in the endpoint
    pass


class FileSummary(BaseModel):
    """Summary of ingested file content"""
    content_type: str = Field(..., description="MIME type of the file")
    file_size_bytes: int = Field(..., description="Raw file size in bytes")
    char_count: int = Field(..., description="Number of characters extracted")
    word_count: int = Field(..., description="Number of words extracted")
    line_count: int = Field(..., description="Number of lines extracted")
    page_count: Optional[int] = Field(None, description="Estimated page count when available")
    llm_summary: Optional[str] = Field(None, description="LLM-generated summary")


class IngestResponse(BaseModel):
    """Response schema for document ingestion"""
    document_id: int = Field(..., description="ID of the ingested document")
    filename: str = Field(..., description="Original filename")
    chunk_count: int = Field(..., description="Number of chunks created")
    summary: FileSummary = Field(..., description="Summary of extracted content")
    message: str = Field(default="Document ingested successfully")


class RetrievalRequest(BaseModel):
    """Request schema for document retrieval"""
    query: str = Field(..., description="Search query", min_length=1, max_length=1000)
    document_filename: Optional[str] = Field(
        None,
        description="Optional filename to scope retrieval"
    )
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results to return")


class RetrievalResultItem(BaseModel):
    """Single retrieval result"""
    chunk_id: int = Field(..., description="ID of the chunk")
    document_id: int = Field(..., description="ID of the source document")
    document_title: str = Field(..., description="Title of the document")
    document_filename: str = Field(..., description="Filename of the document")
    content: str = Field(..., description="Text content of the chunk")
    similarity_score: float = Field(..., description="Cosine similarity score (0-1)")
    chunk_index: int = Field(..., description="Index of this chunk in the document")


class RetrievalResponse(BaseModel):
    """Response schema for document retrieval"""
    query: str = Field(..., description="The search query that was executed")
    result_count: int = Field(..., description="Number of results returned")
    results: List[RetrievalResultItem] = Field(
        default_factory=list, description="List of retrieval results"
    )


class DocumentListItem(BaseModel):
    """Single document list item"""
    document_id: int = Field(..., description="Document ID")
    title: str = Field(..., description="Document title")
    filename: str = Field(..., description="Filename")
    content_type: Optional[str] = Field(None, description="MIME type")
    chunk_count: int = Field(..., description="Number of chunks")
    created_at: Optional[datetime] = Field(None, description="Upload timestamp")


class DocumentListResponse(BaseModel):
    """Response schema for document list"""
    count: int = Field(..., description="Number of documents")
    documents: List[DocumentListItem] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """Error response schema"""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
