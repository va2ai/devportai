"""Document ingestion service for RAG"""
import io
from typing import BinaryIO, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import insert
from pypdf import PdfReader
from app.models import Document, Chunk
from app.chunking import RecursiveCharacterTextSplitter, clean_text
from app.embeddings import EmbeddingProvider
from app.config import settings


class DocumentIngestionService:
    """Service for ingesting documents and storing embeddings"""

    def __init__(self, embedding_provider: EmbeddingProvider):
        """
        Initialize ingestion service

        Args:
            embedding_provider: Provider for generating embeddings
        """
        self.embedding_provider = embedding_provider
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
        )

    async def ingest_file(
        self,
        file: BinaryIO,
        filename: str,
        content_type: str,
        db_session: AsyncSession,
    ) -> Tuple[int, int]:
        """
        Ingest a file (PDF or TXT) and store embeddings

        Args:
            file: File object to ingest
            filename: Original filename
            content_type: MIME type of the file
            db_session: Database session

        Returns:
            Tuple of (document_id, chunk_count)

        Raises:
            ValueError: If file format is unsupported or file is empty
        """
        # Extract text from file
        text = await self._extract_text(file, content_type)

        if not text or not text.strip():
            raise ValueError("File is empty or contains no readable text")

        # Clean text
        text = clean_text(text)

        # Split into chunks
        chunks = self.splitter.split_text(text)

        if not chunks:
            raise ValueError("No text chunks could be extracted from file")

        # Create document record
        doc = Document(
            title=filename.rsplit(".", 1)[0],  # Remove extension
            filename=filename,
            content_type=content_type,
            chunk_count=len(chunks),
        )
        db_session.add(doc)
        await db_session.flush()  # Get the document ID
        document_id = doc.id

        # Generate embeddings for chunks in batch
        chunk_texts = [chunk for chunk in chunks]
        embeddings = await self.embedding_provider.embed_batch(chunk_texts)

        # Create chunk records
        chunk_records = []
        for idx, (chunk_text, embedding) in enumerate(zip(chunk_texts, embeddings)):
            chunk_record = Chunk(
                document_id=document_id,
                content=chunk_text,
                embedding=embedding,
                chunk_index=idx,
                metadata={"original_file": filename},
            )
            chunk_records.append(chunk_record)

        # Bulk insert chunks
        db_session.add_all(chunk_records)
        await db_session.commit()

        return document_id, len(chunks)

    async def _extract_text(self, file: BinaryIO, content_type: str) -> str:
        """
        Extract text from file based on content type

        Args:
            file: File object
            content_type: MIME type

        Returns:
            Extracted text

        Raises:
            ValueError: If format is unsupported
        """
        if content_type == "application/pdf":
            return await self._extract_from_pdf(file)
        elif content_type == "text/plain":
            return await self._extract_from_text(file)
        else:
            raise ValueError(f"Unsupported file format: {content_type}")

    async def _extract_from_pdf(self, file: BinaryIO) -> str:
        """Extract text from PDF file"""
        try:
            # Read PDF file
            pdf_reader = PdfReader(file)

            # Extract text from all pages
            text_parts = []
            for page_num, page in enumerate(pdf_reader.pages):
                text = page.extract_text()
                if text:
                    text_parts.append(f"[Page {page_num + 1}]\n{text}")

            return "\n".join(text_parts)
        except Exception as e:
            raise ValueError(f"Error reading PDF file: {str(e)}")

    async def _extract_from_text(self, file: BinaryIO) -> str:
        """Extract text from plain text file"""
        try:
            content = file.read()
            if isinstance(content, bytes):
                return content.decode("utf-8")
            return content
        except Exception as e:
            raise ValueError(f"Error reading text file: {str(e)}")
