"""Text chunker for Corpus2Skill pipeline."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from src.models import Chunk


@dataclass
class ChunkConfig:
    """Configuration for chunking."""

    max_chunk_size: int = 800  # Max characters per chunk
    min_chunk_size: int = 200  # Minimum chunk size
    overlap: int = 50  # Overlap between chunks


class TextChunker:
    """Split documents into meaningful chunks."""

    def __init__(self, config: Optional[ChunkConfig] = None) -> None:
        self.config = config or ChunkConfig()

    def chunk_document(
        self,
        doc_id: str,
        content: str,
        title: str = "",
    ) -> List[Chunk]:
        """Split document into chunks by sections."""
        # First try to split by markdown headings
        sections = self._split_by_headings(content)

        if not sections:
            # Fallback: split by paragraphs
            sections = self._split_by_paragraphs(content)

        chunks = []
        current_idx = 0

        for section_title, section_text in sections:
            # Further split large sections
            sub_chunks = self._split_text(section_text)

            for sub_text in sub_chunks:
                if len(sub_text.strip()) < self.config.min_chunk_size:
                    continue

                chunk_id = f"{doc_id}_{current_idx:04d}"
                chunk = Chunk(
                    id=chunk_id,
                    content=sub_text.strip(),
                    source_doc_id=doc_id,
                    chunk_index=current_idx,
                    metadata={
                        "section_title": section_title,
                        "title": title,
                    },
                )
                chunks.append(chunk)
                current_idx += 1

        return chunks

    def _split_by_headings(
        self,
        content: str,
    ) -> List[Tuple[str, str]]:
        """Split by markdown headings (# ## ###)."""
        heading_pattern = r"^(#{1,3})\s+(.+)$"
        lines = content.split("\n")
        sections = []
        current_title = "全文"
        current_content = []

        for line in lines:
            if re.match(heading_pattern, line, re.MULTILINE):
                # Save previous section
                if current_content:
                    text = "\n".join(current_content)
                    sections.append((current_title, text))

                # Start new section
                match = re.match(heading_pattern, line, re.MULTILINE)
                level = len(match.group(1))  # 1-3
                current_title = match.group(2).strip()
                current_content = []
            else:
                current_content.append(line)

        # Last section
        if current_content:
            sections.append((current_title, "\n".join(current_content)))

        return sections

    def _split_by_paragraphs(self, content: str) -> List[Tuple[str, str]]:
        """Split by double newlines (paragraphs)."""
        paragraphs = re.split(r"\n\n+", content)
        sections = []

        for i, para in enumerate(paragraphs):
            para = para.strip()
            if para:
                sections.append((f"段落{i+1}", para))

        return sections

    def _split_text(self, text: str) -> List[str]:
        """Split large text into smaller chunks."""
        if len(text) <= self.config.max_chunk_size:
            return [text]

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + self.config.max_chunk_size, text_len)

            # Try to break at Chinese sentence boundary
            if end < text_len:
                for sep in "。！？":
                    boundary = text.rfind(sep, start, end)
                    if boundary > start:
                        end = boundary + 1
                        break

            chunk = text[start:end]
            chunks.append(chunk)
            start = max(end - self.config.overlap, start + 1)

        return chunks