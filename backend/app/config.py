"""Application configuration from environment variables"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Database configuration
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "rag_db"
    db_user: str = "postgres"
    db_password: str = "postgres"

    # Application configuration
    debug: bool = False
    api_title: str = "RAG Fact-Check API"

    # Embedding configuration
    openai_api_key: str = ""
    embedding_provider: str = "openai"  # or "mock" for testing

    # RAG configuration
    chunk_size: int = 1000
    chunk_overlap: int = 200
    max_file_size_mb: int = 50
    allowed_file_types: list = ["application/pdf", "text/plain"]

    # Chat configuration
    chat_model: str = "gpt-4-turbo-preview"
    chat_temperature: float = 0.3
    verification_model: str = "gpt-4-turbo-preview"
    verification_temperature: float = 0.2

    # Tracing configuration
    enable_tracing: bool = True
    jaeger_host: str = "localhost"
    jaeger_port: int = 6831

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


settings = Settings()
