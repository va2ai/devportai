# Chat Endpoint - Generate-then-Verify Pipeline

## Overview

The `/chat` endpoint implements a sophisticated two-step "Generate-then-Verify" pipeline for fact-checked question answering with strict structured outputs and comprehensive tracing.

**Status**: ✅ Production Ready
**Version**: 0.2.0

---

## Architecture

```
User Query
    ↓
[1] RETRIEVAL (with fallback)
    ├→ Semantic search in vector DB
    ├→ Filter by similarity threshold
    └→ If no results → Return "I don't know" (short-circuit)
    ↓
[2] DRAFT GENERATION
    ├→ Format context from chunks
    ├→ Call LLM with strict instructions
    └→ Generate answer using ONLY context
    ↓
[3] ADVERSARIAL VERIFICATION
    ├→ Second LLM pass as "auditor"
    ├→ Check each sentence against chunks
    ├→ Flag unsupported/contradicted claims
    └→ Assign confidence level
    ↓
[4] STRUCTURED RESPONSE
    └→ Return JSON with citations + confidence
```

---

## API Specification

### POST /chat

Generate a fact-checked answer with verification.

**Request Body**:
```json
{
  "query": "What is machine learning?",
  "top_k": 5,
  "similarity_threshold": 0.5
}
```

**Request Schema** (`ChatRequest`):
- `query` (string, required): User question (1-1000 chars)
- `top_k` (int, optional): Number of chunks to retrieve (1-20, default: 5)
- `similarity_threshold` (float, optional): Minimum similarity score (0.0-1.0, default: 0.5)

**Response** (200 OK):
```json
{
  "query": "What is machine learning?",
  "response": {
    "final_text": "Machine learning is a subset of artificial intelligence...",
    "citations": [
      {
        "statement": "Machine learning is a subset of AI",
        "source_chunks": [
          {
            "chunk_id": 42,
            "document_id": 1,
            "document_filename": "ml_guide.pdf",
            "document_title": "ML Guide",
            "content": "Machine learning is...",
            "similarity_score": 0.89,
            "chunk_index": 5
          }
        ],
        "supported": true
      }
    ],
    "confidence_score": 0.89,
    "confidence_level": "high",
    "refusal_reason": null,
    "unsupported_claims": [],
    "corrections": []
  },
  "trace_id": "abc123",
  "retrieval_status": "success"
}
```

---

## Response Fields

### `response` Object

| Field | Type | Description |
|-------|------|-------------|
| `final_text` | string | The verified answer text |
| `citations` | Citation[] | List of citations linking claims to sources |
| `confidence_score` | float (0-1) | Numeric confidence in answer |
| `confidence_level` | enum | "high", "medium", "low", or "refusal" |
| `refusal_reason` | string? | Reason for refusing to answer (if applicable) |
| `unsupported_claims` | string[] | Claims that couldn't be verified |
| `corrections` | string[] | Corrections made during verification |

### `citations` Array

Each citation links a statement to supporting source chunks:

```json
{
  "statement": "Specific claim from answer",
  "source_chunks": [SourceChunk],
  "supported": true
}
```

### `retrieval_status`

- `"success"`: Retrieved sufficient high-quality chunks (3+)
- `"partial"`: Retrieved some chunks but below ideal threshold
- `"failed"`: No chunks found or all below similarity threshold

---

## Confidence Levels

### HIGH (score: 0.8-1.0)
- Answer fully supported by source chunks
- All claims verified
- No contradictions found
- Safe to present to users

### MEDIUM (score: 0.5-0.8)
- Answer mostly supported
- Minor gaps or uncertain claims
- Some statements need cautious interpretation

### LOW (score: 0.2-0.5)
- Answer partially supported
- Contains unsupported or contradicted claims
- High uncertainty
- Should be reviewed before use

### REFUSAL (score: 0.0-0.2)
- Cannot answer with confidence
- No relevant documents found
- Claims contradict sources
- Safe fallback response provided

---

## Fallback Behavior

### Scenario 1: No Documents Retrieved

**Trigger**: Semantic search returns 0 results

**Response**:
```json
{
  "response": {
    "final_text": "I don't know how to answer that question based on the available documents.",
    "confidence_level": "refusal",
    "confidence_score": 0.0,
    "refusal_reason": "No relevant documents found",
    "citations": [],
    "unsupported_claims": [],
    "corrections": []
  },
  "retrieval_status": "failed"
}
```

**Trace**: Shows span tagged with `retrieval_failure`, short-circuiting generation steps.

---

### Scenario 2: Low Similarity Scores

**Trigger**: All retrieved chunks below `similarity_threshold`

**Response**: Same as Scenario 1 with `refusal_reason: "No relevant documents found"`

---

### Scenario 3: Unsupported Claims Detected

**Trigger**: Adversarial verifier finds claims not in source chunks

**Example Query**: "What is the secret password in the document?"

