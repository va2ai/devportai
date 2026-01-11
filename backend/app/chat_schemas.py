"""Pydantic schemas for chat endpoint"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class SourceChunk(BaseModel):
    """Reference to a source chunk in the database"""
    chunk_id: int = Field(..., description="ID of the chunk in the database")
    document_id: int = Field(..., description="ID of the source document")
    document_filename: str = Field(..., description="Original filename")
    document_title: str = Field(..., description="Document title")
    content: str = Field(..., description="Text content of the chunk")
    similarity_score: float = Field(..., ge=0.0, le=1.0, description="Similarity score (0-1)")
    chunk_index: int = Field(..., description="Position of chunk in document")


class Citation(BaseModel):
    """Citation linking an answer statement to source chunks"""
    statement: str = Field(..., description="The statement being cited")
    source_chunks: List[SourceChunk] = Field(..., description="Chunks supporting this statement")
    supported: bool = Field(..., description="Whether statement is supported by chunks")


class DraftAnswer(BaseModel):
    """LLM-generated draft answer before verification"""
    answer_text: str = Field(..., description="The generated answer text")
    reasoning: str = Field(..., description="Brief explanation of how answer was derived")
    source_chunks: List[SourceChunk] = Field(
        default_factory=list,
        description="Chunks used to generate the answer"
    )


class ConfidenceLevel(str, Enum):
    """Confidence level of the verified response"""
    HIGH = "high"       # Answer fully supported by sources
    MEDIUM = "medium"   # Answer mostly supported, minor gaps
    LOW = "low"         # Answer partially supported or uncertain
    REFUSAL = "refusal" # Unable to answer with confidence


class VerifiedResponse(BaseModel):
    """Final verified response after both generation and verification"""
    final_text: str = Field(..., description="The final verified answer text")
    citations: List[Citation] = Field(
        default_factory=list,
        description="Citations linking claims to sources"
    )
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the answer (0-1)"
    )
    confidence_level: ConfidenceLevel = Field(
        ...,
        description="Categorical confidence assessment"
    )
    refusal_reason: Optional[str] = Field(
        None,
        description="Reason for refusing to answer, if applicable"
    )
    unsupported_claims: List[str] = Field(
        default_factory=list,
        description="Claims that couldn't be verified against sources"
    )
    corrections: List[str] = Field(
        default_factory=list,
        description="Corrections made during verification"
    )


class ChatRequest(BaseModel):
    """Request schema for chat endpoint"""
    query: str = Field(..., min_length=1, max_length=1000, description="User query")
    top_k: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of source chunks to retrieve"
    )
    similarity_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum similarity score for retrieval"
    )


class ChatResponse(BaseModel):
    """Response schema for chat endpoint"""
    query: str = Field(..., description="The original user query")
    response: VerifiedResponse = Field(..., description="The verified response")
    trace_id: Optional[str] = Field(None, description="OpenTelemetry trace ID for debugging")
    retrieval_status: str = Field(
        ...,
        description="Status of retrieval: 'success', 'partial', or 'failed'"
    )


class SafeResponse(BaseModel):
    """Safe/fallback response when retrieval fails"""
    final_text: str = Field(
        default="I don't know how to answer that question based on the available documents.",
        description="Safe fallback message"
    )
    citations: List[Citation] = Field(
        default_factory=list,
        description="Empty citations list"
    )
    confidence_score: float = Field(
        default=0.0,
        description="Low confidence for unknown queries"
    )
    confidence_level: ConfidenceLevel = Field(
        default=ConfidenceLevel.REFUSAL,
        description="Refusal confidence level"
    )
    refusal_reason: str = Field(
        ...,
        description="Reason for refusal to answer"
    )
    unsupported_claims: List[str] = Field(
        default_factory=list,
        description="Empty list"
    )
    corrections: List[str] = Field(
        default_factory=list,
        description="Empty list"
    )

    def to_verified_response(self) -> VerifiedResponse:
        """Convert to VerifiedResponse"""
        return VerifiedResponse(**self.model_dump())
