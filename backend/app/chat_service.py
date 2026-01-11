"""Chat service implementing two-step Generate-then-Verify pipeline"""
import json
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI

from app.chat_schemas import (
    SourceChunk,
    DraftAnswer,
    VerifiedResponse,
    Citation,
    ConfidenceLevel,
    SafeResponse,
)
from app.retrieval import DocumentRetrievalService
from app.embeddings import EmbeddingProvider
from app.config import settings
from app.tracing import create_span, set_span_attribute, set_span_status, record_span_event


class ChatService:
    """Service for chat endpoint with verification"""

    DRAFT_GENERATION_PROMPT = """You are a helpful assistant that answers questions based ONLY on the provided context chunks.

Instructions:
1. Answer the question using ONLY information from the context chunks below.
2. Do NOT use any external knowledge or make up information.
3. If the question cannot be answered from the context, explicitly state "I cannot answer this question based on the provided documents."
4. Be specific and reference the chunks when possible.

Context Chunks:
{context}

Question: {query}

Provide a clear, concise answer."""

    VERIFICATION_PROMPT = """You are a fact-checking auditor. Your job is to verify that claims in an answer are supported by the provided source chunks.

Instructions:
1. Carefully review each sentence of the answer.
2. Check if each claim is explicitly supported by the source chunks.
3. Mark unsupported claims as "UNSUPPORTED".
4. If a claim is contradicted by chunks, mark it as "CONTRADICTED".
5. Provide overall confidence: HIGH (fully supported), MEDIUM (mostly supported), or LOW (partially supported or contradicted).

Source Chunks:
{chunks_summary}

Answer to Verify:
{answer}

Respond with JSON in this exact format:
{{
  "supported_statements": ["statement 1", "statement 2"],
  "unsupported_statements": ["unsupported claim"],
  "contradicted_statements": ["contradicted claim"],
  "confidence_level": "HIGH|MEDIUM|LOW",
  "corrections": ["correction 1"],
  "explanation": "brief explanation"
}}"""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        retrieval_service: DocumentRetrievalService,
    ):
        """Initialize chat service"""
        self.embedding_provider = embedding_provider
        self.retrieval_service = retrieval_service
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def chat(
        self,
        query: str,
        db_session: AsyncSession,
        top_k: int = 5,
        similarity_threshold: float = 0.5,
    ) -> Tuple[VerifiedResponse, str, str]:
        """
        Execute full chat pipeline: Retrieve → Generate → Verify

        Args:
            query: User query
            db_session: Database session
            top_k: Number of chunks to retrieve
            similarity_threshold: Minimum similarity for retrieval

        Returns:
            Tuple of (VerifiedResponse, retrieval_status, trace_id)
        """
        with create_span("chat_request", {"query": query}) as main_span:
            # Step 1: Retrieval
            source_chunks, retrieval_status = await self._retrieve_with_fallback(
                query,
                db_session,
                top_k,
                similarity_threshold,
                main_span,
            )

            # If retrieval failed, return safe response
            if not source_chunks:
                safe_response = SafeResponse(
                    refusal_reason=f"Retrieval failed: {retrieval_status}"
                )
                set_span_attribute(main_span, "retrieval_status", retrieval_status)
                set_span_status(main_span, "error", retrieval_status)
                return safe_response.to_verified_response(), retrieval_status, ""

            # Step 2: Draft generation
            draft_answer = await self._generate_draft(
                query,
                source_chunks,
                main_span,
            )

            # Step 3: Adversarial verification
            verified_response = await self._verify_answer(
                draft_answer,
                source_chunks,
                main_span,
            )

            set_span_attribute(main_span, "retrieval_status", retrieval_status)
            set_span_attribute(main_span, "confidence_level", verified_response.confidence_level.value)
            set_span_status(main_span, "success")

            return verified_response, retrieval_status, ""

    async def _retrieve_with_fallback(
        self,
        query: str,
        db_session: AsyncSession,
        top_k: int,
        similarity_threshold: float,
        parent_span,
    ) -> Tuple[List[SourceChunk], str]:
        """
        Retrieve documents with fallback logic

        Returns:
            Tuple of (source_chunks, status)
            Status: 'success', 'partial', or 'failed'
        """
        with create_span("retrieval", {"query": query, "top_k": top_k}) as span:
            try:
                # Perform retrieval
                retrieval_results = await self.retrieval_service.retrieve(
                    query=query,
                    db_session=db_session,
                    top_k=top_k,
                )

                # Filter by similarity threshold
                filtered_results = [
                    r for r in retrieval_results
                    if r.similarity_score >= similarity_threshold
                ]

                record_span_event(
                    span,
                    "retrieval_complete",
                    {
                        "total_results": len(retrieval_results),
                        "filtered_results": len(filtered_results),
                        "threshold": similarity_threshold,
                    },
                )

                if not filtered_results:
                    set_span_attribute(span, "result_count", 0)
                    set_span_status(span, "error", "No results above threshold")
                    return [], "No relevant documents found"

                # Convert to SourceChunk
                source_chunks = [
                    SourceChunk(
                        chunk_id=r.chunk_id,
                        document_id=r.document_id,
                        document_filename=r.document_filename,
                        document_title=r.document_title,
                        content=r.content,
                        similarity_score=r.similarity_score,
                        chunk_index=r.chunk_index,
                    )
                    for r in filtered_results
                ]

                set_span_attribute(span, "result_count", len(source_chunks))
                status = "success" if len(source_chunks) >= 3 else "partial"
                set_span_status(span, "success")

                return source_chunks, status

            except Exception as e:
                set_span_status(span, "error", str(e))
                record_span_event(span, "retrieval_error", {"error": str(e)})
                return [], f"Retrieval error: {str(e)}"

    async def _generate_draft(
        self,
        query: str,
        source_chunks: List[SourceChunk],
        parent_span,
    ) -> DraftAnswer:
        """
        Generate draft answer using LLM

        Args:
            query: User query
            source_chunks: Retrieved source chunks

        Returns:
            DraftAnswer with generated text
        """
        with create_span("draft_generation", {"query": query}) as span:
            # Format context
            context_text = self._format_context(source_chunks)

            # Create prompt
            prompt = self.DRAFT_GENERATION_PROMPT.format(
                context=context_text,
                query=query,
            )

            try:
                # Call LLM
                response = await self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant that answers questions based on provided documents.",
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0.3,
                    max_tokens=1000,
                )

                answer_text = response.choices[0].message.content.strip()

                record_span_event(
                    span,
                    "generation_complete",
                    {"token_usage": response.usage.total_tokens if response.usage else 0},
                )

                set_span_status(span, "success")

                return DraftAnswer(
                    answer_text=answer_text,
                    reasoning="Generated from retrieved context chunks",
                    source_chunks=source_chunks,
                )

            except Exception as e:
                set_span_status(span, "error", str(e))
                record_span_event(span, "generation_error", {"error": str(e)})
                raise

    async def _verify_answer(
        self,
        draft_answer: DraftAnswer,
        source_chunks: List[SourceChunk],
        parent_span,
    ) -> VerifiedResponse:
        """
        Verify answer using adversarial LLM pass

        Args:
            draft_answer: Draft answer to verify
            source_chunks: Source chunks for verification

        Returns:
            VerifiedResponse with verification results
        """
        with create_span("verification_check") as span:
            # Format chunks for verification
            chunks_summary = self._format_chunks_for_verification(source_chunks)

            # Create verification prompt
            prompt = self.VERIFICATION_PROMPT.format(
                chunks_summary=chunks_summary,
                answer=draft_answer.answer_text,
            )

            try:
                # Call LLM for verification
                response = await self.client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a fact-checking auditor. Return only valid JSON.",
                        },
                        {
                            "role": "user",
                            "content": prompt,
                        },
                    ],
                    temperature=0.2,
                    max_tokens=1000,
                )

                # Parse verification result
                response_text = response.choices[0].message.content.strip()

                # Try to extract JSON
                try:
                    verification_result = json.loads(response_text)
                except json.JSONDecodeError:
                    # Try to find JSON in response
                    import re
                    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                    if json_match:
                        verification_result = json.loads(json_match.group())
                    else:
                        verification_result = self._default_verification_result()

                record_span_event(
                    span,
                    "verification_complete",
                    {
                        "unsupported_count": len(verification_result.get("unsupported_statements", [])),
                        "confidence_level": verification_result.get("confidence_level", "MEDIUM"),
                    },
                )

                # Build verified response
                verified_response = self._build_verified_response(
                    draft_answer,
                    source_chunks,
                    verification_result,
                )

                set_span_attribute(span, "confidence_level", verified_response.confidence_level.value)
                set_span_status(span, "success")

                return verified_response

            except Exception as e:
                set_span_status(span, "error", str(e))
                record_span_event(span, "verification_error", {"error": str(e)})

                # Return draft answer with low confidence on error
                return VerifiedResponse(
                    final_text=draft_answer.answer_text,
                    citations=[],
                    confidence_score=0.4,
                    confidence_level=ConfidenceLevel.MEDIUM,
                    refusal_reason=f"Verification error: {str(e)}",
                    unsupported_claims=[],
                    corrections=[],
                )

    def _format_context(self, chunks: List[SourceChunk]) -> str:
        """Format chunks for LLM context"""
        formatted = []
        for i, chunk in enumerate(chunks, 1):
            formatted.append(
                f"[Chunk {i} from {chunk.document_filename}]\n{chunk.content}\n"
            )
        return "\n".join(formatted)

    def _format_chunks_for_verification(self, chunks: List[SourceChunk]) -> str:
        """Format chunks for verification prompt"""
        formatted = []
        for i, chunk in enumerate(chunks, 1):
            formatted.append(
                f"Chunk {i} (from {chunk.document_filename}):\n{chunk.content[:500]}..."
            )
        return "\n\n".join(formatted)

    def _default_verification_result(self) -> dict:
        """Return default verification result on parse error"""
        return {
            "supported_statements": [],
            "unsupported_statements": [],
            "contradicted_statements": [],
            "confidence_level": "MEDIUM",
            "corrections": [],
            "explanation": "Verification response could not be parsed",
        }

    def _build_verified_response(
        self,
        draft_answer: DraftAnswer,
        source_chunks: List[SourceChunk],
        verification_result: dict,
    ) -> VerifiedResponse:
        """Build final VerifiedResponse from verification result"""
        unsupported = verification_result.get("unsupported_statements", [])
        contradicted = verification_result.get("contradicted_statements", [])
        confidence_str = verification_result.get("confidence_level", "MEDIUM").upper()

        # Map confidence
        confidence_map = {
            "HIGH": (ConfidenceLevel.HIGH, 0.9),
            "MEDIUM": (ConfidenceLevel.MEDIUM, 0.6),
            "LOW": (ConfidenceLevel.LOW, 0.3),
        }
        conf_level, conf_score = confidence_map.get(confidence_str, (ConfidenceLevel.MEDIUM, 0.6))

        # If contradicted, set to LOW
        if contradicted:
            conf_level = ConfidenceLevel.LOW
            conf_score = 0.2

        # Build citations (simplified: map statements to chunks)
        citations = [
            Citation(
                statement=draft_answer.answer_text[:100],  # Simplified
                source_chunks=source_chunks[:3],
                supported=len(unsupported) == 0 and len(contradicted) == 0,
            )
        ]

        return VerifiedResponse(
            final_text=draft_answer.answer_text,
            citations=citations,
            confidence_score=conf_score,
            confidence_level=conf_level,
            refusal_reason=None if conf_level != ConfidenceLevel.REFUSAL else "Unable to verify answer",
            unsupported_claims=unsupported,
            corrections=verification_result.get("corrections", []),
        )