**Response**:
```json
{
  "response": {
    "final_text": "I cannot answer this question based on the provided documents.",
    "confidence_level": "low",
    "confidence_score": 0.2,
    "refusal_reason": "Claim contradicts source material",
    "unsupported_claims": ["There is a secret password"],
    "citations": [],
    "corrections": ["No password information found in documents"]
  },
  "retrieval_status": "success"
}
```

---

## OpenTelemetry Tracing

### Trace Structure

Every `/chat` request creates a distributed trace with these spans:

```
chat_request (parent)
  ├── retrieval
  │     └── events: retrieval_complete, retrieval_error
  ├── draft_generation
  │     └── events: generation_complete, generation_error
  └── verification_check
        └── events: verification_complete, verification_error
```

### Span Attributes

**chat_request**:
- `query`: User query text
- `retrieval_status`: success/partial/failed
- `confidence_level`: high/medium/low/refusal

**retrieval**:
- `query`: User query
- `top_k`: Number of chunks requested
- `result_count`: Number of chunks returned
- `threshold`: Similarity threshold used

**draft_generation**:
- `query`: User query
- `token_usage`: LLM tokens consumed

**verification_check**:
- `unsupported_count`: Number of unsupported claims
- `confidence_level`: Final confidence

### Viewing Traces

**Jaeger UI**: http://localhost:16686

Query traces by:
- Service: `rag-fact-check-api`
- Operation: `chat_request`
- Tags: `retrieval_status`, `confidence_level`

---

## Testing

### Unit Tests

```bash
cd backend
poetry run pytest tests/test_chat.py -v
```

**Coverage**:
- ✅ Context formatting
- ✅ Retrieval fallback (no results)
- ✅ Retrieval fallback (below threshold)
- ✅ Successful retrieval
- ✅ SafeResponse structure
- ✅ High confidence verification
- ✅ Low confidence verification
- ✅ Contradiction detection
- ✅ Schema validation

---

### Integration Tests

```bash
poetry run pytest tests/test_chat_api.py -v
```

**Coverage**:
- ✅ Endpoint existence
- ✅ Request validation
- ✅ Response structure
- ✅ Fallback: No documents
- ✅ Fallback: Low similarity
- ✅ Adversarial: Fake facts
- ✅ Tracing integration

---

## Usage Examples

### Example 1: Successful Query

```bash
curl -X POST "http://localhost:3000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is supervised learning?",
    "top_k": 5,
    "similarity_threshold": 0.5
  }'
```

**Expected Response**:
- `confidence_level`: "high" or "medium"
- `retrieval_status`: "success"
- `final_text`: Detailed answer from documents
- `citations`: List of supporting chunks
- `unsupported_claims`: Empty array

---

### Example 2: No Matching Documents

```bash
curl -X POST "http://localhost:3000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is quantum entanglement?",
    "top_k": 5,
    "similarity_threshold": 0.7
  }'
```

**Expected Response** (if no ML docs contain quantum physics):
```json
{
  "query": "What is quantum entanglement?",
  "response": {
    "final_text": "I don't know how to answer that question based on the available documents.",
    "confidence_level": "refusal",
    "confidence_score": 0.0,
    "refusal_reason": "Retrieval failed: No relevant documents found",
    "citations": [],
    "unsupported_claims": [],
    "corrections": []
  },
  "retrieval_status": "failed",
  "trace_id": null
}
```

---

### Example 3: Adversarial - Fake Fact

```bash
curl -X POST "http://localhost:3000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the admin password mentioned in the document?",
    "top_k": 5,
    "similarity_threshold": 0.5
  }'
```

**Expected Response**:
- `confidence_level`: "low" or "refusal"
- `unsupported_claims`: ["Password information requested"]
- `corrections`: ["No password information in documents"]
- `refusal_reason`: May be set

---

## Configuration

### Environment Variables

```env
# OpenAI (required for chat)
OPENAI_API_KEY=sk-...

# Chat models
CHAT_MODEL=gpt-5.1
CHAT_TEMPERATURE=0.3
VERIFICATION_MODEL=gpt-5.1
VERIFICATION_TEMPERATURE=0.2

# Tracing
ENABLE_TRACING=true
JAEGER_HOST=localhost
JAEGER_PORT=6831
```

### Default Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `chat_model` | gpt-5.1 | Model for draft generation |
| `chat_temperature` | 0.3 | Lower = more deterministic |
| `verification_model` | gpt-5.1 | Model for verification |
| `verification_temperature` | 0.2 | Even lower for fact-checking |
| `enable_tracing` | true | Enable OpenTelemetry |
| `jaeger_host` | localhost | Jaeger collector host |
| `jaeger_port` | 6831 | Jaeger collector port |

---

## Prompts

### Draft Generation Prompt

