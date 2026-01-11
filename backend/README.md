# RAG Fact-Check Backend

FastAPI backend for the RAG Fact-Check application with document ingestion and semantic search.

## 🏗️ Architecture

### Services

1. **Document Ingestion Service** (`app/ingestion.py`)
   - Accepts PDF and TXT files
   - Extracts text from PDFs using pypdf
   - Splits text into chunks using RecursiveCharacterTextSplitter
   - Generates embeddings for each chunk using the embedding provider
   - Stores documents and chunks in PostgreSQL with pgvector

2. **Embedding Provider** (`app/embeddings.py`)
   - Abstract `EmbeddingProvider` interface
   - OpenAI implementation (text-embedding-3-small, 1536 dimensions)
   - Mock implementation for testing (deterministic, no API calls)
   - Batch processing with rate limiting

3. **Document Retrieval Service** (`app/retrieval.py`)
   - Semantic search using cosine similarity
   - pgvector `<->` operator for efficient vector search
   - Returns top-k results with similarity scores
   - Includes document metadata and chunk information

4. **Text Chunking** (`app/chunking.py`)
   - `RecursiveCharacterTextSplitter` for intelligent text splitting
   - Configurable chunk size and overlap
   - Recursive separation strategy (paragraph → line → word → character)
   - Text cleaning (remove extra whitespace, control characters)

## 📋 API Endpoints

### Health Check
```
GET /health
```
Returns database connectivity status.

**Response:**
```json
{
  "status": "ok",
  "db": "connected"
}
```

### Document Ingestion
```
POST /api/v1/ingest
Content-Type: multipart/form-data

file: <binary file>
```

Upload a PDF or TXT file for processing.

**Response:**
```json
{
  "document_id": 1,
  "filename": "sample.pdf",
  "chunk_count": 45,
  "message": "Document ingested successfully"
}
```

**Errors:**
- `400`: Unsupported file type, empty file, or extraction error
- `500`: Internal server error

### Document Retrieval
```
POST /api/v1/retrieve
Content-Type: application/json

{
  "query": "What is machine learning?",
  "top_k": 5
}
```

Retrieve relevant document chunks using semantic search.

**Response:**
```json
{
  "query": "What is machine learning?",
  "result_count": 3,
  "results": [
    {
      "chunk_id": 1,
      "document_id": 1,
      "document_title": "sample",
      "document_filename": "sample.pdf",
      "content": "Machine learning is a subset of artificial intelligence...",
      "similarity_score": 0.87,
      "chunk_index": 5
    }
  ]
}
```

## 🗄️ Database Schema

### Documents Table
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

### Chunks Table
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

**Indexes:**
- `idx_chunks_document_id`: Fast lookups by document
- `idx_chunks_embedding`: IVFFLAT index for vector similarity search
- `idx_documents_created_at`: Fast sorting by creation time

## ⚙️ Configuration

Environment variables (see `.env.example`):

```env
# Database
DB_HOST=postgres
DB_PORT=5432
DB_NAME=rag_db
DB_USER=postgres
DB_PASSWORD=postgres

# Embeddings
OPENAI_API_KEY=sk-...  # Leave empty for mock provider
EMBEDDING_PROVIDER=mock  # or "openai"

# RAG Settings
CHUNK_SIZE=1000        # Characters per chunk
CHUNK_OVERLAP=200      # Overlap between chunks
MAX_FILE_SIZE_MB=50
ALLOWED_FILE_TYPES=application/pdf,text/plain
```

## 🚀 Development

### Setup

```bash
cd backend
poetry install
cp .env.example .env
```

### Run Tests

```bash
poetry run pytest tests/
```

**Test Files:**
- `test_chunking.py`: RecursiveCharacterTextSplitter tests
- `test_retrieval.py`: Embedding provider and query construction tests

### Run Server

```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Swagger UI**: http://localhost:8000/docs
**ReDoc**: http://localhost:8000/redoc

### Docker

```bash
docker build -t rag-backend .
docker run -p 8000:8000 --env-file .env rag-backend
```

## 📊 Workflow Example

### 1. Upload Document
```bash
curl -X POST "http://localhost:3000/api/v1/ingest" \
  -F "file=@sample.pdf"
```

Response:
```json
{
  "document_id": 1,
  "filename": "sample.pdf",
  "chunk_count": 45
}
```

### 2. Query Documents
```bash
curl -X POST "http://localhost:3000/api/v1/retrieve" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "machine learning algorithms",
    "top_k": 5
  }'
```

Response:
```json
{
  "query": "machine learning algorithms",
  "result_count": 3,
  "results": [...]
}
```

## 🔍 How Semantic Search Works

1. **Query Embedding**: User's query is embedded using the embedding provider
2. **Vector Search**: Find chunks with similar embeddings using cosine similarity
3. **Ranking**: Results ranked by similarity score (0-1, higher = more similar)
4. **Return**: Top-k results with metadata

**Cosine Similarity Formula:**
```
similarity = 1 - cosine_distance
```

Where pgvector's `<->` operator computes the cosine distance.

## 🧠 Text Chunking Strategy

The `RecursiveCharacterTextSplitter` uses a hierarchical approach:

1. **Try paragraph break** (`\n\n`)
2. **Try line break** (`\n`)
3. **Try space** (` `)
4. **Split character by character** (fallback)

This ensures:
- Semantic chunks when possible
- Chunks don't exceed size limit
- Overlap preserved for context

Example:
```
Chunk 1: [0-1000 chars]
Overlap: [900-1000 chars]
Chunk 2: [900-1900 chars]
```

## 🛡️ Error Handling

### Empty Files
```json
{
  "detail": "File is empty or contains no readable text"
}
```

### Unsupported Formats
```json
{
  "detail": "Unsupported file type: image/jpeg. Supported: PDF, TXT"
}
```

### PDF Extraction Errors
```json
{
  "detail": "Error reading PDF file: [specific error]"
}
```

## 🚦 Limitations

1. **File Size**: Max 50MB (configurable)
2. **Embeddings**: OpenAI has rate limits; mock provider for testing
3. **Vector Dimension**: Fixed at 1536 (OpenAI standard)
4. **File Types**: Only PDF and TXT supported
5. **Query Length**: Max 1000 characters

## 🔄 Future Enhancements

- [ ] Multiple embedding providers (Cohere, Hugging Face)
- [ ] Document update/deletion with cascade
- [ ] Batch ingestion API
- [ ] Token counting with tiktoken
- [ ] Custom chunking strategies
- [ ] Metadata filtering in retrieval
- [ ] Async batch processing with Celery
- [ ] Search result caching

## 📚 Dependencies

- **FastAPI**: Web framework
- **SQLAlchemy**: ORM with async support
- **asyncpg**: PostgreSQL driver for async
- **pgvector**: Vector similarity search
- **pypdf**: PDF text extraction
- **openai**: Embedding generation
- **pydantic**: Data validation

## 📝 Notes

- All I/O operations are async for better performance
- Mock embedding provider for testing without API costs
- Database tables created automatically on startup
- Vector index uses IVFFLAT for efficient similarity search
