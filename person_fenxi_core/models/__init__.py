"""Data models for Psyche KB."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class DocumentType(Enum):
    """Document type enumeration."""

    CORPUS = "corpus"  # Original corpus material
    SKILL = "skill"  # Skill definition
    ANALYSIS = "analysis"  # Analysis result


@dataclass
class Chunk:
    """Text chunk from document."""

    id: str
    content: str
    source_doc_id: str
    chunk_index: int
    metadata: dict = field(default_factory=dict)


@dataclass
class Document:
    """Document entity."""

    id: str
    title: str
    content: str
    doc_type: DocumentType
    file_path: Optional[Path] = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)


@dataclass
class Skill:
    """Skill definition (from SKILL.md)."""

    id: str
    name: str
    description: str
    criteria: dict  # Skill-specific evaluation criteria
    version: int = 1


@dataclass
class AnalysisResult:
    """Analysis result from Analyzer."""

    target_id: str  # Person being analyzed
    skill_id: str
    conclusion: str
    evidence: list[str] = field(default_factory=list)
    confidence: float = 0.0  # 0.0 - 1.0
    created_at: datetime = field(default_factory=datetime.now)