```
You are a helpful assistant that answers questions based ONLY on the provided context chunks.

Instructions:
1. Answer the question using ONLY information from the context chunks below.
2. Do NOT use any external knowledge or make up information.
3. If the question cannot be answered from the context, explicitly state "I cannot answer this question based on the provided documents."
4. Be specific and reference the chunks when possible.

Context Chunks:
{context}

Question: {query}

Provide a clear, concise answer.
```

### Verification Prompt

```
You are a fact-checking auditor. Your job is to verify that claims in an answer are supported by the provided source chunks.

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
{
  "supported_statements": ["statement 1", "statement 2"],
  "unsupported_statements": ["unsupported claim"],
  "contradicted_statements": ["contradicted claim"],
  "confidence_level": "HIGH|MEDIUM|LOW",
  "corrections": ["correction 1"],
  "explanation": "brief explanation"
}
```

---

## Error Handling

### 400 Bad Request
- Empty query
- Invalid `top_k` (not in 1-20)
- Invalid `similarity_threshold` (not in 0.0-1.0)

### 500 Internal Server Error
- LLM API failure
- Database connection error
- Unexpected exception in pipeline

**Response**:
```json
{
  "detail": "Error in chat: <error message>"
}
```

---

## Performance

### Latency

**Typical flow** (with documents in DB):
1. Retrieval: 50-100ms
2. Draft generation: 1-3 seconds (LLM)
3. Verification: 1-3 seconds (LLM)
**Total**: ~2-7 seconds

**Fallback flow** (no documents):
1. Retrieval: 50-100ms
2. Short-circuit: <10ms
**Total**: ~60-110ms (much faster)

### Token Usage

**Per request** (assuming moderate answer):
- Draft generation: 500-1500 tokens
- Verification: 300-800 tokens
**Total**: 800-2300 tokens (~$0.02-$0.05 per request with GPT-4)

---

## Acceptance Criteria ✅

### ✅ Criterion 1: Valid Question Returns JSON
```bash
curl /chat -d '{"query":"What is ML?"}'
# → Returns JSON with answer + citations
```

### ✅ Criterion 2: Fallback Test
```bash
curl /chat -d '{"query":"xyz123","similarity_threshold":0.9}'
# → Returns refusal_reason: "No relevant documents found"
# → Trace shows retrieval_failure tag and short-circuit
```

### ✅ Criterion 3: Adversarial Test
```bash
curl /chat -d '{"query":"What is the fake fact XYZ?"}'
# → Returns confidence: "low" OR refusal
# → unsupported_claims array populated
```

---

## Code Structure

```
backend/app/
├── chat_schemas.py          # Pydantic schemas
│   ├── SourceChunk
│   ├── DraftAnswer
│   ├── VerifiedResponse
│   ├── ConfidenceLevel
│   ├── SafeResponse
│   ├── ChatRequest
│   └── ChatResponse
│
├── chat_service.py          # Core pipeline logic
│   └── ChatService
│       ├── chat()                    # Main pipeline
│       ├── _retrieve_with_fallback() # Step 1
│       ├── _generate_draft()         # Step 2
│       └── _verify_answer()          # Step 3
│
├── tracing.py               # OpenTelemetry setup
│   ├── create_span()
│   ├── set_span_attribute()
│   └── TracingSpans enum
│
└── main.py                  # FastAPI endpoint
    └── POST /chat

tests/
├── test_chat.py             # Unit tests (15 tests)
└── test_chat_api.py         # Integration tests (10 tests)
```

---

## Next Steps

### Phase 3 Enhancements

- [ ] **Structured JSON mode**: Use OpenAI's structured outputs
- [ ] **Citation extraction**: Parse exact sentences from chunks
- [ ] **Query expansion**: Rewrite queries for better retrieval
- [ ] **Reranking**: Cross-encoder for better chunk selection
- [ ] **Caching**: Redis cache for repeated queries
- [ ] **Streaming**: Server-sent events for real-time responses
- [ ] **Metrics**: Prometheus metrics for performance monitoring
- [ ] **Fine-tuned verifier**: Custom model for domain-specific verification

---

## Troubleshooting

### No OpenAI API Key
**Error**: "OPENAI_API_KEY not set"
**Solution**: Set `OPENAI_API_KEY` in `.env` or use `EMBEDDING_PROVIDER=mock`

### Jaeger Not Running
**Symptom**: Tracing errors in logs
**Solution**:
```bash
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 6831:6831/udp \
  jaegertracing/all-in-one:latest
```

### Low Confidence Answers
**Cause**: Verifier too aggressive
**Solution**: Adjust `VERIFICATION_TEMPERATURE` or review prompts

### Slow Responses
**Cause**: LLM API latency
**Solution**: Use faster models (gpt-3.5-turbo) or implement caching

---

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Pydantic V2](https://docs.pydantic.dev/latest/)
- [OpenAI Chat Completions](https://platform.openai.com/docs/guides/text-generation)
- [Jaeger Tracing](https://www.jaegertracing.io/)

---

**Version**: 0.2.0
**Last Updated**: January 2025
**Status**: Production Ready ✅


