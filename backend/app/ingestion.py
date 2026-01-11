"""Document ingestion service for RAG"""
from typing import BinaryIO, Tuple, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from unstructured.partition.auto import partition
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
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
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
    ) -> Tuple[int, int, Dict[str, Any]]:
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
        text = await self._extract_text(file, filename, content_type)

        if not text or not text.strip():
            raise ValueError("File is empty or contains no readable text")

        summary = self._summarize_text(text)

        # Clean text
        text = clean_text(text)
        summary["llm_summary"] = await self._generate_llm_summary(text)

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
                doc_metadata={"original_file": filename},
            )
            chunk_records.append(chunk_record)

        # Bulk insert chunks
        db_session.add_all(chunk_records)
        await db_session.commit()

        return document_id, len(chunks), summary

    async def _extract_text(self, file: BinaryIO, filename: str, content_type: str) -> str:
        """
        Extract text from file using Unstructured

        Args:
            file: File object
            content_type: MIME type

        Returns:
            Extracted text

        Raises:
            ValueError: If format is unsupported or parsing fails
        """
        try:
            file.seek(0)
            elements = partition(
                file=file,
                content_type=content_type,
                include_page_breaks=True,
            )
            return self._elements_to_text(elements)
        except Exception as e:
            raise ValueError(f"Error parsing file with Unstructured: {str(e)}")

    def _elements_to_text(self, elements) -> str:
        """Convert Unstructured elements to a single text blob"""
        text_parts = []
        for element in elements or []:
            text = getattr(element, "text", None)
            if text:
                text_parts.append(text)
        return "\n".join(text_parts)

    def _summarize_text(self, text: str) -> Dict[str, Any]:
        """Compute basic text statistics before cleaning"""
        char_count = len(text)
        word_count = len(text.split()) if text else 0
        line_count = text.count("\n") + 1 if text else 0
        page_breaks = text.count("\f")
        page_count = page_breaks + 1 if page_breaks > 0 else None
        return {
            "char_count": char_count,
            "word_count": word_count,
            "line_count": line_count,
            "page_count": page_count,
        }

    async def _generate_llm_summary(self, text: str) -> str | None:
        """Generate a 1-paragraph summary using the chat model"""
        if not settings.openai_api_key:
            return None
        if not text:
            return None
        truncated = text[:8000]
        prompt = (
            "Summarize the following document in one concise paragraph. "
            "Focus on key facts and purpose. Do not add information not present.\n\n"
            f"{truncated}"
        )
        try:
            response = await self.client.chat.completions.create(
                model=settings.chat_model,
                temperature=0.2,
                messages=[
                    {"role": "system", "content": "You are a precise summarization assistant."},
                    {"role": "user", "content": prompt},
                ],
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return None
