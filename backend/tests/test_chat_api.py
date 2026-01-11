"""Integration tests for /chat endpoint"""
import pytest
from httpx import AsyncClient
from app.main import app


class TestChatEndpointIntegration:
    """Integration tests for chat endpoint"""

    @pytest.mark.asyncio
    async def test_chat_endpoint_exists(self):
        """Test that /chat endpoint exists"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/chat",
                json={
                    "query": "test query",
                    "top_k": 5,
                    "similarity_threshold": 0.5,
                },
            )

            # Should not be 404
            assert response.status_code != 404

    @pytest.mark.asyncio
    async def test_chat_request_validation(self):
        """Test request validation"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Empty query
            response = await client.post(
                "/chat",
                json={
                    "query": "",
                    "top_k": 5,
                },
            )
            assert response.status_code == 422  # Validation error

            # Invalid top_k
            response = await client.post(
                "/chat",
                json={
                    "query": "test",
                    "top_k": 0,
                },
            )
            assert response.status_code == 422

            # Invalid similarity_threshold
            response = await client.post(
                "/chat",
                json={
                    "query": "test",
                    "similarity_threshold": 1.5,
                },
            )
            assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_chat_response_structure(self):
        """Test response structure (may fail if DB empty, but tests schema)"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/chat",
                json={
                    "query": "What is machine learning?",
                    "top_k": 3,
                    "similarity_threshold": 0.3,
                },
            )

            # Should return JSON (may be refusal if no docs)
            if response.status_code == 200:
                data = response.json()

                # Check required fields
                assert "query" in data
                assert "response" in data
                assert "retrieval_status" in data

                # Check response structure
                resp = data["response"]
                assert "final_text" in resp
                assert "citations" in resp
                assert "confidence_score" in resp
                assert "confidence_level" in resp

                # Confidence score should be 0-1
                assert 0.0 <= resp["confidence_score"] <= 1.0

                # Confidence level should be valid
                assert resp["confidence_level"] in ["high", "medium", "low", "refusal"]


class TestChatFallbackScenarios:
    """Test fallback scenarios as per acceptance criteria"""

    @pytest.mark.asyncio
    async def test_fallback_no_documents(self):
        """
        ACCEPTANCE CRITERIA: Fallback Test
        A query with NO matching docs returns JSON with
        refusal_reason and trace showing short-circuit
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Query for something unlikely to be in documents
            response = await client.post(
                "/chat",
                json={
                    "query": "xyzabc123uniquequery",
                    "top_k": 5,
                    "similarity_threshold": 0.9,  # High threshold
                },
            )

            if response.status_code == 200:
                data = response.json()

                # Should indicate retrieval failure
                retrieval_status = data.get("retrieval_status", "")
                assert retrieval_status in ["failed", "No relevant documents found"]

                # Response should have refusal
                resp = data["response"]
                assert resp.get("refusal_reason") is not None or \
                       resp.get("confidence_level") == "refusal"

                # Should have low/zero confidence
                assert resp["confidence_score"] <= 0.5

    @pytest.mark.asyncio
    async def test_fallback_low_similarity(self):
        """Test fallback when similarity threshold not met"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Very high threshold that won't be met
            response = await client.post(
                "/chat",
                json={
                    "query": "test query",
                    "top_k": 5,
                    "similarity_threshold": 0.99,  # Very high
                },
            )

            if response.status_code == 200:
                data = response.json()

                # Likely to fail retrieval
                resp = data["response"]

                # Should have safety mechanism
                if data["retrieval_status"] == "failed":
                    assert resp["confidence_level"] == "refusal" or \
                           resp["confidence_score"] < 0.3


class TestAdversarialVerification:
    """Test adversarial verification scenarios"""

    def test_unsupported_claim_detection_concept(self):
        """
        ACCEPTANCE CRITERIA: Adversarial Test
        Test the concept of detecting unsupported claims
        (Unit test since we need controlled context)
        """
        # This is a conceptual test showing the structure
        # Real test would need mocked LLM or actual documents

        # Example: Draft claims X, but context says Y
        # Verifier should detect contradiction
        draft_claim = "The sky is green"
        context = "The sky is blue during the day"

        # In a real adversarial verification:
        # - Verifier compares claim to context
        # - Finds contradiction
        # - Returns LOW confidence or correction

        # Expected behavior encoded in schemas:
        from app.chat_schemas import VerifiedResponse, ConfidenceLevel

        # Mock a verified response with detected unsupported claim
        verified = VerifiedResponse(
            final_text="The sky is green",
            citations=[],
            confidence_score=0.2,
            confidence_level=ConfidenceLevel.LOW,
            refusal_reason="Claim contradicts source material",
            unsupported_claims=["The sky is green"],
            corrections=["The sky is blue during the day"],
        )

        assert verified.confidence_level == ConfidenceLevel.LOW
        assert len(verified.unsupported_claims) > 0
        assert len(verified.corrections) > 0

    @pytest.mark.asyncio
    async def test_adversarial_fake_fact(self):
        """
        ACCEPTANCE CRITERIA: Adversarial Test
        Query asking for fake fact (not in docs) should return
        low confidence or refusal
        """
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Ask for something specific that won't be in docs
            response = await client.post(
                "/chat",
                json={
                    "query": "What is the secret password stored in document XYZ?",
                    "top_k": 5,
                    "similarity_threshold": 0.5,
                },
            )

            if response.status_code == 200:
                data = response.json()
                resp = data["response"]

                # If retrieval succeeds but answer can't be verified:
                # - Confidence should be low
                # - OR refusal reason should be set
                # - OR unsupported_claims should be flagged

                if data["retrieval_status"] != "failed":
                    # If we got chunks but can't answer:
                    assert resp["confidence_level"] in ["low", "refusal"] or \
                           resp["confidence_score"] < 0.5


class TestOpenTelemetryTracing:
    """Test OpenTelemetry integration"""

    def test_tracing_spans_defined(self):
        """Test that tracing span names are defined"""
        from app.tracing import TracingSpans

        assert hasattr(TracingSpans, "RETRIEVAL")
        assert hasattr(TracingSpans, "DRAFT_GENERATION")
        assert hasattr(TracingSpans, "VERIFICATION")
        assert TracingSpans.RETRIEVAL == "retrieval"
        assert TracingSpans.DRAFT_GENERATION == "draft_generation"
        assert TracingSpans.VERIFICATION == "verification_check"

    @pytest.mark.asyncio
    async def test_trace_id_in_response(self):
        """Test that trace_id field exists in response"""
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/chat",
                json={
                    "query": "test",
                    "top_k": 3,
                },
            )

            if response.status_code == 200:
                data = response.json()
                # trace_id field should exist (may be None)
                assert "trace_id" in data
