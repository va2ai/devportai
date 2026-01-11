"""Text chunking logic for RAG"""
from typing import List
import re


class RecursiveCharacterTextSplitter:
    """Split text into chunks with specified size and overlap"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: List[str] = None,
    ):
        """
        Initialize the text splitter

        Args:
            chunk_size: Maximum characters per chunk
            chunk_overlap: Number of characters to overlap between chunks
            separators: List of separators to split on (in order of preference)
        """
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be less than chunk_size")

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", " ", ""]

    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks

        Args:
            text: The text to split

        Returns:
            List of text chunks
        """
        if not text or not text.strip():
            return []

        return self._split_text_recursive(text, self.separators)

    def _split_text_recursive(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text using separators"""
        chunks = []
        separator = separators[-1]

        # Try each separator in order
        for sep in separators:
            if sep in text:
                separator = sep
                break

        # Split by separator
        if separator:
            splits = text.split(separator)
        else:
            splits = list(text)

        # Merge splits into chunks
        good_splits = []
        for split in splits:
            if len(split) < self.chunk_size:
                good_splits.append(split)
            else:
                # Recursively split large chunks
                if good_splits:
                    merged = self._merge_splits(good_splits, separator)
                    chunks.extend(merged)
                    good_splits = []

                # Recursively split the large split
                other_info = self._split_text_recursive(split, separators[separators.index(separator) + 1 :])
                chunks.extend(other_info)

        # Merge remaining splits
        if good_splits:
            merged = self._merge_splits(good_splits, separator)
            chunks.extend(merged)

        return chunks

    def _merge_splits(self, splits: List[str], separator: str) -> List[str]:
        """Merge splits while respecting chunk_size and chunk_overlap"""
        separator_len = len(separator)
        chunks = []
        current_chunk = []
        current_length = 0

        for split in splits:
            split_len = len(split)

            if current_length + split_len + separator_len <= self.chunk_size:
                # Add to current chunk
                current_chunk.append(split)
                current_length += split_len + separator_len
            else:
                # Current chunk is full, save it and start a new one
                if current_chunk:
                    merged = separator.join(current_chunk)
                    chunks.append(merged)

                    # Add overlap to next chunk
                    # Find overlap by taking the last chunk_overlap characters
                    overlap = ""
                    for chunk in reversed(current_chunk):
                        overlap = chunk + separator + overlap
                        if len(overlap) >= self.chunk_overlap:
                            break

                    # Trim overlap to exact size
                    if len(overlap) > self.chunk_overlap:
                        overlap = overlap[-self.chunk_overlap :]

                    current_chunk = [overlap] if overlap else []
                    current_length = len(overlap) + separator_len if overlap else 0

                # Add the current split
                if split_len <= self.chunk_size:
                    current_chunk.append(split)
                    current_length += split_len + separator_len
                else:
                    # Split is larger than chunk_size, add as is
                    if current_chunk:
                        merged = separator.join(current_chunk)
                        chunks.append(merged)
                        current_chunk = []
                        current_length = 0
                    chunks.append(split)

        # Add final chunk
        if current_chunk:
            merged = separator.join(current_chunk)
            chunks.append(merged)

        return chunks


def clean_text(text: str) -> str:
    """
    Clean text by removing extra whitespace and normalizing

    Args:
        text: Raw text to clean

    Returns:
        Cleaned text
    """
    # Remove extra whitespace
    text = re.sub(r"\s+", " ", text)
    # Remove control characters
    text = "".join(char for char in text if ord(char) >= 32 or char in "\n\t\r")
    return text.strip()
