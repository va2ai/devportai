# RAG Core Implementation Summary

## Overview

A production-ready Retrieval-Augmented Generation (RAG) system has been implemented with:
- Document ingestion (PDF/TXT)
- Text chunking with intelligent splitting
- Vector embedding generation
- Semantic search with cosine similarity
- PostgreSQL pgvector backend

**Status**: ✅ Core RAG pipeline complete and ready for testing

---

## Architecture

### Data Flow

```
User Upload (PDF/TXT)
    ↓
Text Extraction (pypdf)
    ↓
Text Cleaning & Normalization
    ↓
Chunking (RecursiveCharacterTextSplitter)
    ↓
Embedding Generation (OpenAI/Mock)
    ↓
Vector Storage (PostgreSQL pgvector)
    ↓
Semantic Search (Cosine Distance)
    ↓
Return Top-K Results
```

### Components

#### 1. **Embedding Provider** (`app/embeddings.py`)
- **Abstract Interface**: `EmbeddingProvider` base class
- **Implementations**:
  - `OpenAIEmbeddingProvider`: Uses OpenAI's text-embedding-3-small (1536 dimensions)
  - `MockEmbeddingProvider`: Deterministic embeddings for testing
- **Features**:
  - Batch processing with configurable batch size
  - Rate limiting with delays between batches
  - Factory function for easy provider selection

#### 2. **Text Chunking** (`app/chunking.py`)
- **RecursiveCharacterTextSplitter**:
  - Hierarchical splitting strategy
  - Configurable chunk size (default: 1000 chars)
  - Configurable overlap (default: 200 chars)
  - Separator priority: `\n\n` → `\n` → ` ` → character-level
- **Text Cleaning**:
  - Remove extra whitespace
  - Remove control characters
  - Normalize unicode

#### 3. **Document Ingestion Service** (`app/ingestion.py`)
- **File Support**: PDF and TXT formats
- **PDF Extraction**: Page-aware text extraction with page markers
- **Processing Pipeline**:
  1. File validation (type, size)
  2. Text extraction
  3. Text cleaning
  4. Chunking
  5. Batch embedding generation
  6. Database storage
- **Error Handling**: Graceful error messages for:
  - Empty files
  - Unsupported formats
  - PDF corruption
  - Text extraction failures

#### 4. **Retrieval Service** (`app/retrieval.py`)
- **Semantic Search**:
  - Query embedding generation
  - Cosine similarity search using pgvector `<->` operator
  - Top-K result selection
- **Results Include**:
  - Chunk content
  - Similarity score (0-1)
  - Document metadata
  - Chunk index position
  - Source filename

#### 5. **Database Models** (`app/models.py`)
- **Documents Table**:
  - Metadata storage (title, filename, content type)
  - Chunk count tracking
  - JSONB metadata for extensibility
  - Timestamps for audit

- **Chunks Table**:
  - Vector embeddings (pgvector 1536-dim)
  - Chunk content
  - Document reference
  - Position index
  - JSONB metadata

#### 6. **API Endpoints** (`app/main.py`)

##### POST /api/v1/ingest
**Purpose**: Upload and process documents

**Request**:
```bash
curl -X POST "http://localhost:3000/api/v1/ingest" \
  -F "file=@document.pdf"
```

**Response** (200):
```json
{
  "document_id": 1,
  "filename": "document.pdf",
  "chunk_count": 45,
  "message": "Document ingested successfully"
}
```

**Errors**:
- 400: Unsupported format, empty file
- 500: Processing error

---

##### POST /api/v1/retrieve
**Purpose**: Semantic search across documents

**Request**:
```bash
curl -X POST "http://localhost:3000/api/v1/retrieve" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "top_k": 5
  }'
```

**Response** (200):
```json
{
  "query": "machine learning algorithms",
  "result_count": 3,
  "results": [
    {
      "chunk_id": 42,
      "document_id": 1,
      "document_title": "ML Fundamentals",
      "document_filename": "ml_guide.pdf",
      "content": "Supervised learning uses labeled data...",
      "similarity_score": 0.8742,
      "chunk_index": 5
    }
  ]
}
```

