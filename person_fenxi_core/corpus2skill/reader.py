"""Document reader for Corpus2Skill pipeline."""
from __future__ import annotations

import codecs
from pathlib import Path
from typing import List, Optional

from person_fenxi_core.models import Chunk, Document, DocumentType


class DocumentReader:
    """Read documents from various formats."""

    SUPPORTED_EXTENSIONS = {".txt", ".md", ".docx"}

    def read(self, file_path: Path) -> Document:
        """Read a document and return Document object."""
        if not file_path.exists():
            msg = f"File not found: {file_path}"
            raise FileNotFoundError(msg)

        ext = file_path.suffix.lower()
        if ext not in self.SUPPORTED_EXTENSIONS:
            msg = f"Unsupported file type: {ext}"
            raise ValueError(msg)

        content = self._read_content(file_path)

        return Document(
            id=file_path.stem,
            title=file_path.stem,
            content=content,
            doc_type=DocumentType.CORPUS,
            file_path=file_path,
        )

    def _read_content(self, file_path: Path) -> str:
        """Read file content with encoding detection."""
        # Try UTF-8 first
        encodings = ["utf-8", "gbk", "gb2312", "latin-1"]

        for encoding in encodings:
            try:
                content = file_path.read_text(encoding=encoding)
                return content
            except UnicodeDecodeError:
                continue

        # Fallback: read as binary and decode
        raw = file_path.read_bytes()
        return raw.decode("utf-8", errors="ignore")

    def can_read(self, file_path: Path) -> bool:
        """Check if file can be read."""
        return file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS


def read_directory(dir_path: Path) -> List[Document]:
    """Read all supported documents in a directory."""
    reader = DocumentReader()
    documents = []

    for ext in reader.SUPPORTED_EXTENSIONS:
        for file_path in dir_path.glob(f"*{ext}"):
            if file_path.is_file():
                try:
                    doc = reader.read(file_path)
                    documents.append(doc)
                except Exception:
                    # Skip unreadable files
                    continue

    return documents