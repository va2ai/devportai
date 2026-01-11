"""Tests for chat endpoint with verification"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from app.chat_service import ChatService
from app.chat_schemas import (
    SourceChunk,
    DraftAnswer,
    VerifiedResponse,
    ConfidenceLevel,
    SafeResponse,
)
from app.embeddings import MockEmbeddingProvider
from app.retrieval import DocumentRetrievalService


class TestChatService:
    """Test cases for ChatService"""

    @pytest.fixture
    def mock_embedding_provider(self):
        """Mock embedding provider"""
        return MockEmbeddingProvider()

    @pytest.fixture
    def mock_retrieval_service(self):
        """Mock retrieval service"""
        return Mock(spec=DocumentRetrievalService)

    @pytest.fixture
    def chat_service(self, mock_embedding_provider, mock_retrieval_service):
        """Create chat service with mocks"""
        return ChatService(mock_embedding_provider, mock_retrieval_service)

    @pytest.mark.asyncio
    async def test_format_context(self, chat_service):
        """Test context formatting for LLM"""
        chunks = [
            SourceChunk(
                chunk_id=1,
                document_id=1,
                document_filename="test.pdf",
                document_title="Test",
                content="This is chunk 1",
                similarity_score=0.9,
                chunk_index=0,
            ),
            SourceChunk(
                chunk_id=2,
                document_id=1,
                document_filename="test.pdf",
                document_title="Test",
                content="This is chunk 2",
                similarity_score=0.8,
                chunk_index=1,
            ),
        ]

        formatted = chat_service._format_context(chunks)

        assert "Chunk 1" in formatted
        assert "Chunk 2" in formatted
        assert "test.pdf" in formatted
        assert "This is chunk 1" in formatted

    @pytest.mark.asyncio
    async def test_retrieval_fallback_no_results(self, chat_service, mock_retrieval_service):
        """Test fallback when retrieval returns no results"""
        # Mock empty retrieval
        mock_retrieval_service.retrieve = AsyncMock(return_value=[])

        db_session = Mock()
        parent_span = Mock()

        chunks, status = await chat_service._retrieve_with_fallback(
            query="test query",
            db_session=db_session,
            top_k=5,
            similarity_threshold=0.5,
            parent_span=parent_span,
        )

        assert chunks == []
        assert "No relevant documents found" in status

    @pytest.mark.asyncio
    async def test_retrieval_fallback_below_threshold(self, chat_service, mock_retrieval_service):
        """Test fallback when results are below similarity threshold"""
        # Mock retrieval with low similarity results
        mock_result = Mock()
        mock_result.chunk_id = 1
        mock_result.document_id = 1
        mock_result.document_filename = "test.pdf"
        mock_result.document_title = "Test"
        mock_result.content = "low similarity content"
        mock_result.similarity_score = 0.3  # Below threshold
        mock_result.chunk_index = 0

        mock_retrieval_service.retrieve = AsyncMock(return_value=[mock_result])

        db_session = Mock()
        parent_span = Mock()

        chunks, status = await chat_service._retrieve_with_fallback(
            query="test query",
            db_session=db_session,
            top_k=5,
            similarity_threshold=0.5,
            parent_span=parent_span,
        )

        assert chunks == []
        assert "No relevant documents found" in status

    @pytest.mark.asyncio
    async def test_retrieval_success(self, chat_service, mock_retrieval_service):
        """Test successful retrieval"""
        # Mock retrieval with good results
        mock_result = Mock()
        mock_result.chunk_id = 1
        mock_result.document_id = 1
        mock_result.document_filename = "test.pdf"
        mock_result.document_title = "Test"
        mock_result.content = "relevant content"
        mock_result.similarity_score = 0.85
        mock_result.chunk_index = 0

        mock_retrieval_service.retrieve = AsyncMock(return_value=[mock_result])

        db_session = Mock()
        parent_span = Mock()

        chunks, status = await chat_service._retrieve_with_fallback(
            query="test query",
            db_session=db_session,
            top_k=5,
            similarity_threshold=0.5,
            parent_span=parent_span,
        )

        assert len(chunks) == 1
        assert chunks[0].similarity_score == 0.85
        assert status in ["success", "partial"]

    def test_safe_response_structure(self):
        """Test SafeResponse structure"""
        safe = SafeResponse(refusal_reason="No documents available")

        assert safe.confidence_level == ConfidenceLevel.REFUSAL
        assert safe.confidence_score == 0.0
        assert safe.refusal_reason == "No documents available"
        assert len(safe.citations) == 0

        verified = safe.to_verified_response()
        assert isinstance(verified, VerifiedResponse)
        assert verified.confidence_level == ConfidenceLevel.REFUSAL

    def test_build_verified_response_high_confidence(self, chat_service):
        """Test building verified response with high confidence"""
        draft = DraftAnswer(
            answer_text="Test answer",
            reasoning="Based on context",
            source_chunks=[],
        )

        verification_result = {
            "supported_statements": ["Test answer"],
            "unsupported_statements": [],
            "contradicted_statements": [],
            "confidence_level": "HIGH",
            "corrections": [],
            "explanation": "All supported",
        }

        verified = chat_service._build_verified_response(
            draft, [], verification_result
        )

        assert verified.confidence_level == ConfidenceLevel.HIGH
        assert verified.confidence_score >= 0.8
        assert len(verified.unsupported_claims) == 0

    def test_build_verified_response_low_confidence(self, chat_service):
        """Test building verified response with low confidence"""
        draft = DraftAnswer(
            answer_text="Test answer with unsupported claims",
            reasoning="Partially based on context",
            source_chunks=[],
        )

        verification_result = {
            "supported_statements": [],
            "unsupported_statements": ["unsupported claim"],
            "contradicted_statements": [],
            "confidence_level": "LOW",
            "corrections": ["correction 1"],
            "explanation": "Partially supported",
        }

        verified = chat_service._build_verified_response(
            draft, [], verification_result
        )

        assert verified.confidence_level == ConfidenceLevel.LOW
        assert verified.confidence_score <= 0.4
        assert len(verified.unsupported_claims) == 1

    def test_build_verified_response_contradicted(self, chat_service):
        """Test building verified response with contradictions"""
        draft = DraftAnswer(
            answer_text="Wrong answer",
            reasoning="Misinterpreted context",
            source_chunks=[],
        )

        verification_result = {
            "supported_statements": [],
            "unsupported_statements": [],
            "contradicted_statements": ["Wrong claim"],
            "confidence_level": "MEDIUM",
            "corrections": ["Correct claim"],
            "explanation": "Contains contradictions",
        }

        verified = chat_service._build_verified_response(
            draft, [], verification_result
        )

        # Contradictions should force LOW confidence
        assert verified.confidence_level == ConfidenceLevel.LOW
        assert verified.confidence_score <= 0.3
        assert len(verified.corrections) >= 1


class TestChatSchemas:
    """Test Pydantic schemas"""

    def test_source_chunk_validation(self):
        """Test SourceChunk validation"""
        chunk = SourceChunk(
            chunk_id=1,
            document_id=1,
            document_filename="test.pdf",
            document_title="Test",
            content="Test content",
            similarity_score=0.85,
            chunk_index=0,
        )

        assert chunk.similarity_score >= 0.0
        assert chunk.similarity_score <= 1.0

        # Test invalid similarity score
        with pytest.raises(ValueError):
            SourceChunk(
                chunk_id=1,
                document_id=1,
                document_filename="test.pdf",
                document_title="Test",
                content="Test",
                similarity_score=1.5,  # Invalid
                chunk_index=0,
            )

    def test_confidence_level_enum(self):
        """Test ConfidenceLevel enum"""
        assert ConfidenceLevel.HIGH.value == "high"
        assert ConfidenceLevel.MEDIUM.value == "medium"
        assert ConfidenceLevel.LOW.value == "low"
        assert ConfidenceLevel.REFUSAL.value == "refusal"

    def test_verified_response_validation(self):
        """Test VerifiedResponse validation"""
        response = VerifiedResponse(
            final_text="Test answer",
            citations=[],
            confidence_score=0.85,
            confidence_level=ConfidenceLevel.HIGH,
            refusal_reason=None,
            unsupported_claims=[],
            corrections=[],
        )

        assert response.confidence_score >= 0.0
        assert response.confidence_score <= 1.0
        assert response.confidence_level == ConfidenceLevel.HIGH

    def test_chat_request_validation(self):
        """Test ChatRequest validation"""
        from app.chat_schemas import ChatRequest

        # Valid request
        request = ChatRequest(
            query="What is machine learning?",
            top_k=5,
            similarity_threshold=0.5,
        )

        assert request.query == "What is machine learning?"
        assert 1 <= request.top_k <= 20
        assert 0.0 <= request.similarity_threshold <= 1.0

        # Test validation errors
        with pytest.raises(ValueError):
            ChatRequest(query="", top_k=5)  # Empty query

        with pytest.raises(ValueError):
            ChatRequest(query="test", top_k=0)  # Invalid top_k

        with pytest.raises(ValueError):
            ChatRequest(query="test", top_k=5, similarity_threshold=1.5)  # Invalid threshold
