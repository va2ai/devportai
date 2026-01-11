"""Main FastAPI application entry point"""
import os
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import engine, get_db
from app.models import Base
from app.schemas import (
    IngestResponse,
    RetrievalRequest,
    RetrievalResponse,
    RetrievalResultItem,
    ErrorResponse,
)
from app.chat_schemas import ChatRequest, ChatResponse
from app.ingestion import DocumentIngestionService
from app.retrieval import DocumentRetrievalService
from app.chat_service import ChatService
from app.embeddings import get_embedding_provider
from app.tracing import instrument_app
from app.config import settings

app = FastAPI(
    title="RAG Fact-Check API",
    description="API for RAG-based fact checking with verification",
    version="0.2.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
embedding_provider = get_embedding_provider()
ingestion_service = DocumentIngestionService(embedding_provider)
retrieval_service = DocumentRetrievalService(embedding_provider)
chat_service = ChatService(embedding_provider, retrieval_service)

# Instrument app with OpenTelemetry
instrument_app(app)


@app.on_event("startup")
async def startup():
    """Create database tables on startup"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


@app.get("/health")
async def health_check():
    """Health check endpoint with database connectivity verification"""
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ok", "db": "connected"}
    except Exception as e:
        return {"status": "error", "db": "disconnected", "error": str(e)}


@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "RAG Fact-Check API", "version": "0.1.0"}


@app.post("/api/v1/ingest", response_model=IngestResponse)
async def ingest_document(
    file: UploadFile = File(...),
    db_session: AsyncSession = Depends(get_db),
):
    """
    Ingest a document (supported by Unstructured) and generate embeddings

    Args:
        file: The file to ingest (supported format)
        db_session: Database session

    Returns:
        IngestResponse with document ID and chunk count

    Raises:
        HTTPException: If file format is unsupported or ingestion fails
    """
    try:
        # Validate file type
        content_type = file.content_type or ""
        extension = Path(file.filename or "").suffix.lower()
        allowed_types = set(settings.allowed_file_types)
        allowed_exts = set(settings.allowed_file_extensions)

        if content_type not in allowed_types and extension not in allowed_exts:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Unsupported file type: {content_type or 'unknown'} "
                    f"(extension: {extension or 'none'})."
                ),
            )

        # Read file content
        content = await file.read()
        if not content:
            raise HTTPException(status_code=400, detail="File is empty")

        # Create file-like object
        import io
        file_obj = io.BytesIO(content)

        # Ingest document
        document_id, chunk_count = await ingestion_service.ingest_file(
            file=file_obj,
            filename=file.filename,
            content_type=content_type,
            db_session=db_session,
        )

        return IngestResponse(
            document_id=document_id,
            filename=file.filename,
            chunk_count=chunk_count,
            message="Document ingested successfully",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ingesting document: {str(e)}")


@app.post("/api/v1/retrieve", response_model=RetrievalResponse)
async def retrieve_documents(
    request: RetrievalRequest,
    db_session: AsyncSession = Depends(get_db),
):
    """
    Retrieve relevant documents using semantic search

    Args:
        request: RetrievalRequest with query and optional top_k
        db_session: Database session

    Returns:
        RetrievalResponse with list of matching chunks

    Raises:
        HTTPException: If search fails
    """
    try:
        # Perform retrieval
        results = await retrieval_service.retrieve(
            query=request.query,
            db_session=db_session,
            top_k=request.top_k,
        )

        # Convert to response format
        result_items = [
            RetrievalResultItem(
                chunk_id=result.chunk_id,
                document_id=result.document_id,
                document_title=result.document_title,
                document_filename=result.document_filename,
                content=result.content,
                similarity_score=result.similarity_score,
                chunk_index=result.chunk_index,
            )
            for result in results
        ]

        return RetrievalResponse(
            query=request.query,
            result_count=len(result_items),
            results=result_items,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving documents: {str(e)}")


@app.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db_session: AsyncSession = Depends(get_db),
):
    """
    Chat endpoint with two-step Generate-then-Verify pipeline

    This endpoint:
    1. Retrieves relevant documents using semantic search
    2. Generates a draft answer using LLM with only retrieved context
    3. Verifies the answer using an adversarial LLM pass
    4. Returns verified response with citations and confidence

    Fallback behavior:
    - If no documents are retrieved, returns "I don't know" response
    - If similarity scores are too low, returns refusal
    - If verification fails, returns low confidence

    Args:
        request: ChatRequest with query and parameters
        db_session: Database session

    Returns:
        ChatResponse with verified answer, citations, and confidence

    Raises:
        HTTPException: If chat pipeline fails
    """
    try:
        # Execute chat pipeline
        verified_response, retrieval_status, trace_id = await chat_service.chat(
            query=request.query,
            db_session=db_session,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold,
        )

        return ChatResponse(
            query=request.query,
            response=verified_response,
            trace_id=trace_id,
            retrieval_status=retrieval_status,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in chat: {str(e)}")
