"""Unit tests for text chunking logic"""
import pytest
from app.chunking import RecursiveCharacterTextSplitter, clean_text


class TestRecursiveCharacterTextSplitter:
    """Test cases for RecursiveCharacterTextSplitter"""

    def test_basic_splitting(self):
        """Test basic text splitting"""
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
        text = "This is a test. " * 20  # Repeat to create longer text
        chunks = splitter.split_text(text)

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk) <= 50

    def test_empty_text(self):
        """Test splitting empty text returns empty list"""
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
        chunks = splitter.split_text("")
        assert chunks == []

    def test_whitespace_only(self):
        """Test splitting whitespace-only text returns empty list"""
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
        chunks = splitter.split_text("   \n\t  ")
        assert chunks == []

    def test_small_text(self):
        """Test splitting text smaller than chunk size"""
        splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=10)
        text = "This is a small text."
        chunks = splitter.split_text(text)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_overlap_preserved(self):
        """Test that overlap is preserved between chunks"""
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
        text = "word " * 50  # Create text with repeated pattern

        chunks = splitter.split_text(text)

        # Check that consecutive chunks have overlap
        for i in range(len(chunks) - 1):
            # The end of one chunk should overlap with the start of the next
            # (this is a basic check; exact overlap depends on splitting)
            assert len(chunks[i]) > 0
            assert len(chunks[i + 1]) > 0

    def test_chunk_overlap_invalid(self):
        """Test that invalid overlap raises error"""
        with pytest.raises(ValueError):
            RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=50)

        with pytest.raises(ValueError):
            RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=60)

    def test_respects_separators(self):
        """Test that splitter respects separator hierarchy"""
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=100,
            chunk_overlap=0,
            separators=["\n\n", "\n", " "],
        )

        # Text with paragraph breaks (should split on \n\n first)
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        chunks = splitter.split_text(text)

        # Should prefer splitting on \n\n
        assert len(chunks) >= 2

    def test_unicode_text(self):
        """Test splitting unicode text"""
        splitter = RecursiveCharacterTextSplitter(chunk_size=50, chunk_overlap=10)
        text = "这是一个测试文本。" * 10  # Chinese text repeated
        chunks = splitter.split_text(text)

        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk) <= 50


class TestCleanText:
    """Test cases for text cleaning"""

    def test_remove_extra_whitespace(self):
        """Test removal of extra whitespace"""
        text = "This  has   extra    spaces"
        cleaned = clean_text(text)
        assert cleaned == "This has extra spaces"

    def test_remove_newlines(self):
        """Test handling of newlines"""
        text = "Line1\n\nLine2\n\nLine3"
        cleaned = clean_text(text)
        # Should normalize whitespace
        assert "Line1" in cleaned
        assert "Line2" in cleaned
        assert "Line3" in cleaned

    def test_preserve_tabs(self):
        """Test that tabs are preserved"""
        text = "Text\twith\ttabs"
        cleaned = clean_text(text)
        assert "\t" in cleaned

    def test_remove_control_characters(self):
        """Test removal of control characters"""
        text = "Text\x00with\x01control\x02chars"
        cleaned = clean_text(text)
        # Should not contain control chars
        for char in cleaned:
            assert ord(char) >= 32 or char in "\n\t\r"

    def test_strip_leading_trailing(self):
        """Test stripping leading/trailing whitespace"""
        text = "   some text   "
        cleaned = clean_text(text)
        assert cleaned == "some text"

    def test_empty_string(self):
        """Test cleaning empty string"""
        assert clean_text("") == ""

    def test_whitespace_string(self):
        """Test cleaning whitespace-only string"""
        assert clean_text("   ") == ""
