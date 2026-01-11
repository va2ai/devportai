# RAG Fact-Check Application

A production-ready monorepo for a Retrieval-Augmented Generation (RAG) fact-checking application built with FastAPI, React, PostgreSQL, and pgvector.

## 🏗️ Architecture

```
devport/
├── backend/                 # FastAPI backend service
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py         # Main FastAPI application
│   │   ├── config.py       # Configuration management
│   │   └── database.py     # Database setup
│   ├── Dockerfile
│   ├── pyproject.toml      # Poetry dependencies
│   └── README.md
├── frontend/               # React frontend application
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── index.css
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── package.json
│   ├── Dockerfile
│   └── README.md
├── docker-compose.yml      # Orchestration configuration
├── init-db.sql            # Database initialization script
├── .env.example           # Environment variables template
├── .gitignore
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (recommended for development)
- Python 3.11+ (for local development)
- Node.js 18+ (for local frontend development)

### Docker Setup (Recommended)

1. **Clone the repository and navigate to the root:**
```bash
cd devport
```

2. **Create environment file:**
```bash
cp .env.example .env
```

3. **Build and start services:**
```bash
docker-compose up --build
```

This will start:
- **Backend API**: http://localhost:8000 (or configured BACKEND_PORT in .env)
- **Frontend**: http://localhost:5173
- **PostgreSQL**: localhost:5432

**Note**: If port 8000 is already in use on your system, modify the `BACKEND_PORT` in your `.env` file to an available port (e.g., 3000, 3001, 8080).

4. **Verify Health:**
```bash
# Use the same port you configured in BACKEND_PORT (default 8000)
curl http://localhost:8000/health
# Or if using a different port (e.g., 3000):
curl http://localhost:3000/health
# Expected response: {"status": "ok", "db": "connected"}
```

### Local Development Setup

#### Backend

1. **Install Python dependencies:**
```bash
cd backend
poetry install
```

2. **Start PostgreSQL (Docker only):**
```bash
docker run --name rag_postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=rag_db \
  -p 5432:5432 \
  pgvector/pgvector:pg15-latest
```

3. **Run development server:**
```bash
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

1. **Install Node dependencies:**
```bash
cd frontend
npm install
```

2. **Start development server:**
```bash
npm run dev
```

The frontend will be available at http://localhost:5173

## 📋 API Documentation

Once the backend is running:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:3000/redoc

### Health Check Endpoint

```bash
GET /health
```

**Response:**
```json
{
  "status": "ok",
  "db": "connected"
}
```

## 🗄️ Database

The application uses **PostgreSQL 15** with the **pgvector** extension for vector similarity search.

### Database Initialization

The `init-db.sql` script automatically:
- Enables the `vector` extension
- Creates placeholder tables for documents and embeddings
- Sets up proper indexes for vector search

### Connecting to Database

```bash
# From your host machine
psql -h localhost -U postgres -d rag_db

# Or use Docker
docker exec -it rag_postgres psql -U postgres -d rag_db
```

## 🔧 Configuration

All configuration is managed through environment variables. See `.env.example` for available options:

- `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` - Database config
- `DEBUG` - Enable debug mode
- `BACKEND_PORT`, `FRONTEND_PORT` - Service ports
- `VECTOR_DIMENSION` - Vector embedding dimension (default: 1536)

## 📦 Dependencies

### Backend
- **FastAPI** ^0.104.1 - Modern Python web framework
- **SQLAlchemy** ^2.0.23 - SQL toolkit and ORM
- **psycopg2-binary** ^2.9.9 - PostgreSQL adapter
- **python-dotenv** ^1.0.0 - Environment variable management

### Frontend
- **React** ^18.2.0 - UI library
- **Vite** ^5.0.7 - Build tool
- **Tailwind CSS** ^3.3.6 - CSS framework
- **Axios** ^1.6.2 - HTTP client

## 🧪 Testing

### Backend Tests
```bash
cd backend
poetry run pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

## 📝 Project Status

This is the **foundation phase** of the RAG Fact-Check application:

✅ **Completed:**
- Monorepo structure
- FastAPI backend with health check
- React frontend with Tailwind CSS
- Docker & Docker Compose setup
- PostgreSQL with pgvector extension
- Environment configuration

🔄 **Next Phase:**
- RAG pipeline implementation
- Vector embeddings generation
- Document ingestion system
- Fact-checking logic
- Authentication and authorization
- Comprehensive testing suite

## 🛠️ Development Workflow

1. **Make changes** to `/backend` or `/frontend`
2. **With Docker Compose**: Services auto-reload on file changes
3. **Without Docker**: Run services locally with `npm run dev` and `poetry run uvicorn ...`
4. **Test changes** by visiting http://localhost:5173 and http://localhost:8000/docs

## 📚 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [pgvector Documentation](https://github.com/pgvector/pgvector)
- [React Documentation](https://react.dev/)
- [Tailwind CSS Documentation](https://tailwindcss.com/)

## 🤝 Contributing

(Contributing guidelines to be added)

## 📄 License

(License information to be added)

---

**Last Updated**: January 2025