---

## Database Schema

### Tables

#### `documents`
```sql
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  title VARCHAR(255) NOT NULL,
  filename VARCHAR(255) NOT NULL,
  content_type VARCHAR(50),
  file_size INTEGER,
  chunk_count INTEGER DEFAULT 0,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `chunks`
```sql
CREATE TABLE chunks (
  id SERIAL PRIMARY KEY,
  document_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
  content TEXT NOT NULL,
  embedding vector(1536),
  chunk_index INTEGER,
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes

```sql
-- Fast document lookups
CREATE INDEX idx_chunks_document_id ON chunks(document_id);

-- Vector similarity search (IVFFLAT for large datasets)
CREATE INDEX idx_chunks_embedding ON chunks USING ivfflat (embedding vector_cosine_ops);

-- Time-based queries
CREATE INDEX idx_documents_created_at ON documents(created_at);
```

---

## Configuration

### Environment Variables

```env
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=rag_db
DB_USER=postgres
DB_PASSWORD=postgres

# Embedding Settings
OPENAI_API_KEY=sk-...  # Leave blank for mock provider
EMBEDDING_PROVIDER=mock  # "openai" or "mock"

# Chunking Parameters
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# File Handling
MAX_FILE_SIZE_MB=50
ALLOWED_FILE_TYPES=application/pdf,text/plain
```

---

## Testing

### Unit Tests

**Location**: `backend/tests/`

#### test_chunking.py
- ✅ Basic text splitting
- ✅ Empty/whitespace text handling
- ✅ Small text handling (no splitting needed)
- ✅ Overlap preservation
- ✅ Invalid overlap detection
- ✅ Separator hierarchy respect
- ✅ Unicode text support
- ✅ Text cleaning (whitespace, control chars)

#### test_retrieval.py
- ✅ Mock embedding consistency
- ✅ Batch embedding
- ✅ Embedding dimensions
- ✅ Different text variations
- ✅ Similarity score ranges (0-1)
- ✅ Query validation (empty, whitespace)
- ✅ Query length constraints

### Running Tests

```bash
# All tests
poetry run pytest tests/

# Specific test file
poetry run pytest tests/test_chunking.py -v

# With coverage
poetry run pytest tests/ --cov=app
```

---

## Demo Script

**File**: `backend/demo.py`

**Usage**:
```bash
cd backend
python demo.py
```

**Tests**:
1. Health endpoint connectivity
2. Document ingestion with sample text
3. Retrieval with multiple queries
4. Result verification

---

## Implementation Details

### Async/Await Pattern

All I/O operations use async for optimal performance:

```python
async def ingest_file(
    self,
    file: BinaryIO,
    filename: str,
    content_type: str,
    db_session: AsyncSession,
) -> Tuple[int, int]:
    # Extract text asynchronously
    text = await self._extract_text(file, content_type)

    # Generate embeddings asynchronously
    embeddings = await self.embedding_provider.embed_batch(chunk_texts)

    # Store in database asynchronously
    await db_session.commit()
```

### Semantic Search Implementation

```sql
SELECT
    c.id, c.document_id, c.content, c.chunk_index,
    d.title, d.filename,
    1 - (c.embedding <-> query_vector) as similarity
FROM chunks c
JOIN documents d ON c.document_id = d.id
ORDER BY c.embedding <-> query_vector
LIMIT top_k;
```

**Key Points**:
- `<->` operator: Cosine distance between vectors
- `1 - distance`: Converts distance to similarity (0-1 range)
- LIMIT clause: Returns top-K results
- Indexed for fast execution

### Chunking Strategy

The `RecursiveCharacterTextSplitter` balances semantics and size:

1. **Paragraph Level** (`\n\n`): Preserve paragraphs
2. **Line Level** (`\n`): Keep lines together
3. **Word Level** (` `): Preserve words
4. **Character Level**: Last resort for very long words

**Example**:
```
Original: "Long document text....."
↓
Paragraph split: ["Para 1", "Para 2", "Para 3"]
↓
Size check: Para 1 = 500 chars (OK), Para 2 = 1500 chars (too big)
↓
Recursively split: ["Para 2 Line 1", "Para 2 Line 2", ...]
↓
Create chunks with overlap:
  Chunk 1: "Para 1 + Para 2 Line 1" (0-1000)
  Chunk 2: "Para 2 Line 1 + Line 2" (800-1800) <- overlap
```

---

## Performance Characteristics

### Time Complexity

- **Ingestion**: O(n*m) where n=chunk count, m=embedding dim
- **Retrieval**: O(n*log n) with IVFFLAT index

### Space Complexity

- **Per document**: O(chunks * embedding_dim)
- **Storage**: ~6-8KB per chunk with embedding (1536 floats)

### Scalability

- **Single node**: ~10K-100K documents practical limit
- **Scaling strategy**: Partition indices, use async processing
- **Optimization**: IVFFLAT index reduces search from O(n) to O(log n)

---

## Error Handling

### File Upload Errors
```json
{
  "detail": "Unsupported file type: image/png. Supported: PDF, TXT"
}
```

### PDF Extraction Errors
```json
{
  "detail": "Error reading PDF file: Cannot read corrupted PDF"
}
```

### Database Errors
```json
{
  "detail": "Error storing embeddings: Connection timeout"
}
```

### Empty Query
```json
{
  "detail": "Query cannot be empty"
}
```

---

## Production Readiness Checklist

- ✅ Async database operations
- ✅ Proper error handling
- ✅ Input validation
- ✅ Type safety with Pydantic
- ✅ Unit tests
- ✅ Database migrations (init-db.sql)
- ✅ Configuration management
- ✅ Logging ready (FastAPI built-in)
- ✅ API documentation (Swagger UI)
- ✅ Docker support

## Missing Pieces (For Next Phase)

- ❌ LLM answer generation (from retrieved chunks)
- ❌ Fact checking logic
- ❌ Reranking of results
- ❌ Query expansion
- ❌ Caching layer
- ❌ Metrics and monitoring
- ❌ Authentication/authorization
- ❌ Rate limiting
- ❌ Batch processing for large documents

---

## How to Use

### 1. Start Services
```bash
docker-compose up -d
```

### 2. Verify Health
```bash
curl http://localhost:3000/health
```

### 3. Upload Document
```bash
curl -X POST "http://localhost:3000/api/v1/ingest" \
  -F "file=@sample_document.txt"
```

### 4. Search Documents
```bash
curl -X POST "http://localhost:3000/api/v1/retrieve" \
  -H "Content-Type: application/json" \
  -d '{"query":"machine learning", "top_k":5}'
```

### 5. View in Browser
- **Swagger UI**: http://localhost:3000/docs
- **ReDoc**: http://localhost:3000/redoc
- **Frontend**: http://localhost:5173

---

## Code Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app, endpoints
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # Database setup
│   ├── config.py            # Environment config
│   ├── schemas.py           # Pydantic request/response
│   ├── embeddings.py        # Embedding providers
│   ├── chunking.py          # Text splitting logic
│   ├── ingestion.py         # Document ingestion
│   └── retrieval.py         # Semantic search
├── tests/
│   ├── __init__.py
│   ├── test_chunking.py     # Chunking tests
│   └── test_retrieval.py    # Retrieval tests
├── Dockerfile
├── requirements.txt
├── pyproject.toml
├── demo.py                  # Testing script
└── README.md
```

---

## Next Steps

1. **Integrate LLM for Answer Generation**
   - Use OpenAI/Anthropic API
   - Generate answers from retrieved chunks

2. **Implement Fact Checking**
   - Compare retrieved facts against source
   - Identify contradictions
   - Generate confidence scores

3. **Add Reranking**
   - Fine-tune results with cross-encoder
   - Improve relevance

4. **Production Deployment**
   - Set up monitoring
   - Add authentication
   - Configure logging
   - Load testing

---

## References

- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Async](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
