"""Application configuration from environment variables"""
from pydantic import field_validator
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
    allowed_file_types: list[str] = ["application/pdf", "text/plain"]
    allowed_file_extensions: list[str] = [
        ".bmp",
        ".csv",
        ".doc",
        ".docx",
        ".eml",
        ".epub",
        ".heic",
        ".html",
        ".jpeg",
        ".jpg",
        ".md",
        ".msg",
        ".odt",
        ".org",
        ".p7s",
        ".pdf",
        ".png",
        ".ppt",
        ".pptx",
        ".rst",
        ".rtf",
        ".tiff",
        ".tsv",
        ".txt",
        ".xls",
        ".xlsx",
        ".xml",
    ]

    @field_validator("allowed_file_types", "allowed_file_extensions", mode="before")
    @classmethod
    def _split_csv_list(cls, value):
        if isinstance(value, str):
            parts = [item.strip() for item in value.split(",")]
            return [item for item in parts if item]
        return value

    # Chat configuration
    chat_model: str = "gpt-5.1"
    chat_temperature: float = 0.3
    verification_model: str = "gpt-5.1"
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


